# Ketcher Standalone Assets (Offline)

This folder enables completely offline usage of the Ketcher chemical editor inside the admin editor dialog.

## What to place here

Download the official Ketcher Standalone build and place these files under `public/ketcher/standalone/`:

Recommended: copy the full `dist/` directory from the `ketcher-standalone` npm package into `public/ketcher/standalone/`.
This typically includes:
- `main.js`, `index.js`
- `binaryWasm/`, `binaryWasmNoRender/`, `cjs/`, `jsNoRender/`, `infrastructure/`
- CSS is not always provided; the standalone build generally works without a separate CSS file.

## Where to get the files

You can obtain the bundle from the npm registry tarball and extract the `dist/` folder:
- Tarball URL pattern: `https://registry.npmjs.org/ketcher-standalone/-/ketcher-standalone-<version>.tgz`
After extracting, copy the `package/dist/*` contents into `admin_front/public/ketcher/standalone/`.

## How it works

By default, `/ketcher/index.html` uses a dynamic loader:
- It attempts to read `/ketcher/standalone/sri.json` for integrity hashes.
- It then loads `standalone/main.js` with integrity when available, falling back to `standalone/index.js`, and finally to the CDN as a last resort.
- After the script is loaded, it initializes the editor on `#ketcher-container`.

You can force a static load for review/testing by appending `?loader=static` to the URL:
- The page contains a non-executing template tag:
   `<script id="ds-ketcher-static-template" src="standalone/main.js" integrity="..." crossorigin="anonymous" defer type="application/json"></script>`
- In static mode, the page injects a real `<script>` using the attributes from that template, so you can verify a simple, pinned load path.
- The vendoring script keeps the integrity attribute in this file up to date.

## Verifying

1. Ensure files exist:
   - `admin_front/public/ketcher/standalone/ketcher-standalone.min.js`
   - `admin_front/public/ketcher/standalone/ketcher-standalone.min.css`
2. Extract `dist/` into `admin_front/public/ketcher/standalone/` (so that `main.js` exists there).
3. Start the admin frontend and open the editor chemistry dialog.
4. Disable internet or block CDNs to confirm it still loads using local assets.

## Notes

- No changes are required in `RichTextEditor.tsx`; only the iframe page logic references these paths.
- If your build uses different filenames or nested paths, update `/public/ketcher/index.html` accordingly.

## Optional: Subresource Integrity (SRI)

If you want to lock the JS assets to a known build, generate hashes for `main.js` and `index.js` and place them in `public/ketcher/standalone/sri.json`:

Example `sri.json` contents:
{
   "main.js": "sha256-<BASE64_SHA256>",
   "index.js": "sha256-<BASE64_SHA256>"
}

When provided, the page will attach integrity attributes while loading the scripts.

In static mode (`?loader=static`), the integrity value is taken from the template tag in `index.html`. The vendoring script updates this automatically.
