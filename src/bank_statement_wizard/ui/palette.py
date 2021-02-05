import panwid
from urwid_utils.palette import Palette, PaletteEntry

__all__ = ["PALETTE"]


PALETTE = Palette("default",
                  **panwid.listbox.ScrollingListBox.get_palette_entries(),
                  **panwid.DataTable.get_palette_entries(
                      user_entries={"table_row_body highlight": PaletteEntry(
                          mono="white",
                          foreground="white",
                          background="black"
                      )}
                  ))
PALETTE += [
    ("body", "white", "", "standout"),
    ("header", "white", "dark red", "bold"),
    ("button normal", "light gray", "dark blue", "standout"),
    ("title", "white", "black"),
    ("exit", "white", "dark blue")
]
