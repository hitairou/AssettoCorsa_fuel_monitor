# Config File Formats - ecoran_fuel_monitor

## vehicle.ini

`vehicle.ini` is still a flat INI parsed by `data_loader.load_ini()`.
Representative keys:

```ini
[VEHICLE]
mass_total                = 98.65
crr                       = 0.0025
cd                        = 0.355
frontal_area              = 0.3846
fuel_density_g_per_ml     = 0.778
drivetrain_efficiency     = 0.9
primary_ratio             = 4.058
secondary_ratio           = 2.944
gear_1                    = 3.181
rear_tire_circumference_m = 1.5
rule_time_limit_s         = 2536.70
rule_total_distance_m     = 17616.0
total_laps                = 8
lap_distance_m            = 2202.0
```

## strategy.ini

Representative file:

```ini
[ENGINE]
rpm_on_threshold       = 800
rpm_off_threshold      = 500

[FUEL]
start_penalty_ml       = 0.5

[SMOOTHING]
speed_window           = 5
grade_window           = 5

[TIMING]
update_interval_s      = 0.1

[MEASUREMENT]
measurement_start_mode            = first_cross_sf
ignore_initial_partial_lap        = 1
use_dynamic_8lap_estimate         = 1
min_progress_for_dynamic_estimate = 0.10
min_time_for_dynamic_estimate     = 10.0
gear_display_offset               = -1

[GRADE]
vertical_axis_index    = 1
grade_fallback_mode    = pitch
grade_max_abs          = 0.5
grade_min_ds           = 0.05

[POWER]
power_graph_auto_scale  = 1
power_graph_scale_w     = 800.0
power_graph_min_scale_w = 400.0
power_graph_quantile    = 0.95
power_graph_expand_gain = 0.55
power_graph_shrink_gain = 0.12

[GATE]
minimum_valid_run_time_s        = 30.0
minimum_valid_finish_lap_count  = 1

[UI]
ui.preset              = overview
ui.restore_state       = 1
ui.main.econ_warn_kmpl = 350.0
ui.main.econ_good_kmpl = 550.0
```

## Measurement Keys

### measurement_start_mode

Legacy measurement start mode used when gate-based recording is not active.

Allowed values:

- `session_start`
- `first_cross_sf`
- `manual_arm_then_cross_sf`

When gate-based recording is active, manual / semi-auto gate control takes
priority over this legacy setting.

### ignore_initial_partial_lap

- `1`: do not store the pre-measurement partial lap as a completed row
- `0`: allow the first partial lap to enter lap history

### use_dynamic_8lap_estimate

- `1`: include the provisional lap once enough progress/time exists
- `0`: completed laps only

### min_progress_for_dynamic_estimate

Minimum provisional progress before dynamic 8-lap estimation is allowed.

### min_time_for_dynamic_estimate

Minimum provisional lap time in seconds before dynamic 8-lap estimation is
allowed.

### gear_display_offset

Integer offset applied to raw AC gear for UI display.

## Power Graph Keys

The power window now uses a 20-second history buffer at the existing 10 Hz
update cadence.

### power_graph_auto_scale

- `1`: auto-scale from recent history
- `0`: use fixed `power_graph_scale_w`

### power_graph_scale_w

Fixed half-scale for the power graph and stacked bar when auto-scale is off.

### power_graph_min_scale_w

Lower bound for auto-scale. Recommended range: `300` to `500`.

### power_graph_quantile

Quantile of recent absolute power samples used as the auto-scale target.
Recommended default: `0.95`.

### power_graph_expand_gain

Smoothing gain when the graph must expand quickly to fit new peaks.

### power_graph_shrink_gain

Smoothing gain when the graph shrinks back down more slowly.

## Main HUD Keys

### ui.main.econ_warn_kmpl

Average fuel economy value where Main HUD coloring should lean red/orange.

### ui.main.econ_good_kmpl

Average fuel economy value where Main HUD coloring should lean green.

## Gate / Recording Keys

### minimum_valid_run_time_s

Finish gate guard. The finish gate is ignored until the run has lasted at least
this many seconds, unless `minimum_valid_finish_lap_count` is already satisfied.

### minimum_valid_finish_lap_count

Finish gate guard. The finish gate is allowed once at least this many laps have
been completed, even if `minimum_valid_run_time_s` has not elapsed yet.

## Gate JSON Storage

Gate definitions are stored per track/layout under:

```text
config/gates/<track_key>.json
```

Example:

```json
{
  "version": 1,
  "track_key": "suzuka_east_default",
  "mode_defaults": {
    "record_mode": "manual"
  },
  "gates": {
    "start": {
      "enabled": true,
      "center_world": [123.4, 0.0, -56.7],
      "forward_world": [0.99, 0.0, 0.11],
      "tangent_world": [-0.11, 0.0, 0.99],
      "half_width_m": 4.0,
      "directional": true,
      "cooldown_s": 2.0,
      "min_speed_kmh": 3.0
    }
  }
}
```

### track_key

`track_key` currently uses:

- AC shared-memory `static.track`
- AC shared-memory `static.trackConfiguration`

combined into:

```text
<track>_<layout-or-default>
```

### Auto Save / Auto Restore

- setting a gate auto-saves
- changing width auto-saves
- clearing a gate auto-saves
- `SAVE` triggers an explicit save
- track reload / layout change auto-loads matching gate JSON when available
- invalid or broken JSON is treated as a warning and the app continues safely

## UI State Storage

Window positions, sizes, and visibility are still persisted at:

```text
%LOCALAPPDATA%\ecoran_fuel_monitor\ui_state.json
```
