#include "frame_reader.h"

#include <cstdint>
#include <iostream>
#include <string>

int wmain(int argc, wchar_t* argv[]) {
    if (argc != 4) {
        std::wcerr << L"usage: frame_reader_smoke <mapping> <width> <height>\n";
        return 2;
    }
    std::uint32_t expected_width = 0;
    std::uint32_t expected_height = 0;
    try {
        expected_width = static_cast<std::uint32_t>(std::stoul(argv[2]));
        expected_height = static_cast<std::uint32_t>(std::stoul(argv[3]));
    } catch (...) {
        return 2;
    }

    projectblur::virtual_camera::FrameReader reader;
    if (!reader.Open(argv[1])) {
        return 3;
    }
    const auto frame = reader.ReadLatest();
    if (!frame || frame->header.width != expected_width ||
        frame->header.height != expected_height || frame->pixels.empty()) {
        return 4;
    }
    std::wcout << L"sequence=" << frame->header.sequence << L" width="
               << frame->header.width << L" height=" << frame->header.height
               << L" bytes=" << frame->pixels.size() << L"\n";
    return 0;
}
