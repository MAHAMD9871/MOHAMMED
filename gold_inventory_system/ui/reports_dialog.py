from datetime import datetime
from typing import Optional, List, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QWidget, QMessageBox
)
from database.db_manager import DBManager
from utils.export_manager import ExportManager
from utils.print_manager import PrintManager

GREEN = '#90EE90'
RED = '#FFB6C1'


class ReportsDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('التقارير والمقارنات')
        self.resize(900, 600)

        now = datetime.now()
        self.month_combo = QComboBox()
        self.month_combo.addItems(['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'])
        self.month_combo.setCurrentIndex(now.month - 1)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(now.year)

        self.btn_refresh = QPushButton('تحديث')
        self.btn_export_html = QPushButton('تصدير HTML')
        self.btn_print = QPushButton('طباعة من المتصفح')
        self.btn_export_excel = QPushButton('تصدير Excel')
        self.btn_close = QPushButton('إغلاق')

        top = QHBoxLayout()
        top.addWidget(QLabel('الشهر'))
        top.addWidget(self.month_combo)
        top.addWidget(QLabel('السنة'))
        top.addWidget(self.year_spin)
        top.addWidget(self.btn_refresh)
        top.addStretch()
        top.addWidget(self.btn_export_html)
        top.addWidget(self.btn_print)
        top.addWidget(self.btn_export_excel)
        top.addWidget(self.btn_close)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['اسم الصنف', 'الوحدة', 'الشهر الحالي', 'الشهر السابق', 'الفرق'])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_refresh.clicked.connect(self.refresh_report)
        self.month_combo.currentIndexChanged.connect(self.refresh_report)
        self.year_spin.valueChanged.connect(self.refresh_report)
        self.btn_export_html.clicked.connect(self.export_html)
        self.btn_print.clicked.connect(self.print_html)
        self.btn_export_excel.clicked.connect(self.export_excel)
        self.btn_close.clicked.connect(self.close)

        self._last_html_path: str = ''
        self.refresh_report()

    def get_year_month(self) -> tuple[int, int]:
        return self.year_spin.value(), self.month_combo.currentIndex() + 1

    def refresh_report(self) -> None:
        year, month = self.get_year_month()
        rows = self.db_manager.get_monthly_comparison(year, month)
        self.table.setRowCount(0)
        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r['name'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(r['unit'])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{r['qty_curr']:.3f}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{r['qty_prev']:.3f}"))
            diff_value = float(r['diff'])
            sign = '+' if diff_value > 0 else ('-' if diff_value < 0 else '')
            diff_item = QTableWidgetItem(f"{sign}{abs(diff_value):.3f}")
            if diff_value > 0:
                diff_item.setBackground(QColor(GREEN))
            elif diff_value < 0:
                diff_item.setBackground(QColor(RED))
            self.table.setItem(row_idx, 4, diff_item)

    def build_meta(self) -> Dict[str, str]:
        year, month = self.get_year_month()
        return {
            'factory_name': 'مصنع الذهب',
            'report_title': 'تقرير المقارنة الشهرية',
            'year': str(year),
            'month': str(month),
        }

    def export_html(self) -> None:
        rows = self.collect_rows()
        if not rows:
            QMessageBox.information(self, 'تنبيه', 'لا توجد بيانات للتصدير')
            return
        meta = self.build_meta()
        path = ExportManager.export_comparison_to_html(rows, meta)
        self._last_html_path = path
        QMessageBox.information(self, 'تم', f'تم إنشاء ملف HTML:\n{path}')

    def print_html(self) -> None:
        if not self._last_html_path:
            self.export_html()
        if self._last_html_path:
            PrintManager.open_in_browser(self._last_html_path)

    def export_excel(self) -> None:
        rows = self.collect_rows()
        if not rows:
            QMessageBox.information(self, 'تنبيه', 'لا توجد بيانات للتصدير')
            return
        meta = self.build_meta()
        path = ExportManager.export_comparison_to_excel(rows, meta)
        QMessageBox.information(self, 'تم', f'تم إنشاء ملف Excel:\n{path}')

    def collect_rows(self) -> List[Dict[str, object]]:
        data: List[Dict[str, object]] = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            unit = self.table.item(row, 1).text()
            qty_curr = float(self.table.item(row, 2).text())
            qty_prev = float(self.table.item(row, 3).text())
            diff_text = self.table.item(row, 4).text()
            diff_value = float(diff_text.replace('+','').replace('-',''))
            if diff_text.startswith('-'):
                diff_value = -diff_value
            data.append({'name': name, 'unit': unit, 'qty_curr': qty_curr, 'qty_prev': qty_prev, 'diff': diff_value})
        return data