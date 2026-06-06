# Config File Formats - ecoran_fuel_monitor

## vehicle.ini

Standard INI format. Values are flattened by `data_loader.load_ini()`, so both
`fuel_density_g_per_ml` and `vehicle.fuel_density_g_per_ml` can be read.

Example:

```ini
[VEHICLE]
mass_total                = 98.65
crr                       = 0.0025
cd                        = 0.355
frontal_area              = 0.3846
rho_air                   = 1.225
fuel_density_g_per_ml     = 0.778
drivetrain_efficiency     = 0.9
primary_ratio             = 4.058
secondary_ratio           = 2.944
gear_1                    = 3.181
rear_tire_circumference_m = 1.5
fuel_tank_capacity_ml     = 200.0
rule_time_limit_s         = 2536.70
rule_total_distance_m     = 17616.0
total_laps                = 8
lap_distance_m            = 2202.0
gravity                   = 9.81
```

Important key:

- `fuel_density_g_per_ml`
  Used by `compute_fuel_flow()`. If missing, the app falls back to `0.778`.

## strategy.ini

Example:

```ini
[ENGINE]
rpm_on_threshold  = 800
rpm_off_threshold = 500

[FUEL]
start_penalty_ml  = 0.5

[SMOOTHING]
speed_window      = 5
grade_window      = 5

[TIMING]
update_interval_s = 0.1

[RACE]
lap_distance_m    = 2202.0
race_total_laps   = 8
rule_time_limit_s = 2536.70

[MEASUREMENT]
measurement_start_mode            = first_cross_sf
ignore_initial_partial_lap        = 1
use_dynamic_8lap_estimate         = 1
min_progress_for_dynamic_estimate = 0.10
min_time_for_dynamic_estimate     = 10.0
gear_display_offset               = -1

[GRADE]
vertical_axis_index = 1
grade_fallback_mode = pitch
grade_max_abs       = 0.5
grade_min_ds        = 0.05

[POWER]
power_graph_auto_scale = 1
power_graph_scale_w    = 2000.0

[DEBUG]
debug_mode = 0

[UI]
ui.preset       = overview
ui.restore_state = 1
```

## Measurement Keys

### `measurement_start_mode`

Allowed values:

- `session_start`
- `first_cross_sf`
- `manual_arm_then_cross_sf`

Meaning:

- `session_start`
  Measurement begins immediately after entering the session.
- `first_cross_sf`
  Measurement begins on the first start/finish crossing.
- `manual_arm_then_cross_sf`
  Measurement begins only after arming, then crossing start/finish.

Recommended default:

- `first_cross_sf`

### `ignore_initial_partial_lap`

- `1`: do not store the pre-measurement partial lap as a completed row
- `0`: allow the first partial lap to become lap history

Recommended default:

- `1`

### `use_dynamic_8lap_estimate`

- `1`: allow provisional current-lap projection
- `0`: use completed laps only

### `min_progress_for_dynamic_estimate`

Minimum provisional lap progress required before dynamic 8-lap estimation is
allowed.

Recommended default:

- `0.10`

### `min_time_for_dynamic_estimate`

Minimum current-lap elapsed time in seconds before dynamic 8-lap estimation is
allowed.

Recommended default:

- `10.0`

### `gear_display_offset`

Integer offset applied to raw AC gear for UI display.

Example:

- raw neutral reported as `1`
- stock HUD shows `N`
- use `gear_display_offset = -1`

## Power Graph Keys

### `power_graph_auto_scale`

- `1`: auto-scale graph and diverging bars from recent history
- `0`: use fixed `power_graph_scale_w`

### `power_graph_scale_w`

Fixed half-scale used when auto-scale is off.

## UI Keys

### `ui.preset`

Startup window visibility preset.

Allowed values:

- `overview`
- `analysis`
- `lap`
- `bsfc`
- `debug`

### `ui.restore_state`

Whether to restore the saved window layout and visibility state from:

```text
%LOCALAPPDATA%\ecoran_fuel_monitor\ui_state.json
```

- `1`: restore saved layout and visibility
- `0`: ignore saved visibility and use `ui.preset`

## Lap Table Column Names

Short labels in the UI map to these formal names:

- `Lap` -> lap number
- `Econ` -> `Fuel Econ [km/L]`
- `Fuel` -> `Fuel Used [mL]`
- `Spd` -> `Avg Speed [km/h]`
- `Eng kJ` -> `Engine Energy [kJ]`
- `Roll` -> `Roll Energy [kJ]`
- `Aero` -> `Aero Energy [kJ]`
- `Accel` -> `Accel Energy [kJ]`
- `Grade` -> `Grade Energy [kJ]`
- `Rst` -> `Restart Count`
- `ON%` -> `Engine ON Ratio [%]`
