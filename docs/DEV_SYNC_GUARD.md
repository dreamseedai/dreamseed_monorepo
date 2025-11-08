# Dev Sync Guard (Linux + Windows)

This adds reliable, reboot-safe sync readiness on the server (Linux) and re-applies client IDE settings on login (Windows) to keep remote editing snappy and consistent across VS Code, Cursor, Continue, and Windsurf.

## Linux server (systemd service + timer)

Files:
- infra/systemd/dev-sync-guard.sh — Ensures inotify limits and cleans stale editor sockets
- infra/systemd/dev-sync-guard.service — Runs the script at boot (oneshot)
- infra/systemd/dev-sync-guard.timer — Runs at boot + hourly

Install on server (run on the Linux server):

```bash
# One-liner installer (from repo root)
sudo bash infra/systemd/install_dev_sync_guard.sh install

# Verify
systemctl status dev-sync-guard.service --no-pager
systemctl list-timers | grep dev-sync-guard
sysctl fs.inotify.max_user_watches   # expect >= 1048576
journalctl -u dev-sync-guard.service -n 50 --no-pager
```

What it does:
- Raises `fs.inotify.max_user_watches` to 1,048,576 (if below)
- Notes presence of `~/.vscode-server` and `~/.cursor-server`
- Cleans stale `*.sock` files older than 7 days in those folders

## Windows client (PowerShell + Scheduled Task)

File:
- `scripts/devtools/windows/DevSyncGuard.ps1`

Place and run:

```powershell
# One-liner installer (Admin PowerShell, from repo root)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\devtools\windows\Install-DevSyncGuard.ps1

# Run once manually to verify (optional)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\DevSync\DevSyncGuard.ps1
```

Auto-run at login (Administrator PowerShell):

```powershell
$Action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"`"C:\DevSync\DevSyncGuard.ps1`"`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel LeastPrivilege
Register-ScheduledTask -TaskName "DevSyncGuard" -Action $Action -Trigger $Trigger -Principal $Principal -Description "VSCode/Cursor/Continue/Windsurf 동기화 보장" -Force
```

What it does:
- Backs up settings for VS Code, Cursor, Windsurf, SSH config
- Enforces auto-save and minimal watcher exclusions for VS Code/Cursor
- Forces Windsurf Live Sync and aggressive pull interval
- Warns if your SSH alias requires manual addition

## Quick checklist

After server reboot:
- `sysctl fs.inotify.max_user_watches` shows `>= 1048576`
- `systemctl status dev-sync-guard.timer --no-pager` shows active timer
- `journalctl -u dev-sync-guard.service -n 50 --no-pager` is clean

After Windows login:
- Task Scheduler → `DevSyncGuard` → Last Run Result `0x0`
- Manual run `C:\DevSync\DevSyncGuard.ps1` produces no errors

Live sync behavior:
- Save in VS Code → change appears in Cursor/Continue/Windsurf within ~1s
- Windsurf pulls remote changes automatically without manual actions

## Customization tips

- If Windsurf uses different setting keys in your build, edit the keys at the bottom of `DevSyncGuard.ps1`.
- Replace the `dev-server` SSH alias with the alias you actually use.
- For highly ephemeral servers, consider a user-level unit in addition to the system service.

## Uninstall

Linux:
```bash
sudo bash infra/systemd/install_dev_sync_guard.sh uninstall
```

Windows (Admin PowerShell):
```powershell
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\devtools\windows\Install-DevSyncGuard.ps1 -Uninstall
```
