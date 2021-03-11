from enum import Enum, unique

__all__ = ["MouseButton", "MouseState", "MouseEvent"]


@unique
class MouseButton(int, Enum):
    left_button = 1
    middle_button = 2
    right_button = 3
    scroll_wheel_up = 4
    scroll_wheel_down = 5


@unique
class MouseState(int, Enum):
    released = 0
    pressed = 1
    dragging = 2


@unique
class MouseEvent(str, Enum):
    release = "mouse release"
    press = "mouse press"
    drag = "mouse drag"
