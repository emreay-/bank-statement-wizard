from typing import Optional, Callable

from urwid_utils.palette import *
import urwid

from .logger import get_logger
from .user_input import MouseButton, MouseState, MouseEvent

logger = get_logger()


__all__ = ["ScrollingListBox"]


class ListBoxScrollBar(urwid.WidgetWrap):
    def __init__(self, parent):
        self.parent = parent
        self.pile = urwid.Pile([])
        super(ListBoxScrollBar, self).__init__(self.pile)

    def update(self, size):
        width, height = size
        scroll_marker_height = 1
        del self.pile.contents[:]

        if (len(self.parent.body) and self.parent.row_count and
                self.parent.focus is not None and self.parent.row_count > height):
            scroll_position = int(self.parent.focus_position / self.parent.row_count * height)
            scroll_marker_height = max(height * (height / self.parent.row_count), 1)
        else:
            scroll_position = -1

        pos_marker = urwid.AttrMap(urwid.Text(" "), {None: "scroll_pos"})
        down_marker = urwid.AttrMap(urwid.Text(u"\N{DOWNWARDS ARROW}"), {None: "scroll_marker"})
        begin_marker = urwid.AttrMap(urwid.Text(u"\N{CIRCLED MINUS}"), {None: "scroll_marker"})
        end_marker = urwid.AttrMap(urwid.Text(u"\N{CIRCLED PLUS}"), {None: "scroll_marker"})
        view_marker = urwid.AttrMap(urwid.Text(" "), {None: "scroll_view"})
        bg_marker = urwid.AttrMap(urwid.Text(" "), {None: "scroll_bg"})

        for i in range(height):
            if abs(i - scroll_position) <= scroll_marker_height // 2:
                if i == 0 and self.parent.focus_position == 0:
                    marker = begin_marker
                elif i + 1 == height and self.parent.row_count == self.parent.focus_position+1:
                    marker = end_marker
                elif len(self.parent.body) == self.parent.focus_position + 1 \
                        and i == scroll_position + scroll_marker_height // 2:
                    marker = down_marker
                else:
                    marker = pos_marker
            else:
                if i < scroll_position:
                    marker = view_marker
                elif self.parent.row_count and i / height < (len(self.parent.body) / self.parent.row_count):
                    marker = view_marker
                else:
                    marker = bg_marker

            self.pile.contents.append((urwid.Filler(marker), self.pile.options("weight", 1)))

        self._invalidate()

    def selectable(self):
        # FIXME: mouse click/drag
        return False


class ScrollingListBox(urwid.WidgetWrap):
    signals = ["select", "drag_start", "drag_continue", "drag_stop", "load_more"]
    SCROLL_WHEEL_HEIGHT_RATIO = 0.5

    def __init__(self, body: urwid.Widget,
                 infinite: bool = False,
                 with_scrollbar: bool = False,
                 row_count_fn: Optional[Callable] = None):
        self.infinite = infinite
        self.with_scrollbar = with_scrollbar
        self.row_count_fn = row_count_fn

        self.mouse_state: MouseState = MouseState.released
        self.drag_from = None
        self.drag_last = None
        self.drag_to = None
        self.load_more = False
        self.width: int = 0
        self.height: int = 0
        self.page: int = 0

        self.queued_keypress = None

        self.listbox = urwid.ListBox(body)
        self.columns = urwid.Columns([('weight', 1, self.listbox)])

        if self.with_scrollbar:
            self.scroll_bar = ListBoxScrollBar(self)
            self.columns.contents.append((self.scroll_bar, self.columns.options("given", 1)))

        super(ScrollingListBox, self).__init__(self.columns)

    def mouse_event(self, size, event: str, button: int, col: int, row: int, focus: bool):
        if row < 0 or row >= self.height:
            return

        if event == MouseEvent.press:
            if button == MouseButton.left_button:
                self.mouse_state = MouseState.pressed
                self.drag_from = self.drag_last = (col, row)

            elif button == MouseButton.scroll_wheel_up:
                pos = self.listbox.focus_position - int(self.height * self.SCROLL_WHEEL_HEIGHT_RATIO)
                if pos < 0:
                    pos = 0
                self.listbox.focus_position = pos
                self.listbox.make_cursor_visible(size)
                self._invalidate()

            elif button == MouseButton.scroll_wheel_down:
                pos = self.listbox.focus_position + int(self.height * self.SCROLL_WHEEL_HEIGHT_RATIO)
                if pos > len(self.listbox.body) - 1:
                    if self.infinite:
                        self.load_more = True
                    pos = len(self.listbox.body) - 1
                self.listbox.focus_position = pos
                self.listbox.make_cursor_visible(size)
                self._invalidate()

        elif event == MouseEvent.drag:
            if self.drag_from is None:
                return

            if button == MouseButton.left_button:
                self.drag_to = (col, row)
                if self.mouse_state == MouseState.pressed:
                    self.mouse_state = MouseState.dragging
                    urwid.signals.emit_signal(self, "drag_start", self, self.drag_from)
                else:
                    urwid.signals.emit_signal(self, "drag_continue", self, self.drag_last, self.drag_to)

            self.drag_last = (col, row)

        elif event == MouseEvent.release:
            if self.mouse_state == MouseState.dragging:
                self.drag_to = (col, row)
                urwid.signals.emit_signal(self, "drag_stop", self, self.drag_from, self.drag_to)
            self.mouse_state = MouseState.released

        return super(ScrollingListBox, self).mouse_event(size, event, button, col, row, focus)

    def keypress(self, size, key: str):
        command = self._command_map[key]
        if not command:
            return super(ScrollingListBox, self).keypress(size, key)

        # down, page down at end trigger load of more data
        if (
                command in ["cursor down", "cursor page down"]
                and self.infinite
                and (
                    not len(self.body)
                    or self.focus_position == len(self.body) - 1)
        ):
            self.load_more = True
            self.queued_keypress = key
            self._invalidate()

        elif command == "activate":
            urwid.signals.emit_signal(self, "select", self, self.selection)

        return super(ScrollingListBox, self).keypress(size, key)

    @property
    def selection(self):
        if len(self.body):
            return self.body[self.focus_position]

    def render(self, size, focus: bool = False):
        max_column: int = size[0]
        max_row: Optional[int] = size[1] if len(size) > 1 else None

        self.width = max_column
        if max_row:
            self.height = max_row

        if self.load_more and len(self.body) == 0 or "bottom" in self.ends_visible((max_column, max_row)):
            self.load_more = False
            self.page += 1
            try:
                focus = self.focus_position
            except IndexError:
                focus = None

            urwid.signals.emit_signal(self, "load_more", focus)

            if self.queued_keypress and focus and focus < len(self.body):
                self.keypress(size, self.queued_keypress)
            self.queued_keypress = None

        if self.with_scrollbar and len(self.body):
            self.scroll_bar.update(size)

        return super(ScrollingListBox, self).render(size, focus)

    def disable(self):
        self._selectable = False

    def enable(self):
        self._selectable = True

    @property
    def contents(self):
        return self.columns.contents

    @property
    def focus(self):
        return self.listbox.focus

    @property
    def focus_position(self):
        if not len(self.listbox.body):
            raise IndexError
        if len(self.listbox.body):
            return self.listbox.focus_position
        return None

    @focus_position.setter
    def focus_position(self, value):
        if not len(self.body):
            return
        self.listbox.focus_position = value
        self.listbox._invalidate()

    @property
    def row_count(self):
        if self.row_count_fn:
            return self.row_count_fn()
        return len(self.body)

    def __getattr__(self, attr):
        if attr in ["ends_visible", "focus_position", "set_focus", "set_focus_valign", "body", "focus"]:
            return getattr(self.listbox, attr)
        raise AttributeError(attr)

    @classmethod
    def get_palette_entries(cls):
        return {
            "scroll_pos": PaletteEntry(
                mono="white",
                foreground="black",
                background="white",
                foreground_high="black",
                background_high="white"
            ),
            "scroll_marker": PaletteEntry(
                mono="white,bold",
                foreground="black,bold",
                background="white",
                foreground_high="black,bold",
                background_high="white"
            ),
            "scroll_view": PaletteEntry(
                mono="black",
                foreground="black",
                background="light gray",
                foreground_high="black",
                background_high="g50"
            ),
            "scroll_bg": PaletteEntry(
                mono="black",
                foreground="light gray",
                background="dark gray",
                foreground_high="light gray",
                background_high="g23"
            ),

        }
