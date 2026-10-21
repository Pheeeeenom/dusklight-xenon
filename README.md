# Dusklight on the Xbox 360 (beta)

> [!NOTE]
> This is [xenosworks/dusklight-xenon](https://github.com/xenosworks/dusklight-xenon), a port of Dusklight to the
> Xbox 360. Dusklight's team doesn't make or support it, so report its problems here, not to them. Dusklight's own
> README follows below the line, unchanged.

Dusklight runs on the Xbox 360 as a homebrew title, built with [xsdk](https://github.com/xenosworks/xsdk) and drawn
through [vulkan4xenon](https://github.com/xenosworks/vulkan4xenon) at 1280x720 with 4 samples of multisampling.
[docs/README-xsdk.md](docs/README-xsdk.md) says how it's built and what the port changes.

### What you need

- An RGH or JTAG Xbox 360. The title isn't signed, so a retail console won't start it.
- `dusklight.xex` and the `res` folder that comes with it, from this repository's
  [releases](https://github.com/xenosworks/dusklight-xenon/releases).
- Your own copy of the US GameCube disc, GZ2E01, dumped as a plain disc image and named `dusklight.iso` ("Dump your
  game" below says how). Compressed images such as RVZ aren't read on the Xbox 360, nor are Wii discs; Dolphin or
  nodtool turns an RVZ back into an ISO.

Put all three in one folder on the console's hard disk, by FTP for example, and start `dusklight.xex` from your
dashboard. To quit, press the Guide button and choose Xbox Home.

### Saves and settings

They're kept in `TwilitRealm\Dusklight\` in that folder: the settings in `config.json`, the memory card's saves in
`USA\Card A\` as `.gci` files, and the shaders the console has compiled in `shaders\`. Back that folder up to keep
your saves.

### Known limits of the beta

- Dusklight's own menu, which Back opens, isn't drawn yet, but it still opens and takes the controller. If the game
  stops answering the controller, press Back again to close it.
- The first visit to an area may show things popping in while the console compiles shaders it hasn't needed before.
  They're kept, so later visits don't.
- Ordon runs at about 28 to 30 fps.

### Reporting a problem

Open an issue with the
[problem report form](https://github.com/xenosworks/dusklight-xenon/issues/new?template=bug-report.yml): what went
wrong and where, whether it happens every time and how to make it happen, and your save if you can.

---

<div align="center">
  <img src="res/logo.png" alt="Logo" width="640">

  <p align="center">
    <a href="https://twilitrealm.dev">Official Website</a>
    •
    <a href="https://discord.gg/6NpMhefCK9">Discord</a>
  </p>
</div>

# Overview

Dusklight is a reverse-engineered reimplementation of Twilight Princess.

It aims to be as accurate as possible to the original while also providing new options, enhancements, and tools to customize your experience.

> [!IMPORTANT]
> Dusklight's official website is https://twilitrealm.dev/, any other website is not affiliated and may be promoting AI-generated misinformation.

# Setup

> [!IMPORTANT]
> Dusklight does *not* provide any copyrighted assets. You must provide your own copy of the original game.

> [!IMPORTANT]
> At a minimum, Dusklight requires a GPU with support for D3D12, Vulkan 1.1+, or Metal. For older devices, best-effort support is provided for D3D11 and OpenGL ES (Android), but will not achieve full accuracy or performance. Your experience with specific hardware, operating systems, and drivers may vary.

### 1. Dump your game

You must dump your own copy of the game. Please see [this article](https://wiki.dolphin-emu.org/index.php?title=Ripping_Games) for instructions. After dumping, you can use a program like [Dolphin](https://dolphin-emu.org/) or [nodtool](https://github.com/encounter/nod/releases) to convert the `.iso` to `.rvz` to save space.

Dusklight currently supports all commercial discs except for Wii's Korean release.

> [!NOTE]
> Dusklight is based on the [Twilight Princess decompilation](https://github.com/zeldaret/tp), which is currently only matching for GameCube. As a result, even when playing Dusklight with a Wii disc, you will be presented with the GameCube version's HUD and certain other specificities.

### 2. Install Dusklight

Visit the [official installation guide](https://twilitrealm.dev/install/) for full instructions.

# Building

If you'd like to build Dusklight from source, please read the [build instructions](docs/building.md).

Pull requests are welcomed! Note that we do not accept contributions that are primarily AI-generated and will close your PR if we suspect as much. Please also see the [code conventions](docs/code-conventions.md).

# Credits

Special thanks to the [TP decompilation](https://github.com/zeldaret/tp) team, the GC/Wii decompilation community, the [Aurora](https://github.com/encounter/aurora) developers, the [TP speedrunning community](https://zsrtp.link), and all [contributors](https://github.com/TwilitRealm/dusklight/graphs/contributors).

<br/>
<div align="center">
    <a href="https://github.com/encounter/aurora">
        <img src="assets/aurora-powered.png" alt="Powered by Aurora" width="800">
    </a>
</div>
