import copy
import math
import traceback
from dataclasses import *
from typing import List, Dict, Any, Optional, Sequence, Callable, Tuple

import urwid_utils.palette

from .columns import *
from .rows import *
from .dataframe import *
from .sort_info import SortInfo
from ..listbox import ScrollingListBox
from ..logger import get_logger

__all__ = ["DataTable", "DataTableColumn"]

logger = get_logger()


DEFAULT_TABLE_DIVIDER = DataTableDivider(" ")

ColumnIndex = int
RowIndex = int


def intersperse_divider(columns, divider):
    for i, col in enumerate(columns):
        yield col
        if (not i == len(columns)-1
                and not (col.hide or (i < len(columns)-1 and columns[i+1].hide))):
            yield copy.copy(divider)


class DataTable(urwid.WidgetWrap, urwid.listbox.ListWalker):

    signals = ["select", "refresh", "focus", "blur",
               # "focus", "unfocus", "row_focus", "row_unfocus",
               "drag_start", "drag_continue", "drag_stop"]

    ATTR = "table"

    attr_map = {}
    focus_map = {}
    column_focus_map = {}
    highlight_map = {}
    highlight_focus_map = {}
    highlight_focus_map2 = {}

    def __init__(self,
                 columns: List[DataTableColumn],
                 data: Optional[Dict[str, Any]] = None,
                 limit: Optional[int] = None,
                 index_column_name: str = "index",
                 with_header: bool = True,
                 with_footer: bool = False,
                 with_scrollbar: bool = False,
                 empty_message: str = "(no data)",
                 row_height = None,
                 cell_selection: bool = False,
                 sort_by: Optional[SortInfo] = None,
                 query_sort: bool = False,
                 sort_icons: bool = True,
                 sort_refocus: bool = False,
                 no_load_on_init: bool = None,
                 divider=DEFAULT_TABLE_DIVIDER,
                 padding=DEFAULT_CELL_PADDING,
                 row_style=None,
                 detail_fn=None,
                 detail_selectable=False,
                 detail_hanging_indent=None,
                 ui_sort=True,
                 ui_resize=True,
                 row_attr_fn=None):

        if not columns:
            raise Exception("Columns must be defined for the data table")

        self._columns: List[DataTableColumn] = columns
        self.data: Optional[Dict[str, Any]] = data
        self.limit: Optional[int] = limit

        self.index_column_name: str = index_column_name
        if self.index_column_name not in self.column_names:
            self._columns.insert(0, DataTableColumn(self.index_column_name, hide=True))

        self.with_header: bool = with_header
        self.with_footer: bool = with_footer
        self.with_scrollbar: bool = with_scrollbar
        self.empty_message: str = empty_message
        self.row_height = row_height
        self.cell_selection = cell_selection

        self.sort_by: SortInfo = sort_by
        self.initial_sort: SortInfo = self.sort_by

        self.query_sort = query_sort
        self.sort_icons = sort_icons
        self.sort_refocus = sort_refocus
        self.no_load_on_init = no_load_on_init

        if isinstance(divider, str):
            self.divider = DataTableDivider(self.divider)
        else:
            self.divider = divider

        self.padding = padding
        if isinstance(self.padding, tuple):
            self.padding_left, self.padding_right = self.padding
        else:
            self.padding_left = self.padding_right = self.padding

        self.row_style = row_style
        self.detail_fn = detail_fn
        self.detail_selectable = detail_selectable
        self.detail_hanging_indent = detail_hanging_indent
        self.ui_sort = ui_sort
        self.ui_resize = ui_resize
        self.row_attr_fn = row_attr_fn

        self._focus = 0
        self.page = 0

        self.sort_column: ColumnIndex = 0
        self._width = None
        self._height = None
        self._initialized = False
        self._message_showing = False

        self.filters: Optional[List[Callable]] = None
        self.filtered_rows = list()

        if self.divider:
            self._columns = list(intersperse_divider(self._columns, self.divider))

        for c in self._columns:
            c.table = self

        self.data_frame = DataTableDataFrame(
            columns=self.column_names,
            sort=False,
            index_name=self.index_column_name or None
        )

        self.header = DataTableHeaderRow(
            self,
            padding=self.padding,
            style=self.row_style,
            row_height=1  # FIXME
        )

        self.footer = DataTableFooterRow(
            self,
            padding=self.padding,
            style=self.row_style,
            row_height=1
        )

        self.pile = urwid.Pile([])
        self.listbox = ScrollingListBox(
            self, infinite=self.limit,
            with_scrollbar=self.with_scrollbar,
            row_count_fn=self.row_count
        )
        self.listbox_placeholder = urwid.WidgetPlaceholder(self.listbox)

        self._make_signal_connections()
        self._update_pile_contents()

        self.attr = urwid.AttrMap(
            self.pile,
            attr_map=self.attr_map,
        )
        super(DataTable, self).__init__(self.attr)

    def _make_signal_connections(self):
        urwid.connect_signal(
            self.listbox, "drag_start",
            lambda source, drag_from: urwid.signals.emit_signal(
                self, "drag_start", self, drag_from)
        )
        urwid.connect_signal(
            self.listbox, "drag_continue",
            lambda source, drag_from, drag_to: urwid.signals.emit_signal(
                self, "drag_continue", self, drag_from, drag_to)
        )
        urwid.connect_signal(
            self.listbox, "drag_stop",
            lambda source, drag_from, drag_to: urwid.signals.emit_signal(
                self, "drag_stop", self, drag_from, drag_to)
        )

        if self.limit:
            urwid.connect_signal(self.listbox, "load_more", self.load_more)

        if self.with_header:
            if self.ui_sort:
                urwid.connect_signal(
                    self.header, "column_click",
                    lambda index: self.sort_by_column(index, toggle=True)
                )

            if self.ui_resize:
                urwid.connect_signal(self.header, "drag", self.on_header_drag)

    def _update_pile_contents(self):
        if self.with_header:
            self.pile.contents.insert(
                0,
                (
                    urwid.Columns([
                        ("weight", 1, self.header),
                        (1, urwid.Text(("table_row_header", " ")))
                    ]),
                    self.pile.options('pack')
                )
            )

        self.pile.contents.append((self.listbox_placeholder, self.pile.options('weight', 1)))
        self.pile.focus_position = len(self.pile.contents) - 1

        if self.with_footer:
            self.pile.contents.append(
                (self.footer, self.pile.options('pack'))
            )

    def query(self, sort=None, offset=None):
        raise Exception("query method must be overriden")

    def query_result_count(self):
        raise Exception("query_result_count method must be defined")

    @property
    def focus(self):
        return self._focus

    def next_position(self, position):
        index = position + 1
        if index > len(self.filtered_rows):
            raise IndexError
        return index

    @staticmethod
    def prev_position(position):
        index = position-1
        if index < 0:
            raise IndexError
        return index

    def positions(self, reverse=False):
        if reverse:
            return range(len(self) - 1, -1, -1)
        return range(len(self))

    def set_focus(self, position):
        self._emit("blur", self._focus)
        self._focus = position
        self._emit("focus", position)
        self._modified()

    def _modified(self):
        urwid.listbox.ListWalker._modified(self)

    def __getitem__(self, position):
        if isinstance(position, slice):
            return [self[i] for i in range(*position.indices(len(self)))]
        if position < 0 or position >= len(self.filtered_rows):
            raise IndexError
        try:
            r = self.get_row_by_position(position)
            return r
        except IndexError:
            logger.error(traceback.format_exc())
            raise

    def __delitem__(self, position):
        if isinstance(position, slice):
            indexes = [self.position_to_index(p)
                       for p in range(*position.indices(len(self)))]
            self.delete_rows(indexes)
        else:
            try:
                i = self.position_to_index(self.filtered_rows[position])
                self.delete_rows(i)
            except IndexError:
                logger.error(traceback.format_exc())
                raise

    def __len__(self):
        return len(self.filtered_rows)

    def __getattr__(self, attr):
        if attr in [
                "head",
                "tail",
                "index_name",
                "log_dump",
        ]:
            return getattr(self.data_frame, attr)
        elif attr in ["body"]:
            return getattr(self.listbox, attr)
        raise AttributeError(attr)

    def render(self, size, focus=False):
        self._width = size[0]
        if len(size) > 1:
            self._height = size[1]
        if not self._initialized and not self.no_load_on_init:
            self._initialized = True
            self._invalidate()
            self.reset(reset_sort=True)
        return super().render(size, focus)

    @property
    def width(self):
        return self._width

    @property
    def min_width(self):
        return sum([
            c.min_width for c in self.visible_columns
        ])

    @property
    def height(self):
        return self._height

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == "enter" and not self.selection.details_focused:
            self._emit("select", self.selection.data)
        else:
            return key

    def decorate(self, row, column, value):
        if column.decoration_fn:
            value = column.decoration_fn(value)
        if not isinstance(value, urwid.Widget):
            if isinstance(value, tuple):
                value = (value[0], str(value[1]))
            else:
                value = str(value)

            value = urwid.Text(value)
        return value

    @property
    def column_names(self):
        return [c.name for c in self.data_columns]

    @property
    def focus_position(self):
        return self._focus

    @focus_position.setter
    def focus_position(self, value):
        self.set_focus(value)
        self.listbox._invalidate()

    def position_to_index(self, position):
        return self.data_frame.index[position]

    def index_to_position(self, index):
        return self.data_frame.index.index(index)

    def get_dataframe_row(self, index):
        try:
            d = self.data_frame.get_columns(index, as_dict=True)
        except ValueError as e:
            raise Exception(e, index, self.data_frame)
        cls = d.get("_cls")
        if cls:
            if hasattr(cls, "__dataclass_fields__"):
                # klass = type(f"DataTableRow_{cls.__name__}", [cls],
                klass = make_dataclass(
                    f"DataTableRow_{cls.__name__}",
                    [("_cls", Optional[Any], field(default=None))],
                    bases=(cls,)
                )
                k = klass(
                    **{k: d[k]
                       for k in set(
                        cls.__dataclass_fields__.keys())
                       })

                return k
            else:
                return cls(**d)
        else:
            return AttrDict(**d)

    def get_row(self, index):
        row = self.data_frame.get(index, "_rendered_row")

        if self.data_frame.get(index, "_dirty") or row is None:
            self.refresh_calculated_fields([index])
            vals = self.get_dataframe_row(index)
            row = self.render_item(index)
            if self.row_attr_fn:
                attr = self.row_attr_fn(vals)
                if attr:
                    row.set_attr(attr)
            focus = self.data_frame.get(index, "_focus_position")
            if focus is not None:
                row.set_focus_column(focus)
            self.data_frame.set(index, "_rendered_row", row)
            self.data_frame.set(index, "_dirty", False)
        return row

    def get_row_by_position(self, position):
        index = self.position_to_index(self.filtered_rows[position])
        return self.get_row(index)

    def get_value(self, row, column):
        return self.data_frame[self.position_to_index(row), column]

    def set_value(self, row, column, value):
        self.data_frame.set(self.position_to_index(row), column, value)

    @property
    def selection(self):
        if len(self.body) and self.focus_position is not None:
            # FIXME: make helpers to map positions to indexes
            return self[self.focus_position]

    def render_item(self, index):
        row = DataTableBodyRow(self, index,
                               row_height=self.row_height,
                               divider=self.divider,
                               padding=self.padding,
                               cell_selection=self.cell_selection,
                               style=self.row_style)
        return row

    def refresh_calculated_fields(self, indexes=None):
        if not indexes:
            indexes = self.data_frame.index[:]
        if not hasattr(indexes, "__len__"):
            indexes = [indexes]
        for col in self.data_columns:
            if not col.value_fn:
                continue
            for index in indexes:
                if self.data_frame[index, "_dirty"]:
                    self.data_frame.set(index, col.name, col.value_fn(
                        self, self.get_dataframe_row(index)))

    def visible_data_column_index(self, column_name) -> ColumnIndex:
        try:
            return next(i for i, c in enumerate(self.visible_data_columns) if c.name == column_name)
        except StopIteration:
            raise IndexError

    def sort_by_column(self, col=None, reverse=None, toggle=False):
        logger.debug(f"col={col}, reverse={reverse}, toggle={toggle}")
        column_name = None
        column_number = None

        if isinstance(col, tuple):
            col, reverse = col

        elif col is None:
            col = self.sort_column

        if isinstance(col, int):
            try:
                column_name = self.visible_data_columns[col].name
            except IndexError:
                raise Exception(f"Bad column number: {col}")
            column_number = col
        elif isinstance(col, str):
            column_name = col
            column_number = self.visible_data_column_index(column_name)

        self.sort_column = column_number

        if not column_name:
            logger.debug(f"Cannot retrieve a column name for column {col}")
            return
        try:
            column = self.get_column_with_name(column_name)
        except Exception as e:
            logger.exception(f"Implicitly ignored exception while getting column index: {e}")
            return  # FIXME

        if reverse is None and column.sort_reverse is not None:
            reverse = column.sort_reverse

        if toggle and self.sort_by and column_name == self.sort_by.field_name:
            reverse = not self.sort_by.is_reverse

        self.sort_by = SortInfo(field_name=column_name, is_reverse=reverse)

        logger.debug(f"sort_by: {column_name}, ({self.sort_column}), {reverse}")
        if self.query_sort:
            self.reset()

        row_index: Optional[RowIndex] = None

        if self.sort_refocus:
            row_index = self[self._focus].data.get(self.index_column_name, None)
            logger.debug(f"row_index: {row_index}")

        self.sort(column_name, key=column.sort_key)

        if self.with_header:
            logger.debug(f"{self.__class__.__name__}.sort_by_column: Updating sort for the header")
            self.header.update_sort(self.sort_by)

        self.set_focus_column(self.sort_column)
        if row_index:
            self.focus_position = self.index_to_position(row_index)

    def sort(self, column, key: Optional[Callable[[Any], Tuple[bool, Any]]] = None):
        if not key:
            def key(x):
                return x is None, x

        self.data_frame.sort_columns(
            column,
            key=key,
            reverse=self.sort_by.is_reverse)
        self._modified()

    def set_focus_column(self, index):
        idx = [i for i, c in enumerate(self.visible_columns)
               if not isinstance(c, DataTableDivider)
               ][index]

        logger.info(f"{index}, {idx}")
        if self.with_header:
            self.header.set_focus_column(idx)

        if self.with_footer:
            self.footer.set_focus_column(idx)

        self.data_frame["_focus_position"] = idx
        self.data_frame["_dirty"] = True

    def cycle_sort_column(self, step):

        if not self.ui_sort:
            return
        if self.sort_column is None:
            index = 0
        else:
            index = (self.sort_column + step)
            if index < 0:
                index = len(self.visible_data_columns)-1
            if index > len(self.visible_data_columns)-1:
                index = 0
        logger.debug("index: %d" % (index))
        self.sort_by_column(index)

    def sort_index(self):
        self.data_frame.sort_index()
        self._modified()

    def add_columns(self, columns, data=None):
        if not isinstance(columns, list):
            columns = [columns]
            if data:
                data = [data]

        self._columns += columns
        for i, column in enumerate(columns):
            self.data_frame[column.name] = data = data[i] if data else None

        self.invalidate()

    def remove_columns(self, columns):
        if not isinstance(columns, list):
            columns = [columns]

        # FIXME
        columns = [column
                   for column in columns
                   if column != "divider"]

        self._columns = [c for c in self._columns if c.name not in columns]
        self.data_frame.delete_columns(columns)
        self.invalidate()

    def set_columns(self, columns):
        self.remove_columns([c.name for c in self._columns])
        self.add_columns(columns)
        self.reset()

    def toggle_columns(self, columns, show=None):
        if not isinstance(columns, list):
            columns = [columns]

        for column in columns:
            if isinstance(column, int):
                try:
                    column = self._columns[column]
                except IndexError:
                    raise Exception("bad column number: %d" % (column))
            else:
                try:
                    column = next(
                        (c for c in self._columns if c.name == column))
                except IndexError:
                    raise Exception("column %s not found" % (column))

            if show is None:
                column.hide = not column.hide
            else:
                column.hide = show
        self.invalidate()

    def show_columns(self, columns):
        self.toggle_columns(columns, True)

    def hide_columns(self, columns):
        self.show_column(columns, False)

    def resize_column(self, name, size):

        try:
            index, col = next((i, c) for i, c in enumerate(
                self.data_columns) if c.name == name)
        except StopIteration:
            raise Exception(self.data_columns, name)
        if isinstance(size, tuple):
            col.sizing, col.width = size
        elif isinstance(size, int):
            col.sizing = "given"
            col.width = size
        else:
            raise NotImplementedError
        if self.with_header:
            self.header.update()
        for r in self:
            r.update()
        if self.with_footer:
            self.footer.update()

    def on_header_drag(self, source, source_column, start, end):

        if not source:
            return

        def resize_columns(cols, mins, index, delta, direction):
            logger.debug(
                f"cols: {cols}, mins: {mins}, index: {index}, delta: {delta}, direction: {direction}")
            new_cols = [c for c in cols]

            if (index == 0) or (direction == 1 and index != len(cols)-1):
                indexes = range(index, len(cols))
            else:
                indexes = range(index, -1, -1)

            deltas = [a-b for a, b in zip(cols, mins)]
            d = delta

            for n, i in enumerate(indexes):
                if delta < 0:
                    try:
                        d = max(delta, -deltas[i])
                    except:
                        raise Exception(cols, mins, deltas, list(indexes))
                elif delta > 0:
                    # can only grow to maximum of remaining deltas?
                    d = min(delta, sum([deltas[x] for x in indexes[1:]]))
                else:
                    continue

                new_cols[i] += d

                if i == index:
                    delta = -d
                    d = delta
                    indexes = list(reversed(indexes))
                else:
                    delta -= d
                    if delta == 0:
                        break

            return new_cols

        old_widths = self.header.column_widths((self.width,))

        if isinstance(source, DataTableDividerCell):
            try:
                index, cell = list(enumerate([c for c in itertools.takewhile(
                    lambda c: c != source,
                    [x[0] for x in self.header.columns.contents]
                ) if not isinstance(c, DataTableDividerCell)]))[-1]
            except IndexError:
                index, cell = list(enumerate([c for c in itertools.takewhile(
                    lambda c: c != source,
                    [x[0] for x in self.header.columns.contents]
                ) if not isinstance(c, DataTableDividerCell)]))[-1]
        else:
            cell = source
            index = next(i for i, c in enumerate([
                x[0] for x in self.header.columns.contents
                if not isinstance(x[0], DataTableDividerCell)
            ]) if c == cell)

        colname = cell.column.name
        column = next(
            c for c in self.visible_data_columns if c.name == colname)

        new_width = old_width = old_widths[index]

        delta = end-start

        if isinstance(source, DataTableDividerCell):
            drag_direction = 1
        elif index == 0 and source_column <= int(old_width / 3):
            return
        elif index != 0 and source_column <= int(round(old_width / 3)):
            drag_direction = -1
            delta = -delta
        elif index != len(self.visible_data_columns)-1 and source_column >= int(round((2*old_width) / 3)):
            drag_direction = 1
        else:
            return

        widths = [c.header.width for c in self.visible_data_columns]
        mins = [c.min_width for c in self.visible_data_columns]
        new_widths = resize_columns(widths, mins, index, delta, drag_direction)

        for i, c in enumerate(self.visible_data_columns):
            if c.header.width != new_widths[i]:
                self.resize_column(c.name, new_widths[i])

        self.resize_body_rows()
        logger.debug(f"{widths}, {mins}, {new_widths}")
        if sum(widths) != sum(new_widths):
            logger.warning(f"{sum(widths)} != {sum(new_widths)}")

    def resize_body_rows(self):
        for r in self:
            r.on_resize()

    def enable_cell_selection(self):
        logger.debug("enable_cell_selection")
        for r in self:
            r.enable_cell_selection()
        self.reset()
        self.cell_selection = True

    def disable_cell_selection(self):
        logger.debug("disable_cell_selection")
        for r in self:
            r.disable_cell_selection()
        self.reset()
        self.cell_selection = False

    def toggle_cell_selection(self):
        if self.cell_selection:
            self.disable_cell_selection()
        else:
            self.enable_cell_selection()

    def get_column_with_name(self, name: str) -> DataTableColumn:
        return next((c for c in self._columns if c.name == name))

    @property
    def data_columns(self) -> Sequence[DataTableColumn]:
        return [c for c in self._columns if not isinstance(c, DataTableDivider)]

    @property
    def visible_columns(self):
        return [c for c in self._columns if not c.hide]

    @property
    def visible_data_columns(self):
        return [c for c in self.data_columns if not c.hide]

    def add_row(self, data, sort=True):

        self.data_frame.append_rows([data])
        if sort:
            self.sort_by_column()
        self.apply_filters()

    def delete_rows(self, indexes):

        self.data_frame.delete_rows(indexes)
        self.apply_filters()
        if self.focus_position > 0 and self.focus_position >= len(self)-1:
            self.focus_position = len(self)-1

    def invalidate(self):
        self.data_frame["_dirty"] = True
        if self.with_header:
            self.header.update()
        if self.with_footer:
            self.footer.update()
        self._modified()

    def invalidate_rows(self, indexes):
        if not isinstance(indexes, list):
            indexes = [indexes]
        for index in indexes:
            self.refresh_calculated_fields(index)

        self.data_frame[indexes, "_dirty"] = True
        self._modified()
        # FIXME: update header / footer if dynamic

    def swap_rows_by_field(self, p0, p1, field=None):

        if not field:
            field = self.index_column_name

        i0 = self.position_to_index(p0)
        i1 = self.position_to_index(p1)

        r0 = {k: v[0] for k, v in list(self.data_frame[i0, None].to_dict().items())}
        r1 = {k: v[0] for k, v in list(self.data_frame[i1, None].to_dict().items())}

        for k, v in list(r0.items()):
            if k != field:
                self.data_frame.set(i1, k, v)

        for k, v in list(r1.items()):
            if k != field:
                self.data_frame.set(i0, k, v)
        self.data_frame.set(i0, "_dirty", True)

        self.invalidate_rows([i0, i1])

    def swap_rows(self, p0, p1, field=None):
        self.swap_rows_by_field(p0, p1, field=field)

    def row_count(self):

        if not self.limit:
            return None

        if self.limit:
            return self.query_result_count()
        else:
            return len(self)

    def apply_filters(self, filters=None):

        if not filters:
            filters = self.filters
        elif not isinstance(filters, list):
            filters = [filters]

        self.filtered_rows = list(
            i
            for i, row in enumerate(self.data_frame.iterrows())
            if not filters or all(
                f(row)
                for f in filters
            )
        )

        self.filters = filters

    def clear_filters(self):
        self.filtered_rows = list(range(len(self.data_frame)))
        self.filters = None

    def load_all(self):
        if len(self) >= self.query_result_count():
            return
        logger.debug("load_all: %s" % (self.page))
        self.requery(self.page*self.limit, load_all=True)
        self.page = (self.query_result_count() // self.limit)
        self.listbox._invalidate()

    def load_more(self, position):
        if position is not None and position > len(self):
            return False
        self.page = len(self) // self.limit
        offset = (self.page)*self.limit
        if (self.row_count() is not None
                and len(self) >= self.row_count()):

            return False

        try:
            self.requery(offset=offset)
        except Exception as e:
            raise Exception(
                f"{position}, {len(self)}, {self.row_count()}, {offset}, {self.limit}, {e}")

        return True

    def requery(self, offset=None, limit=None, load_all=False, **kwargs):
        logger.debug(f"requery: {offset}, {limit}")
        if (offset is not None) and self.limit:
            self.page = offset // self.limit
            offset = self.page*self.limit
            limit = self.limit
        elif self.limit:
            self.page = (limit // self.limit)
            limit = (self.page) * self.limit
            offset = 0

        kwargs = {"load_all": load_all}
        if self.query_sort:
            kwargs["sort"] = self.sort_by
        else:
            kwargs["sort"] = (None, False)
        limit = limit or self.limit
        if limit:
            kwargs["offset"] = offset
            kwargs["limit"] = limit

        if self.data is not None:
            rows = self.data
        else:
            rows = list(self.query(**kwargs))

        for row in rows:
            row["_cls"] = type(row)

        updated = self.data_frame.update_rows(rows, limit=self.limit)
        self.data_frame["_focus_position"] = self.sort_column

        self.refresh_calculated_fields()
        self.apply_filters()

        if len(updated):
            for i in updated:
                pos = self.index_to_position(i)
                self[pos].update()
            if self.sort_by:
                self.sort_by_column(col=self.sort_by.field_name, reverse=self.sort_by.is_reverse)

        self._modified()

        if not len(self) and self.empty_message:
            self.show_message(self.empty_message)
        else:
            self.hide_message()

    def refresh(self, reset=False):
        logger.debug(f"refresh: {reset}")
        offset = None
        idx = None
        pos = 0
        if reset:
            self.page = 0
            offset = 0
            limit = self.limit
            self.data_frame.delete_all_rows()
        else:
            try:
                idx = getattr(self.selection.data, self.index_column_name)
            except (AttributeError, IndexError):
                pass
            pos = self.focus_position
            limit = len(self)
        self.requery(offset=offset, limit=limit)
        if self._initialized:
            self.pack_columns()

        if idx:
            try:
                pos = self.index_to_position(idx)
            except:
                pass
        self.focus_position = pos

    def reset_columns(self):
        for c in self.visible_columns:
            if c.sizing == c.initial_sizing and c.width == c.initial_width:
                continue
            self.resize_column(c.name, (c.initial_sizing, c.initial_width))

    def reset(self, reset_sort=False):
        self.refresh(reset=True)

        if reset_sort and self.initial_sort is not None:
            self.sort_by_column(col=self.initial_sort.field_name, reverse=self.initial_sort.is_reverse)
        self._modified()

    def pack_columns(self):
        widths = self.header.column_widths((self.width,))
        logger.debug(f"{self}, {widths}")

        other_columns, pack_columns = [
            list(x) for x in partition(
                lambda c: c[0].pack == True,
                zip(self.visible_columns, widths)
            )
        ]

        other_widths = sum([c[1] for c in other_columns])

        num_pack = len(pack_columns)
        available = self.width - \
            (1 if self.with_scrollbar else 0) - other_widths
        if self.row_style in ["boxed", "grid"]:
            available -= 2

        for i, (c, cw) in enumerate(pack_columns):
            w = min(c.contents_width, available//(num_pack-i))
            logger.debug(
                f"resize: {c.name}, available: {available}, contents: min({c.contents_width}, {available//(num_pack-i)}), {w})")
            self.resize_column(c.name, w)
            available -= w

        self.resize_body_rows()

    def show_message(self, message):

        if self._message_showing:
            self.hide_message()

        overlay = urwid.Overlay(
            urwid.Filler(
                urwid.Pile([
                    ("pack", urwid.Padding(
                        urwid.Text(("table_message", message)),
                        width="pack",
                        align="center"
                    )),
                    (1, urwid.Filler(urwid.Text("")))
                ]),
                valign="top"
            ),
            self.listbox,
            "center", ("relative", 100), "top", ("relative", 100)
        )
        self.listbox_placeholder.original_widget = overlay
        self._message_showing = True

    def hide_message(self):
        if not self._message_showing:
            return
        self.listbox_placeholder.original_widget = self.listbox

    def load(self, path):

        with open(path, "r") as f:
            json = "\n".join(f.readlines())
            self.data_frame = DataTableDataFrame.from_json(json)
        self.reset()

    def save(self, path):
        with open(path, "w") as f:
            f.write(self.data_frame.to_json())

    @classmethod
    def get_palette_entries(
            cls,
            user_entries={},
            min_contrast_entries=None,
            min_contrast=2.0,
            default_background="black"
    ):

        foreground_map = {
            "table_divider": ["light gray", "light gray"],
            "table_row_body": ["light gray", "light gray"],
            "table_row_header": ["light gray", "white"],
            "table_row_footer": ["light gray", "white"],
        }

        background_map = {
            None: ["black", "black"],
            "focused": ["dark gray", "g15"],
            "column_focused": ["black", "#660"],
            "highlight": ["light gray", "g15"],
            "highlight focused": ["light gray", "g23"],
            "highlight column_focused": ["light gray", "#660"],
        }

        entries = dict()

        row_attr = "table_row_body"
        for suffix in [None, "focused", "column_focused",
                       "highlight", "highlight focused",
                       "highlight column_focused",
                       ]:
            if suffix:
                attr = ' '.join([row_attr, suffix])
            else:
                attr = row_attr
            entries[attr] = urwid_utils.palette.PaletteEntry(
                mono="white",
                foreground=foreground_map[row_attr][0],
                background=background_map[suffix][0],
                foreground_high=foreground_map[row_attr][1],
                background_high=background_map[suffix][1],
            )

        header_foreground_map = {
            None: ["white,bold", "white,bold"],
            "focused": ["dark gray", "white,bold"],
            "column_focused": ["black", "black"],
            "highlight": ["yellow,bold", "yellow,bold"],
            "highlight focused": ["yellow", "yellow"],
            "highlight column_focused": ["yellow", "yellow"],
        }

        header_background_map = {
            None: ["light gray", "g23"],
            "focused": ["light gray", "g50"],
            "column_focused": ["white", "g70"],  # "g23"],
            "highlight": ["light gray", "g38"],
            "highlight focused": ["light gray", "g50"],
            "highlight column_focused": ["white", "g70"],
        }

        for prefix in ["table_row_header", "table_row_footer"]:
            for suffix in [
                None, "focused", "column_focused",
                "highlight", "highlight focused",
                "highlight column_focused"
            ]:
                if suffix:
                    attr = ' '.join([prefix, suffix])
                else:
                    attr = prefix
                entries[attr] = urwid_utils.palette.PaletteEntry(
                    mono="white",
                    foreground=header_foreground_map[suffix][0],
                    background=header_background_map[suffix][0],
                    foreground_high=header_foreground_map[suffix][1],
                    background_high=header_background_map[suffix][1],
                )

        for name, entry in list(user_entries.items()):
            DataTable.focus_map[name] = "%s focused" % (name)
            DataTable.highlight_map[name] = "%s highlight" % (name)
            DataTable.column_focus_map["%s focused" %
                                       (name)] = "%s column_focused" % (name)
            DataTable.highlight_focus_map["%s highlight" % (
                name)] = "%s highlight focused" % (name)
            for suffix in [None, "focused", "column_focused",
                           "highlight", "highlight focused",
                           "highlight column_focused",
                           ]:

                # Check entry backgroun colors against default bg.  If they're
                # the same, replace the entry's background color with focus or
                # highglight color.  If not, preserve the entry background.

                default_bg_rgb = urwid.AttrSpec(
                    default_background, default_background, 16)
                bg_rgb = urwid.AttrSpec(entry.background, entry.background, 16)
                background = background_map[suffix][0]
                if default_bg_rgb.get_rgb_values() != bg_rgb.get_rgb_values():
                    background = entry.background

                background_high = background_map[suffix][1]
                if entry.background_high:
                    bg_high_rgb = urwid.AttrSpec(
                        entry.background_high,
                        entry.background_high,
                        (1 << 24
                         if urwid_utils.palette.URWID_HAS_TRUE_COLOR
                         else 256
                         )
                    )
                    if default_bg_rgb.get_rgb_values() != bg_high_rgb.get_rgb_values():
                        background_high = entry.background_high

                foreground = entry.foreground
                background = background
                foreground_high = entry.foreground_high if entry.foreground_high else entry.foreground
                if min_contrast_entries and name in min_contrast_entries:
                    # All of this code is available in the colourettu package
                    # (https://github.com/MinchinWeb/colourettu) but newer
                    # versions don't run Python 3, and older versions don't work
                    # right.
                    def normalized_rgb(r, g, b):

                        r1 = r / 255
                        g1 = g / 255
                        b1 = b / 255

                        if r1 <= 0.03928:
                            r2 = r1 / 12.92
                        else:
                            r2 = math.pow(((r1 + 0.055) / 1.055), 2.4)
                        if g1 <= 0.03928:
                            g2 = g1 / 12.92
                        else:
                            g2 = math.pow(((g1 + 0.055) / 1.055), 2.4)
                        if b1 <= 0.03928:
                            b2 = b1 / 12.92
                        else:
                            b2 = math.pow(((b1 + 0.055) / 1.055), 2.4)

                        return (r2, g2, b2)

                    def luminance(r, g, b):

                        return math.sqrt(
                            0.299 * math.pow(r, 2) +
                            0.587 * math.pow(g, 2) +
                            0.114 * math.pow(b, 2)
                        )

                    def contrast(c1, c2):

                        n1 = normalized_rgb(*c1)
                        n2 = normalized_rgb(*c2)
                        lum1 = luminance(*n1)
                        lum2 = luminance(*n2)
                        minlum = min(lum1, lum2)
                        maxlum = max(lum1, lum2)
                        return (maxlum + 0.05) / (minlum + 0.05)

                    table_bg = background_map[suffix][1]
                    attrspec_bg = urwid.AttrSpec(table_bg, table_bg, 256)
                    color_bg = attrspec_bg.get_rgb_values()[3:6]
                    attrspec_fg = urwid.AttrSpec(
                        foreground_high,
                        foreground_high,
                        256
                    )
                    color_fg = attrspec_fg.get_rgb_values()[0:3]
                    cfg = contrast(color_bg, color_fg)
                    cblack = contrast((0, 0, 0), color_fg)
                    if cfg < min_contrast and cfg < cblack:
                        foreground_high = "black"

                if suffix:
                    attr = ' '.join([name, suffix])
                else:
                    attr = name

                # print foreground, foreground_high, background, background_high
                entries[attr] = urwid_utils.palette.PaletteEntry(
                    mono="white",
                    foreground=foreground,
                    background=background,
                    foreground_high=foreground_high,
                    background_high=background_high,
                )

            entries["table_message"] = urwid_utils.palette.PaletteEntry(
                mono="white",
                foreground="black",
                background="white",
                foreground_high="black",
                background_high="white",
            )

        return entries
