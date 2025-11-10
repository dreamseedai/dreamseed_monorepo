# WeasyPrint runtime dependencies and troubleshooting

This report generator (`shared/irt/reports/drift_monthly.py`) uses WeasyPrint to render HTML to PDF. While the Python package is installed in the repo venv, successful PDF generation on Linux requires several system libraries.

## Ubuntu packages (22.04/24.04)

Install the following runtime libraries on the host or inside your Docker image:

```bash
sudo apt-get update
sudo apt-get install -y \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 \
  libffi8 \
  libjpeg-turbo8 \
  libpng16-16 \
  shared-mime-info \
  fonts-dejavu-core \
  fonts-liberation \
  fonts-noto-cjk
```

Notes:
- Package names can vary slightly across Ubuntu releases. If `libffi8` isn’t available, use the closest `libffi` runtime for your distro.
- Add any specific fonts your reports need (e.g., CJK, emoji). DejaVu + Liberation + Noto covers most cases.

## Quick smoke test

After installing system packages and `pip install weasyprint` in your venv, run a minimal render test:

```bash
python -c "from weasyprint import HTML; HTML(string='<!doctype html><h1>Hello WeasyPrint</h1>').write_pdf('/tmp/hello.pdf')" && ls -lh /tmp/hello.pdf
```

If this succeeds, the core rendering stack (Cairo/Pango/GDK-Pixbuf) is ready.

## Common errors and fixes

- Import works, but PDF generation fails with Cairo/Pango errors
  - Ensure the packages above are installed in the runtime environment (host or container). These are native libs used by WeasyPrint.
- Missing fonts or wrong glyphs
  - Install appropriate font packages (e.g., `fonts-noto-cjk` for Korean, `fonts-noto-color-emoji` for emoji). You can also embed web fonts via CSS `@font-face` in the HTML template.
- Running inside Docker
  - Prefer baking the packages into your image. See `infra/pdf_lambda/Dockerfile` for a reference pattern and add the runtime libs listed above.

## Reference
- WeasyPrint docs: https://doc.weasyprint.org/
- Cairo: https://www.cairographics.org/
- Pango: https://pango.gnome.org/