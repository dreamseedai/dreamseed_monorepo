# DreamSeedAI Branding Assets

This folder contains branding assets for DreamSeedAI. Assets are organized under `DreamSeedAI_Logos/`.

## Structure

- DreamSeedAI_Logos/
  - Imported/                    # Original desktop PNG logos (source)
    - DreamSeedAI_logo1.png
    - DreamSeedAI_logo2.png
    - DreamSeedAI_logo3.png
    - DreamSeedAI_logo4.png
    - DreamSeedAI_logo5.png
    - DreamSeedAI_logo6.png
  - Exported_SVG/                # SVG wrappers (embed transparent PNG)
    - DreamSeedAI_logo1.svg
    - ...
  - Exported_PNG/                # Size exports from cleaned PNGs
    - 32x32/
    - 64x64/
    - 128x128/
    - 512x512/

## Imported Desktop-Ready PNG Logos

Six high-resolution PNG files suitable for desktop use reside in `DreamSeedAI_Logos/Imported/` (files `DreamSeedAI_logo1.png` through `DreamSeedAI_logo6.png`). These images are part of the official DreamSeedAI branding assets.

## Exports

- Background cleaning: near-white backgrounds are made transparent.
- SVG: For portability, we provide SVG wrappers that embed the cleaned PNG at native size (scales via `viewBox`).
- PNG sizes: 32x32, 64x64, 128x128, 512x512 generated under `Exported_PNG/`.

Note on vectorization: High-fidelity path vectorization (curves, multi-color) usually requires Inkscape Trace Bitmap or potrace/autotrace. The provided SVG wrappers ensure broad compatibility while keeping style intact. If you need true vector paths, run Inkscape’s trace in batch and replace the wrappers.

## Archive

A zip archive `DreamSeedAI_Logos.zip` is available in this folder and includes the full `DreamSeedAI_Logos/` directory tree (including `Imported/`, `Exported_SVG/`, and `Exported_PNG/`). To rebuild:

```bash
cd assets/branding
zip -r -9 DreamSeedAI_Logos.zip DreamSeedAI_Logos
```
