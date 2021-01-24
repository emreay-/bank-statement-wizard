import re
import os
import itertools
from typing import Union, Tuple, List, Optional, Hashable, cast, Callable

import urwid

__all__ = ["FileSelector"]


INITIAL_TOP_LEVEL: List[str] = []
CALLBACK: Callable[[str], None] = lambda _: None


class _TreeSelector(urwid.TreeWidget):
    unexpanded_icon = urwid.TreeWidget.unexpanded_icon
    expanded_icon = urwid.TreeWidget.expanded_icon

    def __init__(self, node):
        super().__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()

    def selectable(self):
        return True

    def keypress(self, size, key):
        key = super(_TreeSelector, self).keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
        return key

    def unhandled_keys(self, size, key):
        return key

    def update_w(self):
        if self.flagged:
            self._w.attr = "flagged"
            self._w.focus_attr = "flagged focus"
        else:
            self._w.attr = "body"
            self._w.focus_attr = "focus"


class _EmptySelector(urwid.TreeWidget):
    def get_display_text(self):
        return "flag", "(empty directory)"


class _EmptyNode(urwid.TreeNode):
    def load_widget(self):
        return _EmptySelector(self)


class _ErrorSelector(urwid.TreeWidget):
    def get_display_text(self):
        return "error", "(error / permission denied)"


class _ErrorNode(urwid.TreeNode):
    def load_widget(self):
        return _ErrorSelector(self)


class _FileSelector(_TreeSelector):
    def __init__(self, node):
        super().__init__(node)

    def get_display_text(self):
        return self.get_node().get_key()

    def unhandled_keys(self, size, key):
        if key == "enter":
            CALLBACK(self.get_node().get_value())
        return key


class _FileNode(urwid.TreeNode):
    def __init__(self, path, parent=None):
        depth = path.count(os.path.sep)
        key = os.path.basename(path)
        urwid.TreeNode.__init__(self, path, key=key, parent=parent, depth=depth)

    def load_parent(self):
        parent = _DirectoryNode(os.path.split(self.get_value())[0])
        parent.set_child_node(self.get_key(), self)
        return parent

    def load_widget(self):
        return _FileSelector(self)


class _DirectorySelector(_TreeSelector):
    def __init__(self, node):
        super().__init__(node)
        path = node.get_value()
        self.expanded = starts_expanded(path)
        self.update_expanded_icon()

    def get_display_text(self):
        node = self.get_node()
        if node.get_depth() == 0:
            return "/"
        else:
            return node.get_key()


class _DirectoryNode(urwid.ParentNode):
    def __init__(self, path, parent=None):
        if path == os.path.sep:
            depth = 0
            key = None
        else:
            depth = path.count(os.path.sep)
            key = os.path.basename(path)

        urwid.ParentNode.__init__(self, path, key=key, parent=parent, depth=depth)
        self._subdirectory_count = 0

    def load_parent(self) -> "_DirectoryNode":
        parent = _DirectoryNode(os.path.split(self.get_value())[0])
        parent.set_child_node(self.get_key(), self)
        return parent

    def load_child_keys(self) -> List[Optional[Hashable]]:
        try:
            directory_names, file_names = get_directory_and_file_names_under_top_level(self.get_value())
        except OSError:
            self._children[None] = _ErrorNode(self, parent=self, key=None, depth=self.get_depth() + 1)
            return [None]

        directory_names.sort(key=alphabetize)
        file_names.sort(key=alphabetize)

        self._subdirectory_count = len(directory_names)
        keys = directory_names + file_names

        if len(keys) == 0:
            self._children[None] = _EmptyNode(self, parent=self, key=None, depth=self.get_depth() + 1)
            keys = [None]

        return keys

    def load_child_node(self, key: Hashable) -> Union[_EmptyNode, _FileNode, "_DirectoryNode"]:
        index = self.get_child_index(key)

        if key is None:
            return _EmptyNode(None)
        else:
            path = os.path.join(self.get_value(), cast(str, key))
            if index < self._subdirectory_count:
                return _DirectoryNode(path, parent=self)
            else:
                return _FileNode(path, parent=self)

    def load_widget(self):
        return _DirectorySelector(self)


class FileSelector:
    footer_text = [
        ("title", "Directory Browser"),
        "    ",
        ("key", "UP"),
        ", ",
        ("key", "DOWN"),
        ", ",
        ("key", "PAGE UP"),
        ", ",
        ("key", "PAGE DOWN"),
        ", ",
        ("key", "+"),
        ", ",
        ("key", "-"),
        ", ",
        ("key", "LEFT"),
        ", ",
        ("key", "HOME"),
        ", ",
        ("key", "END"),
        ", ",
        ("key", "ENTER"),
    ]

    def __init__(self, on_selected: Callable[[str], None]):
        working_directory = os.getcwd()
        set_initial_top_level(working_directory)
        set_callback(on_selected)

        self.body = urwid.TreeListBox(urwid.TreeWalker(_DirectoryNode(working_directory)))
        self.body.offset_rows = 1
        self.footer = urwid.Text(self.footer_text)
        self.view = urwid.Frame(urwid.AttrWrap(self.body, "body"), footer=urwid.AttrWrap(self.footer, "footer"))


def set_initial_top_level(path: str):
    global INITIAL_TOP_LEVEL
    INITIAL_TOP_LEVEL += path.split(os.path.sep)


def set_callback(cb: Callable[[str], None]):
    global CALLBACK
    CALLBACK = cb


def starts_expanded(path: str):
    if path == "/":
        return True

    i = path.split(os.path.sep)
    if len(i) > len(INITIAL_TOP_LEVEL):
        return False

    if i != INITIAL_TOP_LEVEL[: len(i)]:
        return False

    return True


def handle_file_name_for_shell(name):
    """Return a hopefully safe shell-escaped version of a filename."""

    # Replace unprintable chars with ansi-c versions
    for ch in name:
        if ord(ch) < 32:
            return handle_file_name_for_ansi_c(name)

    name.replace("\\", "\\\\")
    name.replace('"', '\\"')
    name.replace("`", "\\`")
    name.replace("$", "\\$")
    return """+name+"""


def handle_file_name_for_ansi_c(name):
    out = []
    for ch in name:
        if ord(ch) < 32:
            out.append("\\x%02x" % ord(ch))
        elif ch == "\\":
            out.append("\\\\")
        else:
            out.append(ch)

    return '$"" + "".join(out) + ""'


SPLIT_RE = re.compile(r"[a-zA-Z]+|\d+")


def alphabetize(s) -> List[Tuple[str, int]]:
    out = []
    for is_digit, group in itertools.groupby(SPLIT_RE.findall(s), key=lambda x: x.isdigit()):
        if is_digit:
            for n in group:
                out.append(("", int(n)))
        else:
            out.append(("".join(group).lower(), 0))
    return out


def get_directory_and_file_names_under_top_level(path: str) -> Tuple[List[str], List[str]]:
    directory_names, file_names = [], []
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            directory_names.append(name)
        else:
            file_names.append(name)
    return directory_names, file_names
