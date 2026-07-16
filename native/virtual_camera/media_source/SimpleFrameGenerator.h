// ProjectBlur shared-memory frame generator.
#pragma once

#include <cstdint>
#include <string_view>

struct ProjectBlurFrameMetadata final {
    std::uint64_t sequence = 0;
    std::uint64_t source_timestamp_ns = 0;
    std::uint32_t flags = kProjectBlurSampleFallback;
};

class SimpleFrameGenerator final {
public:
    HRESULT Initialize(
        IMFMediaType* media_type,
        std::wstring_view mapping_name,
        std::wstring_view user_sid);

    HRESULT CreateFrame(
        BYTE* output,
        DWORD output_length,
        LONG output_pitch,
        ULONG unused_rgb_mask,
        ProjectBlurFrameMetadata* metadata);

private:
    HRESULT WriteBlackFrame(BYTE* output, DWORD length, LONG pitch) const;
    HRESULT WriteBgraFrame(
        const projectblur::virtual_camera::FrameCopy& frame,
        BYTE* output,
        DWORD length,
        LONG pitch) const;
    HRESULT WriteNv12Frame(
        const projectblur::virtual_camera::FrameCopy& frame,
        BYTE* output,
        DWORD length,
        LONG pitch) const;
    [[nodiscard]] std::uint64_t MonotonicNanoseconds() const noexcept;

    projectblur::virtual_camera::FrameReader reader_;
    UINT32 width_ = 0;
    UINT32 height_ = 0;
    GUID subtype_ = GUID_NULL;
    std::uint64_t performance_frequency_ = 0;
};
