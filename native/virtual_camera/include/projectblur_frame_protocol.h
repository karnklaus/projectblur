#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace projectblur::virtual_camera {

inline constexpr std::array<char, 8> kFrameMagic{
    'P', 'B', 'L', 'U', 'R', 'F', '0', '1'};
inline constexpr std::uint32_t kFrameProtocolVersion = 1;
inline constexpr std::uint32_t kPixelFormatBgra32 = 1;

#pragma pack(push, 1)
struct FrameHeader final {
    char magic[8];
    std::uint32_t header_size;
    std::uint32_t protocol_version;
    std::uint64_t sequence;
    std::uint32_t width;
    std::uint32_t height;
    std::uint32_t stride;
    std::uint32_t pixel_format;
    std::uint64_t timestamp_ns;
    std::uint64_t payload_size;
};
#pragma pack(pop)

static_assert(sizeof(FrameHeader) == 56);
static_assert(offsetof(FrameHeader, sequence) == 16);

}  // namespace projectblur::virtual_camera
