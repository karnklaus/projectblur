#pragma once

#include "projectblur_frame_protocol.h"

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace projectblur::virtual_camera {

struct FrameCopy final {
    FrameHeader header{};
    std::vector<std::uint8_t> pixels;
};

class FrameReader final {
public:
    FrameReader() = default;
    FrameReader(const FrameReader&) = delete;
    FrameReader& operator=(const FrameReader&) = delete;
    ~FrameReader();

    bool Open(std::wstring_view mapping_name) noexcept;
    bool OpenOrCreate(
        std::wstring_view mapping_name,
        std::wstring_view user_sid,
        std::uint32_t max_width,
        std::uint32_t max_height) noexcept;
    void Close() noexcept;
    [[nodiscard]] std::optional<FrameCopy> ReadLatest(
        unsigned int attempts = 3) const;

private:
    HANDLE mapping_ = nullptr;
    std::byte* view_ = nullptr;
    std::size_t mapped_size_ = 0;
};

}  // namespace projectblur::virtual_camera
