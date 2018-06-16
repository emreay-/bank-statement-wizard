import os
from typing import Optional

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle

from .ledger import Ledger


def check_font(font: str):
    return font in canvas.Canvas('').getAvailableFonts()


class StatementReportGenerator:

    _default_font = 'Courier'

    def __init__(self, font: Optional[str] = None):
        self._report_elements = []
        self._report_path = None
        self._document = None
        self._font = font if check_font(font) else self._default_font

    def __call__(
        self,
        path_to_output_dir: str,
        statement_type: str,
        statement_date: str,
        ledger: Ledger
    ):
        self._add_info_table(statement_type, statement_date)
        self._add_transactions_table(ledger)

        self._set_report_path(path_to_output_dir,
                              statement_type, statement_date)
        self._create_document()
        self._build()

    def _add_info_table(self, statement_type: str, statement_date: str):
        info_table_data = [('Statement Date:', statement_date.replace('-', '/')),
                           ('Statement Type:', statement_type)]
        info_table = Table(info_table_data, spaceAfter=40, hAlign='LEFT')
        info_table.setStyle(TableStyle([('FONTNAME', (0, 0), (0, 1), self.font_bold),
                                        ('FONTNAME', (1, 0), (1, 1), self.font)]))
        self.report_elements.append(info_table)

    def _add_transactions_table(self, ledger: Ledger):
        title = [('Date', 'Description', 'Amount', 'Category')]
        transactions_data = title + \
            [(i.date, i.description, i.amount, i.transaction_category)
             for i in ledger]
        transactions_table = Table(transactions_data)
        transactions_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, 0), self.font_bold),
                                                ('FONTNAME', (0, 1), (-1, -1), self.font)]))
        self.report_elements.append(transactions_table)

    def _set_report_path(self, path_to_output_dir: str, statement_type: str, statement_date: str):
        self.report_path = os.path.join(path_to_output_dir, '{}_report_{}.pdf'.format(
            statement_type, statement_date))

    def _create_document(self):
        self.document = SimpleDocTemplate(self.report_path, rightMargin=72, leftMargin=72,
                                          topMargin=72, bottomMargin=72, pagesize=letter)

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
        return '{}-Bold'.format(self.font)
