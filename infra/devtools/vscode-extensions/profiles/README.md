# VS Code Profiles: DreamSeed-Full and PHP-Maintenance

This folder provides scripts and lists to bootstrap two VS Code profiles:

- DreamSeed-Full (daily default): Python/FastAPI, R/Plumber+Quarto, Frontend, K8s/GCP, GitHub
- PHP-Maintenance (secondary): Minimal PHP set

Note: Profiles are created via UI: Command Palette → "Profiles: Create Profile…". The scripts below install/uninstall extensions; enable/disable per profile is managed by VS Code.

## Quick start

1) Ensure `code` CLI is in PATH (Command Palette → Shell Command: Install 'code' command in PATH)

2) Install DreamSeed-Full set (safe; idempotent) or open with profile in one step

```bash
cd infra/devtools/vscode-extensions/profiles
./dreamseed_full_setup.sh
# or open VS Code with the profile (creates if missing)
./open_dreamseed_full.sh               # install + open
./open_dreamseed_full.sh --apply-remove  # also uninstall conflicts
```

3) Optionally remove conflicting/duplicate extensions (dry-run by default)

```bash
./dreamseed_full_setup.sh --apply-remove
```

4) Install PHP-Maintenance minimal set or open with profile

```bash
./php_maintenance_setup.sh
# or
./open_php_maintenance.sh
```

5) Create profiles and enable sets
- Create "DreamSeed-Full" profile; keep AI/Python/R/Frontend/K8s/Git/GitHub tools enabled
- Create "PHP-Maintenance" profile; enable only the PHP set

## Lists you can edit (no script changes needed)

- `dreamseed-full.install.txt` → DreamSeed-Full recommended
- `dreamseed-full.remove.txt` → DreamSeed-Full unwanted/conflicts (uninstall with `--apply-remove`)
- `php-maintenance.install.txt` → PHP minimal set (and optional utilities)

## Workspace recommendations (for repo-wide guidance)

Copy this into `.vscode/extensions.json` (or use the prepared sample):

- Sample file: `extensions.recommended.json`
- Place at repo root: `.vscode/extensions.json`

This helps new environments get the right suggestions and avoid duplicates.

## One-command switch

```bash
# From this folder:
./switch_profile.sh dreamseed   # DreamSeed-Full (optionally pass --apply-remove)
./switch_profile.sh php         # PHP-Maintenance
```

## Tips
- Use VS Code Profiles to keep each stack lean. You can switch profiles from the Accounts menu or Command Palette.
- If listener leak warnings resurface, keep only one Chat tool active in the current profile and close chat panels when not in use.
