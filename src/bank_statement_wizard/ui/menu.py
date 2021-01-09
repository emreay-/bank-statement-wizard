import os
import curses
from dataclasses import dataclass, field
from typing import Optional, List
from enum import IntEnum, unique
from contextlib import contextmanager


__all__ = ["run_ui"]


def set_escape_delay(delay: int = 25):
    os.environ.setdefault("ESCDELAY", str(delay))


def get_usable_height(height: int) -> int:
    return height - 3


def limit_height(height_value: int, current_height: int) -> int:
    return max(min(height_value, get_usable_height(current_height)), 1)


def adjust_width_relative(text: str, width: int, relativity: float) -> int:
    return int(width * relativity) - (len(text) // 2)


def adjust_height_relative(height: int, relativity: float) -> int:
    usable_height = get_usable_height(height)
    return limit_height(int(usable_height * relativity), height)


@contextmanager
def attributes(*attr, window: curses.window):
    for _attr in attr:
        window.attron(_attr)
    try:
        yield True
    finally:
        for _attr in attr:
            window.attroff(_attr)


@unique
class ColorPair(IntEnum):
    title = 1
    subtitle = 2
    header = 3
    footer = 4
    regular = 5
    selected = 6


@dataclass
class MainMenuModel:
    output_directory: Optional[str] = None
    statements: List[str] = field(default_factory=list)


@dataclass
class MainMenuView:
    title: str = ""
    subtitle: str = ""
    header: str = ""
    footer: str = ""
    buttons: List[str] = field(default_factory=list)

    _vertical_index: int = 0
    _current_height: int = 0
    _current_width: int = 0

    @staticmethod
    def initialize_colors():
        curses.init_pair(ColorPair.title, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.subtitle, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.header, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.footer, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.regular, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.selected, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def reset_data(self):
        self.title = "Bank Statement Wizard"
        self.subtitle = "Developed by Emre Ay"
        self.header = "Press ESC to exit"
        self.footer = "INFO: "
        self.buttons = ["Add Statement", "Select Output Directory"]

    def _render_line(self, window: curses.window, text: str, relativity_x: float, relativity_y: float):
        if self._vertical_index == 0:
            self._vertical_index += adjust_height_relative(self._current_height, relativity_y)

        _x = adjust_width_relative(text, self._current_width, relativity_x)
        window.addstr(self._vertical_index, _x, text)
        self._vertical_index += len(text.splitlines())

    def render(self, window: curses.window, width: int, height: int, selected_vertical_element: int):
        window.addstr(0, 0, self.header, curses.color_pair(ColorPair.header))

        with attributes(curses.color_pair(ColorPair.footer), window=window):
            window.addstr(height - 1, 0, self.footer)

        self._vertical_index = 0
        self._current_height = height
        self._current_width = width

        with attributes(curses.color_pair(ColorPair.title), curses.A_BOLD, window=window):
            self._render_line(window, self.title, relativity_x=0.5, relativity_y=0.1)

        self._render_line(window, self.subtitle, relativity_x=0.5, relativity_y=0.1)
        self._render_line(window, "\n", relativity_x=0.5, relativity_y=0.1)
        self._render_line(window, "=" * int(width * 0.3), relativity_x=0.5, relativity_y=0.1)
        self._render_line(window, "\n", relativity_x=0.5, relativity_y=0.1)

        for i, button in enumerate(self.buttons):
            attr = curses.color_pair(ColorPair.selected) if i == selected_vertical_element \
                else curses.color_pair(ColorPair.regular)

            with attributes(attr, window=window):
                self._render_line(window, button, relativity_x=0.5, relativity_y=0.1)

class MainMenu:
    def __init__(self):
        self._model = MainMenuModel()
        self._view = MainMenuView()
        self._main_window: Optional[curses.window] = None
        self._key_stroked: int = 0
        self._exit_key: int = 27
        self._selected_vertical_element: int = 0
        self._number_of_vertical_elements: int = 2

    def _clear(self):
        self._main_window.clear()
        self._main_window.refresh()

    def _set_info(self, width: int):
        self._view.title = self._view.title[:width-1]
        self._view.subtitle = self._view.subtitle[:width-1]
        self._view.header = self._view.header[:width-1]
        self._view.footer = self._view.footer[:width-1]

    def _handle_key_stroke(self):
        curses.curs_set(False)

        if self._key_stroked == curses.KEY_UP:
            self._selected_vertical_element -= 1
        elif self._key_stroked == curses.KEY_DOWN:
            self._selected_vertical_element += 1
        self._selected_vertical_element %= self._number_of_vertical_elements

    def __call__(self, window: curses.window, *args, **kwargs):
        self._main_window = window

        self._clear()
        self._view.initialize_colors()

        while self._key_stroked != self._exit_key:
            self._view.reset_data()
            self._main_window.clear()
            height, width = self._main_window.getmaxyx()

            self._handle_key_stroke()
            self._set_info(width)
            self._view.render(self._main_window, width, height, self._selected_vertical_element)

            self._main_window.refresh()
            self._key_stroked = self._main_window.getch()


def run_ui():
    set_escape_delay()
    main_menu = MainMenu()
    curses.wrapper(main_menu)
