// ProjectBlur-owned frame transport and conversion.
// Media Foundation integration structure is based on Microsoft's
// MIT-licensed Windows Camera Virtual Camera sample.
#include "pch.h"

#include <cstring>

namespace {
constexpr UINT32 kMaximumWidth = 1920;
constexpr UINT32 kMaximumHeight = 1080;
constexpr std::uint64_t kMaximumFrameAgeNanoseconds = 500'000'000ULL;

BYTE ClampByte(int value) noexcept {
    return static_cast<BYTE>(std::clamp(value, 0, 255));
}
}  // namespace

HRESULT SimpleFrameGenerator::Initialize(
    IMFMediaType* media_type,
    std::wstring_view mapping_name,
    std::wstring_view user_sid) {
    RETURN_HR_IF_NULL(E_INVALIDARG, media_type);
    RETURN_IF_FAILED(media_type->GetGUID(MF_MT_SUBTYPE, &subtype_));
    RETURN_HR_IF(
        MF_E_UNSUPPORTED_FORMAT,
        subtype_ != MFVideoFormat_RGB32 && subtype_ != MFVideoFormat_NV12);
    RETURN_IF_FAILED(
        MFGetAttributeSize(media_type, MF_MT_FRAME_SIZE, &width_, &height_));
    RETURN_HR_IF(
        MF_E_INVALIDMEDIATYPE,
        width_ == 0 || height_ == 0 || width_ > kMaximumWidth ||
            height_ > kMaximumHeight ||
            (subtype_ == MFVideoFormat_NV12 &&
             ((width_ & 1U) != 0 || (height_ & 1U) != 0)));

    LARGE_INTEGER frequency{};
    RETURN_HR_IF(
        HRESULT_FROM_WIN32(ERROR_NOT_SUPPORTED),
        !QueryPerformanceFrequency(&frequency) || frequency.QuadPart <= 0);
    performance_frequency_ = static_cast<std::uint64_t>(frequency.QuadPart);
    if (!reader_.OpenOrCreate(
            mapping_name,
            user_sid,
            kMaximumWidth,
            kMaximumHeight)) {
        return HRESULT_FROM_WIN32(GetLastError());
    }
    return S_OK;
}

HRESULT SimpleFrameGenerator::CreateFrame(
    BYTE* output,
    DWORD output_length,
    LONG output_pitch,
    ULONG,
    ProjectBlurFrameMetadata* metadata) {
    RETURN_HR_IF_NULL(E_POINTER, metadata);
    *metadata = {};
    const auto frame = reader_.ReadLatest();
    if (!frame) {
        return WriteBlackFrame(output, output_length, output_pitch);
    }

    metadata->sequence = frame->header.sequence;
    metadata->source_timestamp_ns = frame->header.timestamp_ns;
    const std::uint64_t now_ns = MonotonicNanoseconds();
    const bool timestamp_valid =
        frame->header.timestamp_ns > 0 && now_ns >= frame->header.timestamp_ns;
    const bool stale =
        !timestamp_valid ||
        now_ns - frame->header.timestamp_ns > kMaximumFrameAgeNanoseconds;
    const bool size_mismatch =
        frame->header.width != width_ || frame->header.height != height_;
    if (stale || size_mismatch) {
        metadata->flags = kProjectBlurSampleFallback;
        if (stale) {
            metadata->flags |= kProjectBlurSampleStale;
        }
        if (size_mismatch) {
            metadata->flags |= kProjectBlurSampleSizeMismatch;
        }
        return WriteBlackFrame(output, output_length, output_pitch);
    }

    metadata->flags = 0;
    return subtype_ == MFVideoFormat_RGB32
        ? WriteBgraFrame(*frame, output, output_length, output_pitch)
        : WriteNv12Frame(*frame, output, output_length, output_pitch);
}

HRESULT SimpleFrameGenerator::WriteBlackFrame(
    BYTE* output,
    DWORD length,
    LONG pitch) const {
    RETURN_HR_IF_NULL(E_POINTER, output);
    RETURN_HR_IF(E_INVALIDARG, pitch <= 0);
    const std::size_t row_bytes = static_cast<std::size_t>(pitch);
    if (subtype_ == MFVideoFormat_RGB32) {
        RETURN_HR_IF(
            HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER),
            row_bytes * height_ > length);
        for (UINT32 row = 0; row < height_; ++row) {
            auto* pixels = reinterpret_cast<std::uint32_t*>(
                output + row * row_bytes);
            std::fill(pixels, pixels + width_, 0xff000000U);
        }
        return S_OK;
    }

    const std::size_t required = row_bytes * height_ * 3U / 2U;
    RETURN_HR_IF(
        HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER),
        required > length);
    for (UINT32 row = 0; row < height_; ++row) {
        std::memset(output + row * row_bytes, 16, width_);
    }
    BYTE* uv = output + row_bytes * height_;
    for (UINT32 row = 0; row < height_ / 2U; ++row) {
        std::memset(uv + row * row_bytes, 128, width_);
    }
    return S_OK;
}

HRESULT SimpleFrameGenerator::WriteBgraFrame(
    const projectblur::virtual_camera::FrameCopy& frame,
    BYTE* output,
    DWORD length,
    LONG pitch) const {
    RETURN_HR_IF_NULL(E_POINTER, output);
    RETURN_HR_IF(E_INVALIDARG, pitch <= 0);
    const std::size_t output_stride = static_cast<std::size_t>(pitch);
    const std::size_t source_stride = frame.header.stride;
    RETURN_HR_IF(
        HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER),
        output_stride * height_ > length ||
            source_stride * height_ > frame.pixels.size() ||
            output_stride < source_stride);
    for (UINT32 row = 0; row < height_; ++row) {
        std::memcpy(
            output + row * output_stride,
            frame.pixels.data() + row * source_stride,
            source_stride);
    }
    return S_OK;
}

HRESULT SimpleFrameGenerator::WriteNv12Frame(
    const projectblur::virtual_camera::FrameCopy& frame,
    BYTE* output,
    DWORD length,
    LONG pitch) const {
    RETURN_HR_IF_NULL(E_POINTER, output);
    RETURN_HR_IF(E_INVALIDARG, pitch <= 0);
    const std::size_t output_stride = static_cast<std::size_t>(pitch);
    const std::size_t required = output_stride * height_ * 3U / 2U;
    RETURN_HR_IF(
        HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER),
        required > length || output_stride < width_);

    BYTE* uv_plane = output + output_stride * height_;
    for (UINT32 row = 0; row < height_; row += 2U) {
        const BYTE* first =
            frame.pixels.data() + static_cast<std::size_t>(row) * frame.header.stride;
        const BYTE* second = first + frame.header.stride;
        BYTE* y_first = output + static_cast<std::size_t>(row) * output_stride;
        BYTE* y_second = y_first + output_stride;
        BYTE* uv = uv_plane + static_cast<std::size_t>(row / 2U) * output_stride;
        for (UINT32 column = 0; column < width_; column += 2U) {
            const BYTE* top_left = first + column * 4U;
            const BYTE* top_right = top_left + 4U;
            const BYTE* bottom_left = second + column * 4U;
            const BYTE* bottom_right = bottom_left + 4U;
            const int b = (top_left[0] + top_right[0] + bottom_left[0] +
                           bottom_right[0]) /
                          4;
            const int g = (top_left[1] + top_right[1] + bottom_left[1] +
                           bottom_right[1]) /
                          4;
            const int r = (top_left[2] + top_right[2] + bottom_left[2] +
                           bottom_right[2]) /
                          4;
            const auto write_y = [](const BYTE* pixel) {
                return ClampByte(
                    ((66 * pixel[2] + 129 * pixel[1] + 25 * pixel[0] + 128) >>
                     8) +
                    16);
            };
            y_first[column] = write_y(top_left);
            y_first[column + 1U] = write_y(top_right);
            y_second[column] = write_y(bottom_left);
            y_second[column + 1U] = write_y(bottom_right);
            uv[column] =
                ClampByte(((-38 * r - 74 * g + 112 * b + 128) >> 8) + 128);
            uv[column + 1U] =
                ClampByte(((112 * r - 94 * g - 18 * b + 128) >> 8) + 128);
        }
    }
    return S_OK;
}

std::uint64_t SimpleFrameGenerator::MonotonicNanoseconds() const noexcept {
    LARGE_INTEGER counter{};
    if (!QueryPerformanceCounter(&counter) || performance_frequency_ == 0) {
        return 0;
    }
    const std::uint64_t ticks =
        static_cast<std::uint64_t>(counter.QuadPart);
    const std::uint64_t seconds = ticks / performance_frequency_;
    const std::uint64_t remainder = ticks % performance_frequency_;
    return seconds * 1'000'000'000ULL +
           remainder * 1'000'000'000ULL / performance_frequency_;
}
