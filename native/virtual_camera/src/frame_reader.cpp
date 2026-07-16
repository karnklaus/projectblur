#include "frame_reader.h"

#include <algorithm>
#include <atomic>
#include <cstring>
#include <limits>
#include <sddl.h>
#include <string>

namespace projectblur::virtual_camera {

FrameReader::~FrameReader() {
    Close();
}

bool FrameReader::Open(std::wstring_view mapping_name) noexcept {
    Close();
    const std::wstring owned_name{mapping_name};
    mapping_ = OpenFileMappingW(FILE_MAP_READ, FALSE, owned_name.c_str());
    if (mapping_ == nullptr) {
        return false;
    }
    view_ = static_cast<std::byte*>(
        MapViewOfFile(mapping_, FILE_MAP_READ, 0, 0, 0));
    if (view_ == nullptr) {
        Close();
        return false;
    }
    MEMORY_BASIC_INFORMATION information{};
    if (VirtualQuery(view_, &information, sizeof(information)) == 0) {
        Close();
        return false;
    }
    mapped_size_ = information.RegionSize;
    return mapped_size_ >= sizeof(FrameHeader);
}

bool FrameReader::OpenOrCreate(
    std::wstring_view mapping_name,
    std::wstring_view user_sid,
    std::uint32_t max_width,
    std::uint32_t max_height) noexcept {
    Close();
    if (mapping_name.empty() || user_sid.empty() || max_width == 0 ||
        max_height == 0) {
        SetLastError(ERROR_INVALID_PARAMETER);
        return false;
    }
    constexpr std::uint64_t bytes_per_pixel = 4;
    const std::uint64_t pixel_capacity =
        static_cast<std::uint64_t>(max_width) * max_height * bytes_per_pixel;
    const std::uint64_t mapping_size = sizeof(FrameHeader) + pixel_capacity;
    if (pixel_capacity / bytes_per_pixel / max_width != max_height ||
        mapping_size > std::numeric_limits<std::size_t>::max()) {
        SetLastError(ERROR_ARITHMETIC_OVERFLOW);
        return false;
    }

    const std::wstring sddl =
        L"D:P(A;;GA;;;SY)(A;;GA;;;LS)(A;;GA;;;" +
        std::wstring(user_sid) + L")";
    PSECURITY_DESCRIPTOR descriptor = nullptr;
    if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl.c_str(),
            SDDL_REVISION_1,
            &descriptor,
            nullptr)) {
        return false;
    }
    SECURITY_ATTRIBUTES security{};
    security.nLength = sizeof(security);
    security.lpSecurityDescriptor = descriptor;

    const std::wstring owned_name{mapping_name};
    mapping_ = CreateFileMappingW(
        INVALID_HANDLE_VALUE,
        &security,
        PAGE_READWRITE,
        static_cast<DWORD>(mapping_size >> 32U),
        static_cast<DWORD>(mapping_size & 0xffffffffU),
        owned_name.c_str());
    const DWORD creation_error = GetLastError();
    LocalFree(descriptor);
    if (mapping_ == nullptr) {
        return false;
    }
    view_ = static_cast<std::byte*>(MapViewOfFile(
        mapping_,
        FILE_MAP_READ | FILE_MAP_WRITE,
        0,
        0,
        static_cast<SIZE_T>(mapping_size)));
    if (view_ == nullptr) {
        Close();
        return false;
    }
    mapped_size_ = static_cast<std::size_t>(mapping_size);

    if (creation_error != ERROR_ALREADY_EXISTS) {
        FrameHeader header{};
        std::copy(kFrameMagic.begin(), kFrameMagic.end(), header.magic);
        header.header_size = sizeof(FrameHeader);
        header.protocol_version = kFrameProtocolVersion;
        header.pixel_format = kPixelFormatBgra32;
        std::memcpy(view_, &header, sizeof(header));
        MemoryBarrier();
    }
    return true;
}

void FrameReader::Close() noexcept {
    if (view_ != nullptr) {
        UnmapViewOfFile(view_);
        view_ = nullptr;
    }
    if (mapping_ != nullptr) {
        CloseHandle(mapping_);
        mapping_ = nullptr;
    }
    mapped_size_ = 0;
}

std::optional<FrameCopy> FrameReader::ReadLatest(unsigned int attempts) const {
    if (view_ == nullptr || attempts == 0) {
        return std::nullopt;
    }
    const auto* sequence_pointer = reinterpret_cast<const std::uint64_t*>(
        view_ + offsetof(FrameHeader, sequence));
    std::atomic_ref<const std::uint64_t> sequence{*sequence_pointer};

    for (unsigned int attempt = 0; attempt < attempts; ++attempt) {
        const std::uint64_t before = sequence.load(std::memory_order_acquire);
        if (before == 0 || (before & 1U) != 0) {
            continue;
        }

        FrameCopy copy;
        std::memcpy(&copy.header, view_, sizeof(copy.header));
        if (!std::equal(
                kFrameMagic.begin(),
                kFrameMagic.end(),
                copy.header.magic) ||
            copy.header.header_size != sizeof(FrameHeader) ||
            copy.header.protocol_version != kFrameProtocolVersion ||
            copy.header.pixel_format != kPixelFormatBgra32 ||
            copy.header.width == 0 || copy.header.height == 0 ||
            copy.header.stride != copy.header.width * 4ULL) {
            return std::nullopt;
        }
        if (copy.header.height >
            std::numeric_limits<std::uint64_t>::max() / copy.header.stride) {
            return std::nullopt;
        }
        const std::uint64_t expected_size =
            static_cast<std::uint64_t>(copy.header.stride) * copy.header.height;
        if (copy.header.payload_size != expected_size ||
            copy.header.payload_size > mapped_size_ - sizeof(FrameHeader)) {
            return std::nullopt;
        }

        const auto* payload = reinterpret_cast<const std::uint8_t*>(
            view_ + sizeof(FrameHeader));
        copy.pixels.assign(payload, payload + copy.header.payload_size);
        const std::uint64_t after = sequence.load(std::memory_order_acquire);
        if (before == after && (after & 1U) == 0) {
            copy.header.sequence = after;
            return copy;
        }
    }
    return std::nullopt;
}

}  // namespace projectblur::virtual_camera
