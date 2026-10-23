#include "dusk/xbox_prompts.hpp"

#include "JSystem/J2DGraph/J2DMaterial.h"
#include "JSystem/JUtility/JUTTexture.h"
#include "dusk/settings.h"

#include <xxhash.h>

#include <cstdint>
#include <cstring>

namespace dusk::xbox_prompts {
namespace {

// A prompt texture as the disc holds it, and what replaces it (tools/xbox_prompts.py).
struct Prompt {
    u64 hash;  // XXH64 of the original's image data
    u32 size;  // that data's size
    u16 width;
    u16 height;
    u8 format;     // the original's GX format
    u8 newFormat;  // the replacement's; if it differs, the texture is pointed at the replacement
    const u8* data;
};

#include "dusk/xbox_prompts_data.inc"

// What a layout tints the GameCube's buttons' bases with: TEV colour 1, which J2DPictureEx takes as
// white, and colour 0, its black, where that has the same colour. On the disc only these buttons'
// panes give these textures these colours. Each turns the Xbox 360 controller's colour for the
// button that does the same under its default map: A's green and, for B, X's blue on the base they
// share (tt_zelda_button_ab_maru); RB's grey for Z (im_zelda_button_z_base); and white for X's and
// Y's, whose replacements are drawn in B's red and Y's amber (tools/xbox_prompts.py).
struct Tint {
    u16 width;
    u16 height;
    u8 format;
    GXColorS10 from;
    GXColorS10 to;
};

constexpr Tint kTints[] = {
    {40, 40, GX_TF_IA4, {98, 163, 46, 255}, {96, 185, 40, 255}},
    {40, 40, GX_TF_IA4, {96, 163, 46, 255}, {96, 185, 40, 255}},
    {40, 40, GX_TF_IA4, {200, 39, 39, 255}, {35, 110, 220, 255}},
    {40, 40, GX_TF_IA4, {195, 63, 63, 255}, {35, 110, 220, 255}},
    {48, 48, GX_TF_IA4, {80, 70, 165, 255}, {85, 85, 85, 255}},
    {48, 48, GX_TF_IA4, {110, 105, 165, 255}, {115, 115, 115, 255}},
    {32, 48, GX_TF_RGBA8, {171, 171, 170, 255}, {255, 255, 255, 255}},
    {32, 48, GX_TF_RGBA8, {185, 189, 189, 255}, {255, 255, 255, 255}},
    {48, 32, GX_TF_RGBA8, {161, 166, 166, 255}, {255, 255, 255, 255}},
    {48, 32, GX_TF_RGBA8, {185, 189, 189, 255}, {255, 255, 255, 255}},
};

// A texture's image data is a 32-bit offset from its header (JUTTexture::storeTIMG), which reaches
// the replacement only in a 32-bit address space.
static_assert(sizeof(void*) == 4);

}  // namespace

bool enabled() {
    static const bool enabled = getSettings().game.xbox360ButtonPrompts;
    return enabled;
}

void patch(const ResTIMG* texture) {
    if (!enabled()) {
        return;
    }
    ResTIMG* const timg = const_cast<ResTIMG*>(texture);
    u8* const image = reinterpret_cast<u8*>(timg) +
                      (timg->imageOffset != 0 ? s32(timg->imageOffset) : s32(sizeof(ResTIMG)));
    for (const Prompt& prompt : kPrompts) {
        if (timg->format != prompt.format || timg->width != prompt.width ||
            timg->height != prompt.height || XXH64(image, prompt.size, 0) != prompt.hash)
        {
            continue;
        }
        if (prompt.newFormat == prompt.format) {
            std::memcpy(image, prompt.data, prompt.size);
        } else {
            timg->format = prompt.newFormat;
            timg->imageOffset = static_cast<s32>(
                reinterpret_cast<uintptr_t>(prompt.data) - reinterpret_cast<uintptr_t>(timg));
        }
        return;
    }
}

void tint(J2DMaterial* material) {
    if (!enabled()) {
        return;
    }
    J2DTevBlock* const tev = material->getTevBlock();
    const JUTTexture* const texture = tev->getTexture(0);
    const J2DGXColorS10* const black = tev->getTevColor(0);
    const J2DGXColorS10* const white = tev->getTevColor(1);
    if (texture == NULL || texture->getTexInfo() == NULL || black == NULL || white == NULL) {
        return;
    }
    const ResTIMG* const timg = texture->getTexInfo();
    for (const Tint& tint : kTints) {
        if (timg->width == tint.width && timg->height == tint.height &&
            timg->format == tint.format && white->r == tint.from.r && white->g == tint.from.g &&
            white->b == tint.from.b && white->a == tint.from.a)
        {
            if (black->r == tint.from.r && black->g == tint.from.g && black->b == tint.from.b) {
                tev->setTevColor(0, GXColorS10{tint.to.r, tint.to.g, tint.to.b, black->a});
            }
            tev->setTevColor(1, tint.to);
            return;
        }
    }
}

}  // namespace dusk::xbox_prompts
