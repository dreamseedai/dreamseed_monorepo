# VS Code PHP Extensions: Cleanup and Install

This folder contains safe, idempotent scripts to standardize VS Code extensions for PHP work.

All scripts are DRY‑RUN by default except `install_php_extensions.sh` (which only adds missing extensions). Use `--apply` to actually uninstall in the cleanup script.

## Core set (customize as needed)
- bmewburn.vscode-intelephense-client (PHP language)
- xdebug.php-debug (PHP Debug)
- junstyle.php-cs-fixer (PHP CS Fixer)

You can add more via:
- Environment variable: `KEEP_EXTENSIONS` (spaces or commas)
- File next to scripts: `keep-extensions.txt` (one ID per line)
	- Start from `keep-extensions.txt.sample` → copy to `keep-extensions.txt` and uncomment
- For installer, extra IDs via `EXTRA_PHP_EXTENSIONS` or `extra-extensions.txt`
	- Start from `extra-extensions.txt.sample` → copy to `extra-extensions.txt` and uncomment

## Scripts

1) Remove non‑PHP extensions (dry‑run)

```bash
cd infra/devtools/vscode-extensions/php
./cleanup_php_only.sh
```

2) Actually apply removals

```bash
./cleanup_php_only.sh --apply
```

3) Install core PHP extensions (idempotent)

```bash
./install_php_extensions.sh
```

4) Verify current state

```bash
./verify_cleanup.sh
```

## Notes
- Requires VS Code CLI `code` in PATH. Install via Command Palette → "Shell Command: Install 'code' command in PATH".
- Only user-installed extensions are touched; built-in extensions are not affected.
- Prefer running in a dedicated VS Code Profile for PHP to avoid removing tools you need for other stacks.
