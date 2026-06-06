# BSFC Map Notes

The current BSFC map is not measured BSFC data for the actual engine.

The high-load and peak-power region is anchored from a thermal-efficiency estimate:

- BSFC[g/kWh] = 3600 / (eta * 43.0), using gasoline lower heating value 43.0 MJ/kg.
- eta = 29.6% gives approximately 283 g/kWh.
- eta = 28.7% gives approximately 292 g/kWh.
- Therefore high-load and peak-power cells are set around 280-310 g/kWh.

The low-load, low-rpm, and over-rev high-rpm regions are intentionally worsened
according to the general BSFC-map shape rather than direct measurement.
