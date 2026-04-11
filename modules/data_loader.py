# modules/data_loader.py
# Loads INI and CSV config files.  No external dependencies.

import os

try:
    import ConfigParser as configparser   # Python 2
except ImportError:
    import configparser                    # Python 3


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _app_root():
    """Return the app root directory (parent of modules/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def config_path(filename):
    return os.path.join(_app_root(), "config", filename)


# ---------------------------------------------------------------------------
# INI loader - returns a flat dict with type coercion
# ---------------------------------------------------------------------------

def _coerce(value):
    """Try int -> float -> str."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_ini(filename):
    """
    Load an INI file from config/.
    Returns a flat dict: keys are lower-case 'section.key' and also bare 'key'.
    Comments (lines starting with ; or #) are handled by ConfigParser.
    """
    path = config_path(filename)
    result = {}
    if not os.path.isfile(path):
        return result

    cp = configparser.RawConfigParser()
    cp.read(path)

    for section in cp.sections():
        for key, value in cp.items(section):
            coerced = _coerce(value)
            result[key] = coerced
            result["{0}.{1}".format(section.lower(), key.lower())] = coerced

    return result


# ---------------------------------------------------------------------------
# CSV loader helpers
# ---------------------------------------------------------------------------

def _skip_comment(line):
    s = line.strip()
    return s == "" or s.startswith("#") or s.startswith(";")


def load_csv_2d(filename):
    """
    Load a 2-D BSFC-style CSV.
    Row 0 (after comments): 'rpm', load_0, load_1, ...
    Rows 1+: rpm_val, bsfc_0, bsfc_1, ...

    Returns:
        rpm_axis  : list of float
        load_axis : list of float
        table     : list of list of float  [rpm_idx][load_idx]
    """
    path = config_path(filename)
    rpm_axis  = []
    load_axis = []
    table     = []

    if not os.path.isfile(path):
        return rpm_axis, load_axis, table

    with open(path, "r") as f:
        header_done = False
        for line in f:
            if _skip_comment(line):
                continue
            parts = [p.strip() for p in line.split(",")]
            if not header_done:
                # First non-comment row is header
                load_axis = [float(p) for p in parts[1:]]
                header_done = True
            else:
                if len(parts) < 2:
                    continue
                rpm_axis.append(float(parts[0]))
                table.append([float(p) for p in parts[1:]])

    return rpm_axis, load_axis, table


def load_csv_1d(filename):
    """
    Load a 1-D lookup table CSV.
    Format: x, y  (header row optionally has labels, skipped if non-numeric)

    Returns:
        xs : list of float
        ys : list of float
    """
    path = config_path(filename)
    xs = []
    ys = []

    if not os.path.isfile(path):
        return xs, ys

    with open(path, "r") as f:
        for line in f:
            if _skip_comment(line):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            try:
                xs.append(float(parts[0]))
                ys.append(float(parts[1]))
            except ValueError:
                # Header row with text labels - skip
                continue

    return xs, ys


def load_vehicle_config():
    return load_ini("vehicle.ini")


def load_strategy_config():
    return load_ini("strategy.ini")
