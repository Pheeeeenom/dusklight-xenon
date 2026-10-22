# Xbox 360 (xsdk)

Dusklight for the Xbox 360, a homebrew title built with [xsdk](https://github.com/xenosworks/xsdk), a homebrew SDK
that builds titles for the console's retail kernel. GX draws through the vulkan4xenon backend of
[aurora-xenon](https://github.com/xenosworks/aurora-xenon), this repository's `extern/aurora`, on
[vulkan4xenon](https://github.com/xenosworks/vulkan4xenon), a Vulkan 1.0 subset on xsdk's GPU layer. The changes are
on the `xenon` branch. Game code changed for the port sits under `__XSDK__` with the original kept, as
`docs/code-conventions.md` asks of `TARGET_PC`.

The top of `README.md` says what a player needs, where saves go and what the beta doesn't do yet.

## Building

Build these first, in WSL with xsdk's toolchain:

-   xsdk: `make` in its checkout builds `libxsdk.a` (its `docs/GETTING_STARTED.md` has the toolchain);
-   vulkan4xenon: `make` in its checkout, against the same xsdk, builds `libvulkan4xenon.a`;
-   SDL from [SDL-xenon](https://github.com/xenosworks/SDL-xenon), as its `docs/README-xsdk.md` says;
-   [glslang-xenon](https://github.com/xenosworks/glslang-xenon) needs only checking out: this build adds it.

vulkan4xenon and glslang-xenon are taken from beside this repository unless `VULKAN4XENON_DIR` and
`GLSLANG_XENON_DIR` name them. Then, with the submodules checked out (`git submodule update --init --recursive`):

```bash
cmake -S. -Bbuild-xsdk -GNinja -DCMAKE_TOOLCHAIN_FILE=<xsdk>/cmake/xsdk.cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DSDL3_DIR=<SDL-xenon's build>
cmake --build build-xsdk --target dusklight
```

That builds `build-xsdk/dusklight.xex`, with its own title ID, 0x4455534B ("DUSK"), and name, and copies `res` beside
it. On the console the two go in one folder with the player's `dusklight.iso`.

Settings for a build, each under `if (XSDK)` in `CMakeLists.txt`:

-   `DUSK_XSDK_MSAA`: the EFB's samples, 1, 2 or 4; 4 by default, as Ordon ran as fast at 4 as at 1 and 2
    (vulkan4xenon's docs/ROADMAP.md, milestone 30).
-   `DUSK_XSDK_GLSL_PACK=OFF` links no shader pack, so every program is compiled on the console.
-   `DUSK_XSDK_RECORD_GLSL=ON` builds a title that draws nothing, on Aurora's null backend, and records each
    pipeline's GLSL into `game:\shaders`, for the pack.

## What the port changes

-   **The disc:** `game:\dusklight.iso`, a plain GameCube image, opened at start with no launcher screen; without it
    the title ends (`src/m_Do/m_Do_main.cpp`). Aurora reads it through its C reader, as nod's Rust doesn't build for
    xsdk.
-   **The screen:** 1280x720, which the console scales to its output, and the EFB at `DUSK_XSDK_MSAA` samples.
-   **The start:** vulkan4xenon's logo for 2 s, then the GameCube's warning, Nintendo and Dolby screens while the game
    loads, as its first frames drawn (`src/dusk/main.cpp`, `src/d/d_s_logo.cpp`).
-   **Memory:** MEM1 of 144 MB, not the PC's 256, and Aurora's frame pools and texture caches sized from what a run
    through the title scene used, as the CPU and GPU share 512 MB (`CMakeLists.txt`).
-   **Threads:** the game's own threads on hardware thread 1, away from the game thread and Aurora's workers
    (`src/dusk/OSThread.cpp`); Aurora places its own.
-   **Byte order:** no swaps on the big-endian console (`include/helpers/endian.h`).
-   **Left out:** the network, the crash handler, Discord, Sentry and code mods; the game's reports are on, and the
    log is at Info, as each line is a write to the hard disk.
-   **The run's log:** each stage as it starts, the frame rate and the title's memory every 10 s, and the heaps' peaks a
    minute into the title scene; 600 frames into the title scene, a capture, `game:\dusklight_title.ppm`
    (`src/dusk/xenon_run.cpp`).

The player's files go in `game:\TwilitRealm\Dusklight\`, SDL-xenon's preference path for Dusklight: `config.json`,
the memory card in `USA\Card A\`, the programs compiled on the console in `shaders\`, and Dusklight's logs in `logs\`.
xsdk's log is `game:\dusklight.log`.

## The shader pack

`platforms/xenon/glsl_pack.c` holds the 150 programs recorded so far, compiled on the PC to SPIR-V and Xenos
microcode. A program it doesn't hold is compiled on the console the first time the game asks for it, and kept
(vulkan4xenon's docs/ROADMAP.md, milestone 13). To add to the pack, run a `DUSK_XSDK_RECORD_GLSL` build as far as it
should record, copy what it wrote in `game:\shaders` to `platforms/xenon/shaders`, and in WSL, from this repository's
root:

```bash
python3 extern/aurora/tools/build_glsl_pack.py --vulkan4xenon <vulkan4xenon> --xost <xsdk>/xenos-toolchain \
    --glslang ~/xsdk-gcc/bin/glslang --optimize --output platforms/xenon/glsl_pack platforms/xenon/shaders
```

## What's drawn

What Aurora's vulkan4xenon backend draws and what it skips is in aurora-xenon's `docs/README-xsdk.md`. Dusklight's
menus and Aurora's ImGui overlay are drawn since vulkan4xenon's milestone 16; with advanced settings on, the Interface
tab's Debug Overlays option shows ImGui's debug overlays.
