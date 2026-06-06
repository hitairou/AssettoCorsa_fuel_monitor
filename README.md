# ecoran_fuel_monitor

Assetto Corsa in-game Python app for monitoring fuel economy, demand power,
lap fuel usage, BSFC operating points, and debug telemetry during EcoRun
testing.

## Repository Role

This directory is the source-of-truth development copy:

```text
C:\Development\Github\ecoran_fuel_monitor
```

The Assetto Corsa runtime copy is only a deploy target:

```text
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\ecoran_fuel_monitor
```

Do not edit the runtime copy directly unless it is an emergency hotfix. Make
changes here, commit them, then deploy with `deploy.ps1`.

## Layout

```text
ecoran_fuel_monitor.py  Assetto Corsa Python app entry point
sim_info.py             Shared-memory wrapper
config/                 Vehicle, strategy, BSFC, and torque config
docs/                   Architecture, assumptions, config notes, install notes
modules/                App logic, telemetry, windows, renderers, metrics
third_party/            Runtime compatibility files required by AC Python
```

## Development Workflow

1. Edit files under this repository.
2. Run a syntax check:

```powershell
python -m py_compile .\ecoran_fuel_monitor.py .\modules\*.py
```

3. Deploy to Assetto Corsa:

```powershell
.\deploy.ps1
```

4. Launch from Content Manager and verify in game.
5. Commit the verified change:

```powershell
git status
git add .
git commit -m "Describe the change"
```

## Deploy

Default deploy command:

```powershell
.\deploy.ps1
```

Preview without copying:

```powershell
.\deploy.ps1 -DryRun
```

Deploy to a different Assetto Corsa app folder:

```powershell
.\deploy.ps1 -Destination "D:\SteamLibrary\steamapps\common\assettocorsa\apps\python\ecoran_fuel_monitor"
```

`deploy.ps1` excludes Git metadata, Python caches, and runtime logs.

## GitHub Remote

After creating an empty GitHub repository, connect it with:

```powershell
git remote add origin https://github.com/<owner>/<repo>.git
git branch -M main
git push -u origin main
```

Use a private repository if vehicle data, measured maps, or competition setup
should not be public.

## Runtime Notes

- `config/strategy.ini` controls measurement-session start mode, gear display
  offset, dynamic 8-lap estimate settings, UI preset, and graph scaling.
- `config/vehicle.ini` contains vehicle constants such as fuel density,
  drivetrain efficiency, gear ratios, race distance, and lap count.
- Runtime logs and Python caches are intentionally ignored by Git.

## Power Graph Diagnostics

Power graph diagnostics are hidden during normal use. To validate renderer
internals, set `power_graph_debug_overlay = 1` or `debug_mode = 1` in
`config/strategy.ini`, then check:

1. Main HUD `REV` changes after Power renderer edits.
2. Power window shows the `GREV` line.
3. Power graph test lines cover the full graph area when overlay is enabled.
4. `histE` increases over time and stays near the expected rolling length.
5. `last` and `cur` values match the bar display closely.
6. `pts` is at least 2 and the last history point and current point are near the right edge.
7. `err` is empty.
