from functools import wraps
from dataclasses import dataclass, field
from typing import Optional, Callable, List

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
    ("body", "white", "", "standout"),
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
class WrappedButton:
    name: str
    widget: urwid.Button
    key_short_cut: str
    callback: Optional[Callable] = None

    def set_callback(self, on_press: Callable) -> "WrappedButton":
        self.callback = on_press
        urwid.connect_signal(self.widget, "click", self.callback)
        return self


@dataclass
class TopMenu:
    buttons: List[WrappedButton] = field(default_factory=list)
    handler: Optional[urwid.Columns] = None

    def __getattr__(self, item) -> WrappedButton:
        for b in self.buttons:
            if b.name == item:
                return b

    @staticmethod
    def default() -> "TopMenu":
        top_menu = TopMenu()
        for (label, key) in [("Statements Menu", "f2"), ("Filter Menu", "f3"), ("Plot Menu", "f4"),
                             ("Export Menu", "f5"), ("Search", "f6"), ("Go To...", "f7"), ("Done", "f8")]:
            name = "".join([i.lower() for i in label.replace(" ", "_") if i.isalpha() or i == "_"])
            name = f"{name}_button"
            top_menu.buttons.append(WrappedButton(name=name, widget=urwid.Button(label), key_short_cut=key))
        top_menu.handler = urwid.Columns([b.widget for b in top_menu.buttons])
        return top_menu


@dataclass
class BankStatementWizardView:
    main_view: Optional[urwid.Widget] = None

    header: Optional[urwid.Widget] = None

    title_text: Optional[urwid.Widget] = None
    title: Optional[urwid.Widget] = None

    exit_text: Optional[urwid.Widget] = None
    exit_view: Optional[urwid.Widget] = None

    statements_button: Optional[urwid.Widget] = None
    filter_button: Optional[urwid.Widget] = None
    plot_button: Optional[urwid.Widget] = None
    export_button: Optional[urwid.Widget] = None
    search_button: Optional[urwid.Widget] = None
    go_to_button: Optional[urwid.Widget] = None
    done_button: Optional[urwid.Widget] = None
    menu: Optional[TopMenu] = None

    def setup(self,
              statements_button_callback: Callable,
              filter_button_callback: Callable,
              plot_button_callback: Callable,
              export_button_callback: Callable,
              search_button_callback: Callable,
              go_to_button_callback: Callable,
              done_button_callback: Callable):
        big_font = urwid.font.HalfBlock5x4Font()

        self.title_text = urwid.BigText("Bank Statement Wizard", big_font)
        self.title = SwitchingPadding(self.title_text, "center", None)
        self.title = urwid.Filler(self.title, "middle")
        self.title = urwid.BoxAdapter(self.title, 7)
        self.title = urwid.AttrMap(self.title, "title")

        self.header = urwid.Text("Press ESC to exit")
        self.header = urwid.AttrWrap(self.header, "header")

        self.menu = TopMenu.default()
        self.menu.statements_menu_button.set_callback(statements_button_callback)
        self.menu.filter_menu_button.set_callback(filter_button_callback)
        self.menu.plot_menu_button.set_callback(plot_button_callback)
        self.menu.export_menu_button.set_callback(export_button_callback)
        self.menu.search_button.set_callback(search_button_callback)
        self.menu.go_to_button.set_callback(go_to_button_callback)
        self.menu.done_button.set_callback(done_button_callback)
        self.menu.handler = urwid.AttrMap(self.menu.handler, "button normal")

        self.set_to_default_view()

        self.exit_text = urwid.BigText(("exit", " Quit? [ESC to cancel] "), big_font)
        self.exit_view = urwid.Overlay(self.exit_text, self.main_view, "center", None, "middle", None)

    def set_frame(self):
        self.main_view = urwid.Frame(header=self.header, body=self.main_view)
        self.main_view = urwid.AttrWrap(self.main_view, "body")

    def set_to_default_view(self):
        self.main_view = urwid.ListBox(urwid.SimpleListWalker([self.title, self.menu.handler]))
        self.set_frame()

    def set_to_statements_menu(self):
        _text = urwid.Text("Statements Options")
        self.main_view = urwid.ListBox(urwid.SimpleListWalker([self.title, self.menu.handler, _text]))
        self.set_frame()

    def set_to_filter_menu(self):
        _text = urwid.Text("Filter Options")
        self.main_view = urwid.ListBox(urwid.SimpleListWalker([self.title, self.menu.handler, _text]))
        self.set_frame()

    def set_to_plot_menu(self):
        _text = urwid.Text("Plot Options")
        self.main_view = urwid.ListBox(urwid.SimpleListWalker([self.title, self.menu.handler, _text]))
        self.set_frame()


def _update_loop_widget(f):
    @wraps(f)
    def _wrapped(instance: "BankStatementWizardApp", *args, **kwargs):
        f(instance, *args, **kwargs)
        instance._loop.widget = instance._view.main_view
    return _wrapped


class BankStatementWizardApp:
    def __init__(self):
        self._view = BankStatementWizardView()
        self._view.setup(
            self._statements_button_callback,
            self._filter_button_callback,
            self._plot_button_callback,
            self._export_button_callback,
            self._search_button_callback,
            self._go_to_button_callback,
            self._done_button_callback
        )
        self._loop = urwid.MainLoop(self._view.main_view, PALETTE, unhandled_input=self._unhandled_input)
        self._is_quitting: bool = False

    @_update_loop_widget
    def _statements_button_callback(self, widget: urwid.Widget):
        self._view.set_to_statements_menu()

    @_update_loop_widget
    def _filter_button_callback(self, widget: urwid.Widget):
        self._view.set_to_filter_menu()

    @_update_loop_widget
    def _plot_button_callback(self,  _):
        self._view.set_to_plot_menu()

    @_update_loop_widget
    def _export_button_callback(self, widget: urwid.Widget):
        pass

    @_update_loop_widget
    def _search_button_callback(self, widget: urwid.Widget):
        pass

    @_update_loop_widget
    def _go_to_button_callback(self, widget: urwid.Widget):
        pass

    @_update_loop_widget
    def _done_button_callback(self, widget: urwid.Widget):
        self._view.set_to_default_view()

    def _unhandled_input(self, key):
        if self._is_quitting:
            if key == "enter":
                raise urwid.ExitMainLoop()
            if key == "esc":
                self._is_quitting = False
                self._loop.widget = self._view.main_view
                return True
        else:
            if key == "esc":
                self._is_quitting = True
                self._loop.widget = self._view.exit_view
                return True

        for button in self._view.menu.buttons:
            if key == button.key_short_cut:
                button.callback(button.widget)

    def run(self):
        self._loop.run()


def run_ui():
    BankStatementWizardApp().run()
