// ProjectBlur virtual-camera registration and performance probe.
#ifndef NOMINMAX
#define NOMINMAX
#endif
#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <mfapi.h>
#include <mferror.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <mfvirtualcamera.h>
#include <sddl.h>
#include <wrl/client.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "VirtualCameraMediaSource.h"

#pragma comment(lib, "advapi32")
#pragma comment(lib, "mf")
#pragma comment(lib, "mfplat")
#pragma comment(lib, "mfreadwrite")
#pragma comment(lib, "mfuuid")
#pragma comment(lib, "mfsensorgroup")
#pragma comment(lib, "ole32")

using Microsoft::WRL::ComPtr;

namespace {
class HResultError final : public std::runtime_error {
public:
    HResultError(HRESULT result, std::string_view operation)
        : std::runtime_error(Format(result, operation)), result_(result) {}

    [[nodiscard]] HRESULT result() const noexcept { return result_; }

private:
    static std::string Format(HRESULT result, std::string_view operation) {
        std::ostringstream stream;
        stream << operation << " failed (HRESULT 0x" << std::hex
               << static_cast<std::uint32_t>(result) << ')';
        return stream.str();
    }
    HRESULT result_;
};

void Check(HRESULT result, std::string_view operation) {
    if (FAILED(result)) {
        throw HResultError(result, operation);
    }
}

class ComRuntime final {
public:
    ComRuntime() {
        const HRESULT com = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        if (FAILED(com) && com != RPC_E_CHANGED_MODE) {
            Check(com, "CoInitializeEx");
        }
        owns_com_ = SUCCEEDED(com);
        Check(MFStartup(MF_VERSION), "MFStartup");
        owns_mf_ = true;
    }
    ~ComRuntime() {
        if (owns_mf_) {
            MFShutdown();
        }
        if (owns_com_) {
            CoUninitialize();
        }
    }

private:
    bool owns_com_ = false;
    bool owns_mf_ = false;
};

std::wstring CurrentUserSid() {
    HANDLE raw_token = nullptr;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &raw_token)) {
        throw HResultError(HRESULT_FROM_WIN32(GetLastError()), "OpenProcessToken");
    }
    const auto close_token =
        std::unique_ptr<void, decltype(&CloseHandle)>(raw_token, CloseHandle);
    DWORD bytes = 0;
    GetTokenInformation(raw_token, TokenUser, nullptr, 0, &bytes);
    if (GetLastError() != ERROR_INSUFFICIENT_BUFFER || bytes == 0) {
        throw HResultError(
            HRESULT_FROM_WIN32(GetLastError()),
            "GetTokenInformation(size)");
    }
    std::vector<std::byte> buffer(bytes);
    if (!GetTokenInformation(
            raw_token,
            TokenUser,
            buffer.data(),
            bytes,
            &bytes)) {
        throw HResultError(
            HRESULT_FROM_WIN32(GetLastError()),
            "GetTokenInformation");
    }
    const auto* token_user = reinterpret_cast<const TOKEN_USER*>(buffer.data());
    LPWSTR raw_sid = nullptr;
    if (!ConvertSidToStringSidW(token_user->User.Sid, &raw_sid)) {
        throw HResultError(
            HRESULT_FROM_WIN32(GetLastError()),
            "ConvertSidToStringSidW");
    }
    const std::unique_ptr<void, decltype(&LocalFree)> sid_guard(raw_sid, LocalFree);
    return std::wstring(raw_sid);
}

std::wstring MappingName(const std::wstring& sid) {
    return L"Global\\ProjectBlurFrame-" + sid;
}

std::filesystem::path ExecutableDirectory() {
    std::wstring buffer(32768, L'\0');
    const DWORD length = GetModuleFileNameW(
        nullptr,
        buffer.data(),
        static_cast<DWORD>(buffer.size()));
    if (length == 0 || length >= buffer.size()) {
        throw HResultError(
            HRESULT_FROM_WIN32(GetLastError()),
            "GetModuleFileNameW");
    }
    buffer.resize(length);
    return std::filesystem::path(buffer).parent_path();
}

void SetRegistryString(
    HKEY root,
    const std::wstring& subkey,
    const wchar_t* name,
    const std::wstring& value) {
    HKEY raw_key = nullptr;
    const LONG created = RegCreateKeyExW(
        root,
        subkey.c_str(),
        0,
        nullptr,
        REG_OPTION_NON_VOLATILE,
        KEY_SET_VALUE,
        nullptr,
        &raw_key,
        nullptr);
    if (created != ERROR_SUCCESS) {
        throw HResultError(HRESULT_FROM_WIN32(created), "RegCreateKeyExW");
    }
    const auto close_key =
        std::unique_ptr<std::remove_pointer_t<HKEY>, decltype(&RegCloseKey)>(
            raw_key,
            RegCloseKey);
    const DWORD bytes =
        static_cast<DWORD>((value.size() + 1U) * sizeof(wchar_t));
    const LONG set = RegSetValueExW(
        raw_key,
        name,
        0,
        REG_SZ,
        reinterpret_cast<const BYTE*>(value.c_str()),
        bytes);
    if (set != ERROR_SUCCESS) {
        throw HResultError(HRESULT_FROM_WIN32(set), "RegSetValueExW");
    }
}

std::wstring ComRegistryPath() {
    return std::wstring(L"Software\\Classes\\CLSID\\") +
           kProjectBlurMediaSourceClsid + L"\\InprocServer32";
}

void RegisterComServer(const std::filesystem::path& dll, bool machine) {
    if (!std::filesystem::is_regular_file(dll)) {
        throw std::runtime_error("media-source DLL does not exist: " + dll.string());
    }
    const HKEY root = machine ? HKEY_LOCAL_MACHINE : HKEY_CURRENT_USER;
    SetRegistryString(root, ComRegistryPath(), nullptr, dll.wstring());
    SetRegistryString(root, ComRegistryPath(), L"ThreadingModel", L"Both");
}

void UnregisterComServer(bool machine) {
    const HKEY root = machine ? HKEY_LOCAL_MACHINE : HKEY_CURRENT_USER;
    const std::wstring parent = std::wstring(L"Software\\Classes\\CLSID\\") +
                                kProjectBlurMediaSourceClsid;
    const LONG result = RegDeleteTreeW(root, parent.c_str());
    if (result != ERROR_SUCCESS && result != ERROR_FILE_NOT_FOUND) {
        throw HResultError(HRESULT_FROM_WIN32(result), "RegDeleteTreeW");
    }
}

ComPtr<IMFVirtualCamera> CreateVirtualCamera() {
    ComPtr<IMFVirtualCamera> camera;
    Check(
        MFCreateVirtualCamera(
            MFVirtualCameraType_SoftwareCameraSource,
            MFVirtualCameraLifetime_System,
            MFVirtualCameraAccess_CurrentUser,
            kProjectBlurCameraFriendlyName,
            kProjectBlurMediaSourceClsid,
            nullptr,
            0,
            &camera),
        "MFCreateVirtualCamera");
    const std::wstring sid = CurrentUserSid();
    const std::wstring mapping = MappingName(sid);
    Check(
        camera->SetString(PROJECTBLUR_FRAME_MAPPING_NAME, mapping.c_str()),
        "set frame mapping attribute");
    Check(
        camera->SetString(PROJECTBLUR_FRAME_USER_SID, sid.c_str()),
        "set user SID attribute");
    return camera;
}

struct Device final {
    ComPtr<IMFActivate> activate;
    std::wstring friendly_name;
    std::wstring symbolic_link;
};

std::vector<Device> EnumerateProjectBlurCameras() {
    ComPtr<IMFAttributes> attributes;
    Check(MFCreateAttributes(&attributes, 1), "MFCreateAttributes");
    Check(
        attributes->SetGUID(
            MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE,
            MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_GUID),
        "set device source type");
    IMFActivate** raw_devices = nullptr;
    UINT32 count = 0;
    Check(
        MFEnumDeviceSources(attributes.Get(), &raw_devices, &count),
        "MFEnumDeviceSources");
    std::vector<Device> devices;
    for (UINT32 index = 0; index < count; ++index) {
        ComPtr<IMFActivate> activate;
        activate.Attach(raw_devices[index]);
        raw_devices[index] = nullptr;
        LPWSTR raw_name = nullptr;
        UINT32 name_length = 0;
        if (FAILED(activate->GetAllocatedString(
                MF_DEVSOURCE_ATTRIBUTE_FRIENDLY_NAME,
                &raw_name,
                &name_length))) {
            continue;
        }
        const std::wstring name(raw_name, name_length);
        CoTaskMemFree(raw_name);
        if (name.find(L"ProjectBlur") == std::wstring::npos) {
            continue;
        }
        LPWSTR raw_link = nullptr;
        UINT32 link_length = 0;
        std::wstring link;
        if (SUCCEEDED(activate->GetAllocatedString(
                MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_SYMBOLIC_LINK,
                &raw_link,
                &link_length))) {
            link.assign(raw_link, link_length);
            CoTaskMemFree(raw_link);
        }
        devices.push_back(Device{activate, name, link});
    }
    CoTaskMemFree(raw_devices);
    return devices;
}

std::uint64_t MonotonicNanoseconds() {
    LARGE_INTEGER frequency{};
    LARGE_INTEGER counter{};
    if (!QueryPerformanceFrequency(&frequency) ||
        !QueryPerformanceCounter(&counter) || frequency.QuadPart <= 0) {
        return 0;
    }
    const auto ticks = static_cast<std::uint64_t>(counter.QuadPart);
    const auto per_second = static_cast<std::uint64_t>(frequency.QuadPart);
    return ticks / per_second * 1'000'000'000ULL +
           ticks % per_second * 1'000'000'000ULL / per_second;
}

void ProbeMediaSource() {
    ComPtr<IMFActivate> activate;
    Check(
        CoCreateInstance(
            CLSID_ProjectBlurMediaSource,
            nullptr,
            CLSCTX_INPROC_SERVER,
            IID_PPV_ARGS(&activate)),
        "CoCreateInstance(ProjectBlur media source)");
    const std::wstring sid = CurrentUserSid();
    Check(
        activate->SetString(
            PROJECTBLUR_FRAME_MAPPING_NAME,
            MappingName(sid).c_str()),
        "set probe mapping attribute");
    Check(
        activate->SetString(PROJECTBLUR_FRAME_USER_SID, sid.c_str()),
        "set probe user SID attribute");
    ComPtr<IMFMediaSource> source;
    Check(
        activate->ActivateObject(IID_PPV_ARGS(&source)),
        "activate ProjectBlur media source");
    ComPtr<IMFPresentationDescriptor> descriptor;
    Check(
        source->CreatePresentationDescriptor(&descriptor),
        "create ProjectBlur presentation descriptor");
    DWORD stream_count = 0;
    Check(
        descriptor->GetStreamDescriptorCount(&stream_count),
        "count ProjectBlur streams");
    source->Shutdown();
    std::cout << "media_source=ok\nstreams=" << stream_count << '\n';
}

double Percentile(std::vector<double> values, double percentile) {
    if (values.empty()) {
        return 0.0;
    }
    std::sort(values.begin(), values.end());
    const std::size_t rank = std::max<std::size_t>(
        1,
        static_cast<std::size_t>(std::ceil(percentile * values.size())));
    return values[std::min(rank - 1U, values.size() - 1U)];
}

struct BenchmarkOptions final {
    double seconds = 10.0;
    double warmup_seconds = 1.5;
    UINT32 width = 1280;
    UINT32 height = 720;
    UINT32 fps = 30;
    std::filesystem::path output;
};

std::wstring OptionValue(
    int argc,
    wchar_t* argv[],
    std::wstring_view name,
    std::wstring_view fallback = L"") {
    for (int index = 2; index + 1 < argc; ++index) {
        if (argv[index] == name) {
            return argv[index + 1];
        }
    }
    return std::wstring(fallback);
}

bool HasOption(int argc, wchar_t* argv[], std::wstring_view name) {
    for (int index = 2; index < argc; ++index) {
        if (argv[index] == name) {
            return true;
        }
    }
    return false;
}

BenchmarkOptions ParseBenchmarkOptions(int argc, wchar_t* argv[]) {
    BenchmarkOptions options;
    const auto seconds = OptionValue(argc, argv, L"--seconds");
    const auto warmup = OptionValue(argc, argv, L"--warmup");
    const auto width = OptionValue(argc, argv, L"--width");
    const auto height = OptionValue(argc, argv, L"--height");
    const auto fps = OptionValue(argc, argv, L"--fps");
    const auto output = OptionValue(argc, argv, L"--output");
    if (!seconds.empty()) options.seconds = std::stod(seconds);
    if (!warmup.empty()) options.warmup_seconds = std::stod(warmup);
    if (!width.empty()) options.width = static_cast<UINT32>(std::stoul(width));
    if (!height.empty()) options.height = static_cast<UINT32>(std::stoul(height));
    if (!fps.empty()) options.fps = static_cast<UINT32>(std::stoul(fps));
    if (!output.empty()) options.output = output;
    if (options.seconds <= 0 || options.warmup_seconds < 0 ||
        options.fps == 0 ||
        !((options.width == 1280 && options.height == 720) ||
          (options.width == 1920 && options.height == 1080))) {
        throw std::invalid_argument("unsupported benchmark options");
    }
    return options;
}

std::string RunBenchmark(const BenchmarkOptions& options) {
    const auto devices = EnumerateProjectBlurCameras();
    if (devices.empty()) {
        throw std::runtime_error("ProjectBlur Camera is not installed");
    }
    ComPtr<IMFMediaSource> source;
    Check(
        devices.front().activate->ActivateObject(IID_PPV_ARGS(&source)),
        "activate ProjectBlur Camera");
    ComPtr<IMFSourceReader> reader;
    Check(
        MFCreateSourceReaderFromMediaSource(source.Get(), nullptr, &reader),
        "MFCreateSourceReaderFromMediaSource");
    ComPtr<IMFMediaType> media_type;
    Check(MFCreateMediaType(&media_type), "MFCreateMediaType");
    Check(media_type->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video), "set major type");
    Check(media_type->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_NV12), "set NV12 type");
    Check(
        MFSetAttributeSize(
            media_type.Get(), MF_MT_FRAME_SIZE, options.width, options.height),
        "set frame size");
    Check(
        MFSetAttributeRatio(
            media_type.Get(), MF_MT_FRAME_RATE, options.fps, 1),
        "set frame rate");
    Check(
        reader->SetCurrentMediaType(
            static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
            nullptr,
            media_type.Get()),
        "select benchmark media type");

    using Clock = std::chrono::steady_clock;
    const auto overall_start = Clock::now();
    const auto measurement_start = overall_start +
        std::chrono::duration_cast<Clock::duration>(
            std::chrono::duration<double>(options.warmup_seconds));
    const auto measurement_end = measurement_start +
        std::chrono::duration_cast<Clock::duration>(
            std::chrono::duration<double>(options.seconds));
    std::vector<double> read_ms;
    std::vector<double> intervals_ms;
    std::vector<double> frame_age_ms;
    std::set<std::uint64_t> unique_sequences;
    std::uint64_t first_sequence = 0;
    std::uint64_t last_sequence = 0;
    std::uint64_t samples = 0;
    std::uint64_t fallback_samples = 0;
    std::uint64_t metadata_samples = 0;
    Clock::time_point previous_arrival{};

    while (Clock::now() < measurement_end) {
        const auto read_start = Clock::now();
        DWORD stream_index = 0;
        DWORD stream_flags = 0;
        LONGLONG timestamp = 0;
        ComPtr<IMFSample> sample;
        Check(
            reader->ReadSample(
                static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM),
                0,
                &stream_index,
                &stream_flags,
                &timestamp,
                &sample),
            "IMFSourceReader::ReadSample");
        const auto arrival = Clock::now();
        if ((stream_flags & MF_SOURCE_READERF_ENDOFSTREAM) != 0) {
            break;
        }
        if (!sample || arrival < measurement_start) {
            continue;
        }
        ++samples;
        read_ms.push_back(std::chrono::duration<double, std::milli>(
                              arrival - read_start)
                              .count());
        if (previous_arrival != Clock::time_point{}) {
            intervals_ms.push_back(std::chrono::duration<double, std::milli>(
                                       arrival - previous_arrival)
                                       .count());
        }
        previous_arrival = arrival;

        UINT64 sequence = 0;
        UINT64 source_timestamp_ns = 0;
        UINT32 flags = 0;
        if (SUCCEEDED(sample->GetUINT64(PROJECTBLUR_SAMPLE_SEQUENCE, &sequence)) &&
            SUCCEEDED(sample->GetUINT64(
                PROJECTBLUR_SAMPLE_SOURCE_TIMESTAMP_NS,
                &source_timestamp_ns)) &&
            SUCCEEDED(sample->GetUINT32(PROJECTBLUR_SAMPLE_FLAGS, &flags))) {
            ++metadata_samples;
            if ((flags & kProjectBlurSampleFallback) != 0) {
                ++fallback_samples;
            }
            if (sequence > 0) {
                unique_sequences.insert(sequence);
                if (first_sequence == 0) first_sequence = sequence;
                last_sequence = sequence;
            }
            const std::uint64_t now_ns = MonotonicNanoseconds();
            if (source_timestamp_ns > 0 && now_ns >= source_timestamp_ns &&
                (flags & kProjectBlurSampleFallback) == 0) {
                frame_age_ms.push_back(
                    static_cast<double>(now_ns - source_timestamp_ns) / 1e6);
            }
        }
    }
    reader.Reset();
    source->Shutdown();
    source.Reset();

    const double elapsed = std::chrono::duration<double>(
                               std::min(Clock::now(), measurement_end) -
                               measurement_start)
                               .count();
    const double delivered_fps = elapsed > 0 ? samples / elapsed : 0.0;
    const std::uint64_t published_span =
        first_sequence > 0 && last_sequence >= first_sequence
        ? (last_sequence - first_sequence) / 2U + 1U
        : 0;
    const std::uint64_t dropped_unique =
        published_span > unique_sequences.size()
        ? published_span - unique_sequences.size()
        : 0;
    const std::uint64_t duplicate_samples =
        samples > fallback_samples + unique_sequences.size()
        ? samples - fallback_samples - unique_sequences.size()
        : 0;

    std::ostringstream json;
    json << std::fixed << std::setprecision(3)
         << "{\n"
         << "  \"schema_version\": 1,\n"
         << "  \"camera\": \"ProjectBlur Camera\",\n"
         << "  \"width\": " << options.width << ",\n"
         << "  \"height\": " << options.height << ",\n"
         << "  \"requested_fps\": " << options.fps << ",\n"
         << "  \"measurement_seconds\": " << elapsed << ",\n"
         << "  \"samples_delivered\": " << samples << ",\n"
         << "  \"delivered_fps\": " << delivered_fps << ",\n"
         << "  \"p95_read_ms\": " << Percentile(read_ms, 0.95) << ",\n"
         << "  \"p95_inter_frame_ms\": " << Percentile(intervals_ms, 0.95) << ",\n"
         << "  \"metadata_samples\": " << metadata_samples << ",\n"
         << "  \"fallback_samples\": " << fallback_samples << ",\n"
         << "  \"unique_source_frames\": " << unique_sequences.size() << ",\n"
         << "  \"source_frame_span\": " << published_span << ",\n"
         << "  \"source_frames_not_observed\": " << dropped_unique << ",\n"
         << "  \"duplicate_samples\": " << duplicate_samples << ",\n"
         << "  \"p95_frame_age_ms\": " << Percentile(frame_age_ms, 0.95) << "\n"
         << "}";
    return json.str();
}

void WriteResult(const std::string& value, const std::filesystem::path& output) {
    std::cout << value << '\n';
    if (!output.empty()) {
        std::ofstream file(output, std::ios::binary | std::ios::trunc);
        if (!file) {
            throw std::runtime_error("unable to open benchmark output");
        }
        file << value << '\n';
    }
}

void PrintUsage() {
    std::wcout
        << L"ProjectBlurCameraControl commands:\n"
        << L"  install --machine-com [--dll path]\n"
        << L"  start\n  stop\n  remove --machine-com\n"
        << L"  status\n  mapping-name\n  probe-source\n"
        << L"  benchmark [--seconds 10] [--warmup 1.5] [--width 1280] "
           L"[--height 720] [--fps 30] [--output file]\n";
}
}  // namespace

int wmain(int argc, wchar_t* argv[]) {
    try {
        if (argc < 2) {
            PrintUsage();
            return 2;
        }
        const std::wstring command = argv[1];
        if (command == L"mapping-name") {
            std::wcout << MappingName(CurrentUserSid()) << L'\n';
            return 0;
        }

        ComRuntime runtime;
        if (command == L"probe-source") {
            ProbeMediaSource();
            return 0;
        }
        if (command == L"install") {
            const bool machine = HasOption(argc, argv, L"--machine-com");
            if (!machine) {
                throw std::invalid_argument(
                    "install requires --machine-com because Windows Camera "
                    "Frame Server cannot activate a per-user COM server");
            }
            std::filesystem::path dll = OptionValue(argc, argv, L"--dll");
            if (dll.empty()) {
                dll = ExecutableDirectory() / L"ProjectBlurMediaSource.dll";
            }
            dll = std::filesystem::absolute(dll);
            RegisterComServer(dll, machine);
            UnregisterComServer(false);
            auto camera = CreateVirtualCamera();
            Check(camera->Start(nullptr), "IMFVirtualCamera::Start");
            LPWSTR symbolic_link = nullptr;
            UINT32 link_length = 0;
            if (SUCCEEDED(camera->GetAllocatedString(
                    MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_SYMBOLIC_LINK,
                    &symbolic_link,
                    &link_length))) {
                std::wcout << L"symbolic_link="
                           << std::wstring(symbolic_link, link_length) << L'\n';
                CoTaskMemFree(symbolic_link);
            }
            Check(camera->Shutdown(), "IMFVirtualCamera::Shutdown");
            std::wcout << L"installed=ProjectBlur Camera\n"
                       << L"mapping=" << MappingName(CurrentUserSid()) << L'\n'
                       << L"com_scope=" << (machine ? L"machine" : L"current-user")
                       << L'\n';
            return 0;
        }
        if (command == L"start") {
            auto camera = CreateVirtualCamera();
            Check(camera->Start(nullptr), "IMFVirtualCamera::Start");
            Check(camera->Shutdown(), "IMFVirtualCamera::Shutdown");
            std::wcout << L"started=ProjectBlur Camera\n";
            return 0;
        }
        if (command == L"stop") {
            auto camera = CreateVirtualCamera();
            Check(camera->Stop(), "IMFVirtualCamera::Stop");
            Check(camera->Shutdown(), "IMFVirtualCamera::Shutdown");
            std::wcout << L"stopped=ProjectBlur Camera\n";
            return 0;
        }
        if (command == L"remove") {
            const bool machine = HasOption(argc, argv, L"--machine-com");
            if (!machine) {
                throw std::invalid_argument(
                    "remove requires --machine-com to unregister the "
                    "Frame Server-visible COM source");
            }
            auto camera = CreateVirtualCamera();
            Check(camera->Remove(), "IMFVirtualCamera::Remove");
            Check(camera->Shutdown(), "IMFVirtualCamera::Shutdown");
            UnregisterComServer(machine);
            if (machine) {
                UnregisterComServer(false);
            }
            std::wcout << L"removed=ProjectBlur Camera\n";
            return 0;
        }
        if (command == L"status") {
            const auto devices = EnumerateProjectBlurCameras();
            std::wcout << L"count=" << devices.size() << L'\n';
            for (const auto& device : devices) {
                std::wcout << L"name=" << device.friendly_name << L'\n'
                           << L"symbolic_link=" << device.symbolic_link << L'\n';
            }
            return devices.empty() ? 3 : 0;
        }
        if (command == L"benchmark") {
            const BenchmarkOptions options = ParseBenchmarkOptions(argc, argv);
            WriteResult(RunBenchmark(options), options.output);
            return 0;
        }
        PrintUsage();
        return 2;
    } catch (const HResultError& error) {
        std::cerr << error.what() << '\n';
        const int exit_code = static_cast<int>(error.result() & 0xffffU);
        return exit_code == 0 ? 1 : exit_code;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
