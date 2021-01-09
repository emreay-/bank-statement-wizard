import os
import curses
from typing import Optional
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


@unique
class ColorPair(IntEnum):
    title = 1
    subtitle = 2
    header = 3
    footer = 4
    regular = 5


@contextmanager
def attributes(*attr, window: curses.window):
    for _attr in attr:
        window.attron(_attr)
    try:
        yield True
    finally:
        for _attr in attr:
            window.attroff(_attr)


class MainMenu:
    def __init__(self):
        self._main_window: Optional[curses.window] = None
        self._title = "Bank Statement Wizard"
        self._subtitle = "Developed by Emre Ay"
        self._header = "Press ESC to exit"
        self._footer = "INFO: "
        self._key_stroked = 0
        self._exit_key = 27

    def _clear(self):
        self._main_window.clear()
        self._main_window.refresh()

    def _initialize_colors(self):
        curses.init_pair(ColorPair.title, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.subtitle, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.header, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.footer, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.regular, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def _set_info(self, width: int):
        self._title_str = self._title[:width-1]
        self._subtitle_str = self._subtitle[:width-1]
        self._header_str = self._header[:width-1]
        self._footer_str = self._footer[:width-1]

    def _render(self, width: int, height: int):
        self._main_window.addstr(0, 0, self._header_str, curses.color_pair(ColorPair.header))

        # Render status bar
        with attributes(curses.color_pair(ColorPair.footer), window=self._main_window):
            self._main_window.addstr(height - 1, 0, self._footer_str)
            self._main_window.addstr(height - 1, len(self._footer_str), " " * (width - len(self._footer_str) - 1))

        with attributes(curses.color_pair(ColorPair.title), curses.A_BOLD, window=self._main_window):
            title_y = adjust_height_relative(height, 0.5)
            title_x = adjust_width_relative(self._title_str, width, 0.5)
            self._main_window.addstr(title_y, title_x, self._title_str)

        sub_title_y = title_y + 1
        sub_title_x = adjust_width_relative(self._subtitle_str, width, 0.5)
        self._main_window.addstr(sub_title_y, sub_title_x, self._subtitle_str)

    def __call__(self, main_window: curses.window, *args, **kwargs):
        self._main_window = main_window

        self._clear()
        self._initialize_colors()

        while self._key_stroked != self._exit_key:
            self._main_window.clear()
            height, width = self._main_window.getmaxyx()

            self._set_info(width)
            self._render(width, height)
            main_window.refresh()
            self._key_stroked = main_window.getch()


def run_ui():
    set_escape_delay()
    main_menu = MainMenu()
    curses.wrapper(main_menu)
