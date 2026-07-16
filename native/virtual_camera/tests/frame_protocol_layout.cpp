#include "projectblur_frame_protocol.h"

#include <algorithm>

int main() {
    using projectblur::virtual_camera::FrameHeader;
    using projectblur::virtual_camera::kFrameMagic;

    FrameHeader header{};
    std::copy(kFrameMagic.begin(), kFrameMagic.end(), header.magic);
    header.header_size = sizeof(FrameHeader);
    header.protocol_version =
        projectblur::virtual_camera::kFrameProtocolVersion;
    header.pixel_format = projectblur::virtual_camera::kPixelFormatBgra32;

    return std::equal(kFrameMagic.begin(), kFrameMagic.end(), header.magic) &&
                   header.header_size == 56
               ? 0
               : 1;
}
