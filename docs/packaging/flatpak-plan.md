# Flatpak Packaging Plan

## Overview

Package Sin's Guide as a Flatpak so users can install and run it without Python tooling, virtual environments, or dependency management. The end result is a single `flatpak install` command.

## Runtime Selection

Use **`org.kde.Platform`** / **`org.kde.Sdk`** (KDE 6.x) — the Qt-included runtime. PySide6 is a Qt binding, so using KDE's platform avoids bundling Qt separately.

| Component | Selection |
|-----------|-----------|
| Runtime | `org.kde.Platform//6.8` |
| SDK | `org.kde.Sdk//6.8` |
| Extensions | `org.freedesktop.Sdk.Extension.rust-stable` (for cryptography builds) |

## Flatpak Manifest Structure (`com.sin_guide.SinsGuide.yml`)

```yaml
id: com.sin_guide.SinsGuide
runtime: org.kde.Platform
runtime-version: '6.8'
sdk: org.kde.Sdk
command: sins-guide

finish-args:
  # X11 for overlay window
  - --socket=x11
  # IPC for Qt shared memory
  - --share=ipc
  # D-Bus session bus (Qt/X11 integration)
  - --socket=session-bus
  # Filesystem access for Steam Proton prefix (Client.txt logging)
  - --filesystem=~/.steam:ro
  - --filesystem=~/.local/share/Steam:ro
  # Wayland (optional, for XWayland Proton)
  - --socket=wayland
  # Device access for screenshots (gem OCR)
  - --device=dri

modules:
  # 1. Tesseract OCR (gem scanning dependency)
  - name: tesseract
    buildsystem: autotools
    sources:
      - type: archive
        url: https://github.com/tesseract-ocr/tesseract/archive/5.5.0.tar.gz
    # tessdata is bundled via a separate module or post-install

  # 2. Python dependencies (flatpak-pip-generator output)
  # Generated via: flatpak-pip-generator --requirements-file=requirements.txt
  - name: python-dependencies
    buildsystem: simple
    build-commands:
      - pip3 install --prefix=${FLATPAK_DEST} --no-deps *.whl
    sources:
      - generated-requirements.json  # auto-generated

  # 3. The application itself
  - name: sins-guide
    buildsystem: simple
    build-commands:
      - pip3 install --prefix=${FLATPAK_DEST} .
      - install -Dm644 com.sin_guide.SinsGuide.desktop ${FLATPAK_DEST}/share/applications/
      - install -Dm644 com.sin_guide.SinsGuide.metainfo.xml ${FLATPAK_DEST}/share/metainfo/
    sources:
      - type: dir
        path: ../..
```

## Python Dependencies

Generate the dependency snapshot with:

```bash
flatpak run --command=flatpak-pip-generator org.freedesktop.Sdk//24.08 \
  $(cat sin_guide/requirements.txt | tr '\n' ' ')
```

This creates `python3-<package>-<version>.json` files that the manifest includes.

### Known Complex Dependencies

| Dependency | Issue | Solution |
|------------|-------|----------|
| **PySide6** | Downloads Qt binaries during pip install | Use `org.kde.Platform` runtime which bundles Qt — build PySide6 from sdist against system Qt, or prebuilt wheel |
| **python-xlib** | Pure Python | No issues |
| **pytesseract** | Wraps `tesseract` binary | Bundled as a separate module above |
| **pillow** | Native extensions | Builds cleanly with org.kde.Sdk |
| **lxml** | Native/libxml2 | Builds cleanly with org.kde.Sdk |

## Permissions Rationale

| Permission | Why |
|------------|-----|
| `--socket=x11` | Transparent overlay window rendered with PySide6/Qt |
| `--share=ipc` | Qt shared memory for X11 SHM |
| `--socket=session-bus` | D-Bus integration (required by some Qt platform plugins) |
| `--filesystem=~/.steam:ro` | Read `Client.txt` from Steam Proton prefix for log parsing |
| `--filesystem=~/.local/share/Steam:ro` | Alternate Steam library location |
| `--device=dri` | GPU access for screenshot capture (gem OCR) |

## Build & Release Workflow

### Initial Setup (one-time)

```bash
# Install Flatpak SDK extensions
flatpak install org.kde.Sdk//6.8 org.kde.Platform//6.8

# Generate Python dep manifests
flatpak run --command=flatpak-pip-generator org.freedesktop.Sdk//24.08 \
  -r sin_guide/requirements.txt -o generated-requirements
```

### Build Command

```bash
flatpak-builder build-dir com.sin_guide.SinsGuide.yml --force-clean
```

### Test Install

```bash
flatpak-builder --user --install build-dir com.sin_guide.SinsGuide.yml --force-clean
```

### Release Build

```bash
# Tag the release
git tag v1.0.0

# Production build with GPG signing
flatpak-builder --gpg-sign=<key-id> --repo=repo build-dir com.sin_guide.SinsGuide.yml

# Create Flatpak bundle
flatpak build-bundle repo SinsGuide-1.0.0.flatpak com.sin_guide.SinsGuide
```

## Action Items

- [ ] Create `com.sin_guide.SinsGuide.yml` manifest
- [ ] Create desktop file (`com.sin_guide.SinsGuide.desktop`)
- [ ] Create AppStream metainfo (`com.sin_guide.SinsGuide.metainfo.xml`)
- [ ] Run `flatpak-pip-generator` to freeze Python dependencies
- [ ] Set up CI workflow to build Flatpak on tag pushes
- [ ] Test on a clean Fedora/SteamOS environment
- [ ] Publish to GitHub Releases on merge to `main`
