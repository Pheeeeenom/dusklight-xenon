#pragma once

class J2DMaterial;
struct ResTIMG;

namespace dusk::xbox_prompts {

/// Whether the game shows Xbox 360 button prompts: the setting as it was at start, as archives that
/// stay loaded keep the textures `patch` swapped.
bool enabled();

/// If `enabled` and `texture` is a GameCube button prompt, swaps it for its Xbox 360 one where it
/// lies, in its archive. Called as the game stores a texture (JUTTexture::storeTIMG), before it's
/// drawn.
void patch(const ResTIMG* texture);

/// If `enabled` and `material` tints a GameCube button's base as a layout sets it, tints it in the
/// Xbox 360 controller's colour for the button that does the same. Called as a layout's material is
/// made (J2DMaterialFactory::create).
void tint(J2DMaterial* material);

}  // namespace dusk::xbox_prompts
