# Installation Guide - ecoran_fuel_monitor

## Install Path

Copy `apps/python/ecoran_fuel_monitor/` to:

```text
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\ecoran_fuel_monitor\
```

Expected structure:

```text
ecoran_fuel_monitor\
├─ ecoran_fuel_monitor.py
├─ sim_info.py
├─ config\
├─ docs\
├─ modules\
└─ third_party\
```

## Enable the App

1. Start Assetto Corsa.
2. Open `Options -> General -> UI Modules`.
3. Enable `ecoran_fuel_monitor`.

Only the main module needs to be enabled. The extra Power / Lap / BSFC / Debug
windows are created by the same script at runtime.

## First Launch

1. Enter a driving session.
2. Open `ecoran_fuel_monitor`.
3. Use Main HUD buttons to open `PWR`, `LAP`, `BSFC`, `DBG`.
4. Use the Debug window's `Gate Control` section for gate editing / recording.

## Persisted Files

### UI layout

```text
%LOCALAPPDATA%\ecoran_fuel_monitor\ui_state.json
```

### Gate definitions

```text
apps/python/ecoran_fuel_monitor/config/gates/<track_key>.json
```

Gate files are auto-saved after edits and auto-restored when the same
track/layout is loaded again.

## Verification

A healthy startup should show:

- Main HUD with only three values
- Power graph covering 20 seconds
- Lap table with borders
- Debug window with units and Gate Control buttons
- BSFC heatmap with cell values and trace

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Main HUD appears but values stay `---` | shared memory not ready | enter a live session and retry |
| Gate file does not restore | no saved file for current `track_key` | create/save gates once on that layout |
| Gate load warns but app keeps running | broken JSON | delete or fix the corresponding file under `config/gates/` |
| Layout resets every launch | `ui.restore_state = 0` or save failure | enable restore or check `%LOCALAPPDATA%` write access |
