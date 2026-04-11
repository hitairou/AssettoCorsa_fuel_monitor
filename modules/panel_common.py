# modules/panel_common.py
# Shared helpers for AC label/button creation.

try:
    import ac
except ImportError:
    class _AcStub(object):
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return 0
            return _noop

    ac = _AcStub()


def safe_call(func, *args):
    try:
        return func(*args)
    except Exception:
        return None


def add_label(window_id, text, x, y, width, height=16, font_size=12,
              align="left", color=(1.0, 1.0, 1.0, 1.0)):
    label = ac.addLabel(window_id, text)
    safe_call(ac.setPosition, label, x, y)
    safe_call(ac.setSize, label, width, height)
    safe_call(ac.setFontSize, label, font_size)
    safe_call(ac.setFontAlignment, label, align)
    safe_call(ac.setFontColor, label, color[0], color[1], color[2], color[3])
    return label


def add_button(window_id, text, x, y, width, height=20, font_size=11,
               callback=None):
    button = ac.addButton(window_id, text)
    safe_call(ac.setPosition, button, x, y)
    safe_call(ac.setSize, button, width, height)
    safe_call(ac.setFontSize, button, font_size)
    safe_call(ac.setBackgroundOpacity, button, 0.5)
    safe_call(ac.setBackgroundColor, button, 0.15, 0.15, 0.15)
    if callback is not None:
        safe_call(ac.addOnClickedListener, button, callback)
    return button


def set_text(ctrl_id, text):
    safe_call(ac.setText, ctrl_id, str(text))


def set_color(ctrl_id, color):
    safe_call(ac.setFontColor, ctrl_id, color[0], color[1], color[2], color[3])


def set_visible(ctrl_id, visible):
    safe_call(ac.setVisible, ctrl_id, 1 if visible else 0)


def set_button_state(button_id, active,
                     active_color=(0.18, 0.50, 0.18),
                     inactive_color=(0.16, 0.16, 0.16)):
    color = active_color if active else inactive_color
    safe_call(ac.setBackgroundColor, button_id, color[0], color[1], color[2])
    safe_call(ac.setBackgroundOpacity, button_id, 0.75 if active else 0.45)


def move(ctrl_id, x, y, width=None, height=None):
    safe_call(ac.setPosition, ctrl_id, x, y)
    if width is not None and height is not None:
        safe_call(ac.setSize, ctrl_id, width, height)
