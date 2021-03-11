import collections
import raccoon as rc
from typing import Dict, Optional, List, Any

from ..logger import get_logger

logger = get_logger()

ColumnName = str


class DataTableDataFrame(rc.DataFrame):
    DEFAULT_COLUMNS = ["_dirty", "_focus_position", "_value_fn", "_cls", "_details", "_rendered_row"]

    def __init__(self, data: Optional[Dict[ColumnName, List]] = None, columns: Optional[List[ColumnName]] = None,
                 index: Optional[List[Any]] = None, index_name: ColumnName = "index", sort: bool = None):
        if columns and index_name not in columns:
            columns.insert(0, index_name)
        columns += self.DEFAULT_COLUMNS
        super().__init__(data=data, columns=columns, index=index, index_name=index_name, sort=sort)

    def _validate_index(self, indexes):
        try:
            return super(DataTableDataFrame, self)._validate_index(indexes)
        except ValueError:
            logger.error("duplicates in index: %s" % (
                [item for item, count
                 in list(collections.Counter(indexes).items()) if count > 1
                 ]))
            raise

    def log_dump(self, n=5, columns=None, label=None):
        df = self
        if columns:
            if not isinstance(columns, list):
                columns = [columns]
            df = df[columns]
        logger.info("%slength: %d, index: %s [%s%s]\n%s" % (
            "%s, " % (label) if label else "",
            len(self),
            self.index_name,
            ",".join([str(x) for x in self.index[0:min(n, len(self.index))]]),
            "..." if len(self.index) > n else "",
            df.head(n)))

    def transpose_data(self, rows):
        data_columns = list(set().union(*(list(d.keys()) for d in rows)))
        data_columns += [
            c for c in self.columns
            if c not in data_columns
            and c != self.index_name
            and c not in self.DEFAULT_COLUMNS
        ]
        data_columns += ["_cls", "_details"]

        data = dict(
            list(zip((data_columns),
                     [list(z) for z in zip(*[[
                         d.get(k, None if k != "_details" else {
                             "open": False, "disabled": False})
                         if isinstance(d, collections.abc.MutableMapping)
                         else getattr(d, k, None if k != "_details" else {"open": False, "disabled": False})
                         # for k in data_columns + self.DEFAULT_COLUMNS] for d in rows])]
                         for k in data_columns] for d in rows])]
                     ))
        )
        return data

    def update_rows(self, rows, limit=None):
        data = self.transpose_data(rows)
        if not limit:
            if len(rows):
                indexes = [x for x in self.index if x not in data.get(
                    self.index_name, [])]
                if len(indexes):
                    self.delete_rows(indexes)
            else:
                self.delete_all_rows()

        if not len(rows):
            return []

        if self.index_name not in data:
            index = list(range(len(self), len(self) + len(rows)))
            data[self.index_name] = index
        else:
            index = data[self.index_name]

        for c in data.keys():
            try:
                self.set(data[self.index_name], c, data[c])
            except ValueError as e:
                logger.error(e)
                logger.info(f"update_rows: {self.index}, {data}")
                raise Exception(c, len(self.index), len(data[c]))
        return data.get(self.index_name, [])

    def append_rows(self, rows):
        length = len(rows)
        if not length:
            return

        colnames = list(self.columns) + [c for c in self.DEFAULT_COLUMNS if c not in self.columns]

        data = self.transpose_data(rows)
        colnames += [c for c in data.keys() if c not in colnames]

        for c in self.columns:
            if not c in data:
                data[c] = [None]*length

        for c in colnames:
            if not c in self.columns:
                self[c] = None

        kwargs = dict(
            columns=colnames,
            data=data,
            sort=False,
            index=data[self.index_name],
            index_name=self.index_name,
        )

        try:
            newdata = DataTableDataFrame(**kwargs)
        except ValueError:
            raise Exception(kwargs)
        try:
            self.append(newdata)
        except ValueError:
            raise Exception(f"{self.index}, {newdata}")

    def clear(self):
        self.delete_all_rows()
