from dataclasses import dataclass
from typing import Callable, Optional, Dict

import urwid

__all__ = ["SwitchingPadding", "TopMenuButton", "PopUpMixin", "PopUpWrapper", "create_overlay",
           "create_box", "create_line_box", "BIG_TEXT_FONT"]


BIG_TEXT_FONT = urwid.font.HalfBlock5x4Font()


class SwitchingPadding(urwid.Padding):
    def padding_values(self, size, focus):
        max_columns = size[0]
        width, ignore = self.original_widget.pack(size, focus=focus)
        self.align = "left" if max_columns > width else "right"
        return urwid.Padding.padding_values(self, size, focus)


@dataclass
class TopMenuButton:
    widget: urwid.Widget
    key_short_cut: str

    def __getattr__(self, name) -> urwid.Widget:
        w = self.widget
        while True:
            if isinstance(w, urwid.PopUpLauncher) and name == "pop_up_launcher":
                break
            if isinstance(w, urwid.Button) and name == "button":
                break
            if hasattr(w, "original_widget"):
                w = w.original_widget
            else:
                raise ValueError(f"Cannot get {name} attribute for {self.__class__.__name__}")
        return w

    def set_pop_up_callback(self, callback: Callable) -> "TopMenuButton":
        urwid.connect_signal(self.button, "click", lambda w: self.pop_up_launcher.open_pop_up())
        self.pop_up_launcher.callback = callback
        return self

    def set_button_callback(self, callback: Callable) -> "TopMenuButton":
        urwid.connect_signal(self.button, "click", callback)
        return self

    def activate(self):
        self.button.mouse_event(None, "mouse press", 1, 4, 0, True)

    @staticmethod
    def from_label_and_key(label: str, key: str) -> "TopMenuButton":
        label = f"{label} ({key.title()})"
        button = urwid.Button(label)
        button = urwid.AttrMap(button, "button normal", "button select")
        return TopMenuButton(widget=button, key_short_cut=key)


class PopUpMixin:
    def attach(self, launcher: urwid.PopUpLauncher):
        urwid.connect_signal(self, 'close', lambda button: launcher.close_pop_up())

    def launch(self, launcher: urwid.PopUpLauncher):
        self.attach(launcher)
        return self


class PopUpWrapper(urwid.PopUpLauncher):
    def __init__(self, parent):
        super().__init__(parent)
        self.callback: Optional[Callable[["PopUpWrapper"], urwid.Widget]] = None
        self.parameters: Dict = {'left': 0, 'top': 1, 'overlay_width': 32, 'overlay_height': 7}

    def create_pop_up(self):
        if not self.callback:
            raise ValueError(f"Pop up wrapped was not set")
        return self.callback(self)

    def get_pop_up_parameters(self):
        return self.parameters


def create_line_box(*widgets) -> urwid.LineBox:
    body = list(widgets)
    return urwid.LineBox(urwid.ListBox(urwid.SimpleFocusListWalker(body)))


def create_box(*widgets) -> urwid.Filler:
    body = list(widgets)
    return urwid.Filler(urwid.Pile(body))


def create_overlay(widget: urwid.Widget, background: str = " ", **kwargs):
    _kwargs = dict(align="center", width=("relative", 80), valign="middle",
                   height=("relative", 80), min_width=24, min_height=8)
    _kwargs.update(kwargs)
    return urwid.Overlay(widget, urwid.SolidFill(background), **_kwargs)