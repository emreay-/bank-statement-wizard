import os
import curses
from typing import Optional
from enum import IntEnum, unique
from contextlib import contextmanager


__all__ = ["run_ui"]


def set_escape_delay(delay: int = 25):
    os.environ.setdefault("ESCDELAY", str(delay))


def adjust_width_center(text: str, width: int) -> int:
    return int((width // 2) - (len(text) // 2) - len(text) % 2)


def adjust_height_center(height: int) -> int:
    return int((height // 2) - 2)


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
        self._footer = ""
        self._key_stroked = 0
        self._exit_key = 27

    def _clear(self):
        self._main_window.clear()
        self._main_window.refresh()

    def _initialize_colors(self):
        curses.init_pair(ColorPair.title, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.subtitle, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.header, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.footer, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.regular, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def _set_info(self, width: int):
        self._title_str = self._title[:width-1]
        self._subtitle_str = self._subtitle[:width-1]
        self._header_str = self._header[:width-1]
        self._footer_str = self._footer[:width-1]

    def _render(self, width: int, height: int):
        center_y = adjust_height_center(height)

        self._main_window.addstr(0, 0, self._header_str, curses.color_pair(ColorPair.header))

        # Render status bar
        with attributes(curses.color_pair(ColorPair.footer), window=self._main_window):
            self._main_window.addstr(height - 1, 0, self._footer_str)
            self._main_window.addstr(height - 1, len(self._footer_str), " " * (width - len(self._footer_str) - 1))

        with attributes(curses.color_pair(ColorPair.title), curses.A_BOLD, window=self._main_window):
            self._main_window.addstr(center_y, adjust_width_center(self._title_str, width), self._title_str)

        self._main_window.addstr(center_y + 1, adjust_width_center(self._subtitle_str, width), self._subtitle_str)

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
