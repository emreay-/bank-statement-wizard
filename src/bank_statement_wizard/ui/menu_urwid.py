from dataclasses import dataclass
from typing import Optional

import urwid
import urwid.raw_display


__all__ = ["run_ui"]


class SwitchingPadding(urwid.Padding):
    def padding_values(self, size, focus):
        max_columns = size[0]
        width, ignore = self.original_widget.pack(size, focus=focus)
        self.align = "left" if max_columns > width else "right"
        return urwid.Padding.padding_values(self, size, focus)


PALETTE = [
    ("body", "white", "dark gray", "standout"),
    ("header", "white", "dark red", "bold"),
    ("button normal", "light gray", "dark blue", "standout"),
    ("button select", "white", "dark green"),
    ("button disabled", "dark gray", "dark blue"),
    ("edit", "light gray", "dark blue"),
    ("title", "white", "black"),
    ("chars", "light gray", "black"),
    ("exit", "white", "dark blue")
]


@dataclass
class BankStatementWizardView:
    main_view: Optional[urwid.Widget] = None
    exit_view: Optional[urwid.Widget] = None

    title: Optional[urwid.Widget] = None
    header: Optional[urwid.Widget] = None
    exit_text: Optional[urwid.Widget] = None

    add_statement_button: Optional[urwid.Widget] = None
    filter_button: Optional[urwid.Widget] = None
    plot_button: Optional[urwid.Widget] = None
    export_button: Optional[urwid.Widget] = None
    search_button: Optional[urwid.Widget] = None
    go_to_button: Optional[urwid.Widget] = None
    menu: Optional[urwid.Widget] = None

    def setup(self):
        big_font = urwid.font.HalfBlock5x4Font()

        self.title = urwid.BigText("Bank Statement Wizard", big_font)

        self.header = urwid.Text("Press ESC to exit")
        self.header = urwid.AttrWrap(self.header, "header")

        self.add_statement_button = urwid.Button(label="Add Statement")
        self.filter_button = urwid.Button(label="Filter Menu")
        self.plot_button = urwid.Button(label="Plot Menu")
        self.export_button = urwid.Button(label="Export Menu")
        self.search_button = urwid.Button(label="Search")
        self.go_to_button = urwid.Button(label="Go To...")

        self.menu = urwid.Columns([
            self.add_statement_button,
            self.filter_button,
            self.plot_button,
            self.export_button,
            self.search_button,
            self.go_to_button,
        ])
        self.menu = urwid.AttrMap(self.menu, "button normal")

        self.main_view = SwitchingPadding(self.title, "center", None)
        self.main_view = urwid.Filler(self.main_view, "middle")
        self.main_view = urwid.BoxAdapter(self.main_view, 7)
        self.main_view = urwid.AttrMap(self.main_view, "title")
        self.main_view = urwid.ListBox(urwid.SimpleListWalker([self.main_view, self.menu]))
        self.main_view = urwid.Frame(header=self.header, body=self.main_view)
        self.main_view = urwid.AttrWrap(self.main_view, "body")

        self.exit_text = urwid.BigText(("exit", " Quit? [Y or N] "), big_font)
        self.exit_view = urwid.Overlay(self.exit_text, self.main_view, "center", None, "middle", None)


class BankStatementWizardApp:
    def __init__(self):
        self._view = BankStatementWizardView()
        self._view.setup()
        self._loop = urwid.MainLoop(self._view.main_view, PALETTE, unhandled_input=self._unhandled_input)

    def _unhandled_input(self, key):
        if key == "esc":
            self._loop.widget = self._view.exit_view
            return True
        if self._loop.widget != self._view.exit_view:
            return
        if key.lower() == "y":
            raise urwid.ExitMainLoop()
        elif key.lower() == "n":
            self._loop.widget = self._view.main_view
            return True

    def run(self):
        self._loop.run()


def run_ui():
    BankStatementWizardApp().run()
