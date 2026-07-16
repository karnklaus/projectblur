// ProjectBlur virtual-camera identifiers.
// Media Foundation structure follows Microsoft's MIT-licensed Virtual Camera sample.
#pragma once

#include <guiddef.h>

inline constexpr GUID CLSID_ProjectBlurMediaSource{
    0x615f8dba,
    0x693f,
    0x476c,
    {0x8a, 0x89, 0x37, 0xe6, 0x28, 0x54, 0x26, 0x3d}};
inline constexpr wchar_t kProjectBlurMediaSourceClsid[] =
    L"{615F8DBA-693F-476C-8A89-37E62854263D}";
inline constexpr wchar_t kProjectBlurCameraFriendlyName[] =
    L"ProjectBlur Camera";

inline constexpr GUID PROJECTBLUR_FRAME_MAPPING_NAME{
    0x5c09680e,
    0x7ed2,
    0x44bc,
    {0xb7, 0xed, 0x15, 0x6a, 0x71, 0xf3, 0x6a, 0x09}};
inline constexpr GUID PROJECTBLUR_FRAME_USER_SID{
    0x82ca41cd,
    0x61bc,
    0x4079,
    {0x9d, 0x49, 0xd5, 0x07, 0x0a, 0xe6, 0x8b, 0x32}};
inline constexpr GUID PROJECTBLUR_SAMPLE_SEQUENCE{
    0xd854d3fa,
    0x68f1,
    0x4daf,
    {0xa1, 0xdc, 0xb1, 0xa1, 0x51, 0xaf, 0x6b, 0x45}};
inline constexpr GUID PROJECTBLUR_SAMPLE_SOURCE_TIMESTAMP_NS{
    0x54a02cf6,
    0xe399,
    0x462b,
    {0x93, 0x2d, 0xe8, 0x55, 0x52, 0xbd, 0x9d, 0x4a}};
inline constexpr GUID PROJECTBLUR_SAMPLE_FLAGS{
    0xa9c7dade,
    0xdc40,
    0x4045,
    {0x8c, 0xad, 0xa6, 0x82, 0x52, 0x8e, 0xdc, 0x51}};

inline constexpr std::uint32_t kProjectBlurSampleFallback = 1U << 0;
inline constexpr std::uint32_t kProjectBlurSampleStale = 1U << 1;
inline constexpr std::uint32_t kProjectBlurSampleSizeMismatch = 1U << 2;

// Kept only because the Microsoft-derived media-source base implements IKsControl.
inline constexpr GUID PROPSETID_SIMPLEMEDIASOURCE_CUSTOMCONTROL{
    0x0ce2ef73,
    0x4800,
    0x4f53,
    {0x9b, 0x8e, 0x8c, 0x06, 0x79, 0x0f, 0xc0, 0xc7}};
enum {
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORING = 0,
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_END
};
enum {
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_GRAYSCALE = 0x0FFFFFF,
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_RED = 0x0FF0000,
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_GREEN = 0x000FF00,
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_BLUE = 0x00000FF
};
struct KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_S {
    std::uint32_t ColorMode;
};
using PKSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_S =
    KSPROPERTY_SIMPLEMEDIASOURCE_CUSTOMCONTROL_COLORMODE_S*;
