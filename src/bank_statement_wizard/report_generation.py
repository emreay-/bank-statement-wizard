import os
from typing import Optional, Tuple, Dict

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie, Rect

from .domain.ledger import Ledger


def check_font(font: str):
    return font in canvas.Canvas('').getAvailableFonts()


class StatementReportGenerator:

    _default_font = "Courier"
    _default_page_size = letter
    _default_margin = 72

    def __init__(
        self,
        font: Optional[str] = None,
        page_size: Optional[Tuple[float, float]] = None,
        margin: Optional[int] = None
    ):
        self._report_elements = []
        self._report_path = None
        self._document = None
        self._font = font if check_font(font) else self._default_font
        self._page_size = page_size if page_size else self._default_page_size
        self._margin = margin if margin != None else self._default_margin

    def __call__(
        self,
        path_to_output_dir: str,
        statement_type: str,
        statement_date: str,
        ledger: Ledger,
        expense_stats: Dict[str, Tuple]
    ):
        self._add_info_table(statement_type, statement_date)
        self._add_balance_table(ledger)
        self._add_transactions_table(ledger)
        self._add_category_stats(expense_stats)
        self._add_pie_chart(expense_stats, size=self.width * 0.45, padding=0)

        self._set_report_path(path_to_output_dir,
                              statement_type, statement_date)
        self._create_document()
        self._build()

    def _add_info_table(self, statement_type: str, statement_date: str):
        info_table_data = [("Statement Date:", statement_date.replace("-", "/")),
                           ("Statement Type:", statement_type)]
        info_table = Table(info_table_data, spaceAfter=40, hAlign="LEFT")
        info_table.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), self.font_bold),
                                        ("FONTNAME", (1, 0), (-1, -1), self.font)]))
        self.report_elements.append(info_table)

    def _add_balance_table(self, ledger: Ledger):
        data = [("Credit Balance [Money deposited]       : ", "{:.2f}".format(ledger.credit_balance)),
                ("Debit Balance  [Money spent/withdrawn] : ",
                 "{:.2f}".format(ledger.debit_balance)),
                ("Balance                                : ", "{:.2f}".format(ledger.balance))]
        balance_table = Table(data, spaceAfter=40, hAlign="LEFT")
        balance_table.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), self.font_bold),
                                           ("FONTNAME", (1, 0), (-1, -1), self.font)]))
        self.report_elements.append(balance_table)

    def _add_transactions_table(self, ledger: Ledger):
        title = [("Date", "Description", "Amount", "Category")]
        transactions_data = title + \
            [(i.date, i.description, i.amount, i.category)
             for i in ledger.transactions]
        transactions_table = Table(transactions_data, spaceAfter=40)
        transactions_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, 0), self.font_bold),
                                                ("FONTNAME", (0, 1), (-1, -1), self.font)]))
        self.report_elements.append(transactions_table)

    def _add_category_stats(self, expense_stats: Dict[str, Tuple]):
        if expense_stats:
            title = [("Category", "Total Amount", "Percentage")]
            data = [(category, "{:.2f}".format(total), "{:.2f} %".format(percentage * 100))
                    for category, (total, percentage) in expense_stats.items()]
            data.sort(key=lambda x: float(x[1]), reverse=True)
            stats_table = Table(title + data, spaceAfter=40)
            stats_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, 0), self.font_bold),
                                             ("FONTNAME", (0, 1), (-1, -1), self.font)]))
            self.report_elements.append(stats_table)

    def _add_pie_chart(
            self,
            expense_stats: Dict[str, Tuple],
            size: int,
            padding: int,
    ):
        if expense_stats:
            figure = Drawing(self.width, min(size + 2 * padding, self.height))
            pie_chart = Pie()
            pie_chart.x = (self.width - size) / 2
            pie_chart.y = padding
            pie_chart.width = size
            pie_chart.height = size
            pie_chart.data = [i[0] for i in expense_stats.values()]
            pie_chart.labels = list(expense_stats.keys())
            pie_chart.slices.strokeWidth = 0.5
            pie_chart.sideLabels = True
            figure.add(pie_chart)
            self.report_elements.append(figure)

    def _set_report_path(self, path_to_output_dir: str, statement_type: str, statement_date: str):
        self.report_path = os.path.join(path_to_output_dir, "{}_report_{}.pdf".format(
            statement_type, statement_date))

    def _create_document(self):
        self.document = SimpleDocTemplate(
            self.report_path,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
            pagesize=self._default_page_size
        )

    def _build(self):
        self.document.build(self.report_elements)

    @property
    def report_elements(self):
        return self._report_elements

    @property
    def document(self):
        return self._document

    @document.setter
    def document(self, value):
        self._document = value

    @property
    def report_path(self):
        return self._report_path

    @report_path.setter
    def report_path(self, value):
        self._report_path = value

    @property
    def font(self):
        return self._font

    @property
    def font_bold(self):
        return "{}-Bold".format(self.font)

    @property
    def margin(self):
        return self._margin

    @property
    def width(self):
        return self._page_size[0] - 2 * self.margin - 12

    @property
    def height(self):
        return self._page_size[1] - 2 * self.margin - 12
