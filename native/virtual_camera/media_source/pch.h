// Selected media-source structure is derived from Microsoft's MIT-licensed
// Windows Camera Virtual Camera sample at commit
// 790ac218eba8b6995393e9cc9537dfd7730fdb83.
#pragma once

#ifndef NOMINMAX
#define NOMINMAX
#endif
#define WIN32_LEAN_AND_MEAN

#include <unknwn.h>
#include <windows.h>
#include <propvarutil.h>
#include <ole2.h>
#include <Ks.h>
#include <ksproxy.h>
#include <ksmedia.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfobjects.h>
#include <mferror.h>
#include <mfvirtualcamera.h>
#include <strsafe.h>

#include <algorithm>
#include <cstdint>
#include <memory>
#include <string>

#define RESULT_DIAGNOSTICS_LEVEL 4
#include <wil/cppwinrt.h>
#include <wil/result.h>
#include <wil/com.h>
#include <wil/resource.h>

#include "frame_reader.h"
#include "VirtualCameraMediaSource.h"
#include "SimpleFrameGenerator.h"
#include "SimpleMediaSource.h"
#include "SimpleMediaStream.h"
#include "VirtualCameraMediaSourceActivate.h"

#pragma comment(lib, "mfuuid")
#pragma comment(lib, "mf")
#pragma comment(lib, "mfplat")
#pragma comment(lib, "mfsensorgroup")
#pragma comment(lib, "advapi32")

inline void DebugPrint(LPCWSTR format, ...) {
    WCHAR buffer[512]{};
    va_list arguments;
    va_start(arguments, format);
    StringCbVPrintfW(buffer, sizeof(buffer), format, arguments);
    va_end(arguments);
    OutputDebugStringW(buffer);
}

#define DEBUG_MSG(...) \
    do { \
        DebugPrint(L"[%s@%d] ", TEXT(__FUNCTION__), __LINE__); \
        DebugPrint(__VA_ARGS__); \
        DebugPrint(L"\n"); \
    } while (false)

namespace wilEx {
template<typename T>
wil::unique_cotaskmem_array_ptr<T> make_unique_cotaskmem_array(
    std::size_t count) {
    wil::unique_cotaskmem_array_ptr<T> array;
    const std::size_t bytes =
        sizeof(wil::details::element_traits<T>::type) * count;
    void* pointer = ::CoTaskMemAlloc(bytes);
    if (pointer != nullptr) {
        ZeroMemory(pointer, bytes);
        array.reset(
            reinterpret_cast<typename wil::details::element_traits<T>::type*>(
                pointer),
            count);
    }
    return array;
}
}  // namespace wilEx

namespace winrt {
template<> bool is_guid_of<IMFMediaSourceEx>(guid const& id) noexcept;
template<> bool is_guid_of<IMFMediaStream2>(guid const& id) noexcept;
template<> bool is_guid_of<IMFActivate>(guid const& id) noexcept;
}  // namespace winrt
