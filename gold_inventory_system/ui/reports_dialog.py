from __future__ import annotations

from typing import Optional, List, Dict
from datetime import datetime

try:
    from PySide6 import QtWidgets, QtCore, QtGui  # type: ignore
except Exception:  # pragma: no cover
    from PyQt5 import QtWidgets, QtCore, QtGui  # type: ignore

from database.db_manager import DBManager
from utils.export_manager import ExportManager
from utils.print_manager import PrintManager


LIGHT_GREEN = "#90EE90"
LIGHT_RED = "#FFB6C1"


class ReportsDialog(QtWidgets.QDialog):
    def __init__(self, db: DBManager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("تقرير المقارنة الشهري")
        self.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.resize(900, 600)
        self._build_ui()
        self._load_report()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Period selection
        form = QtWidgets.QHBoxLayout()
        self.year_spin = QtWidgets.QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(QtCore.QDate.currentDate().year())

        self.month_combo = QtWidgets.QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(str(m), m)
        self.month_combo.setCurrentIndex(QtCore.QDate.currentDate().month() - 1)

        form.addWidget(QtWidgets.QLabel("السنة:"))
        form.addWidget(self.year_spin)
        form.addSpacing(10)
        form.addWidget(QtWidgets.QLabel("الشهر:"))
        form.addWidget(self.month_combo)
        form.addStretch(1)

        self.btn_refresh = QtWidgets.QPushButton("تحديث")
        form.addWidget(self.btn_refresh)
        layout.addLayout(form)

        # Table
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "الصنف", "الوحدة", "كمية الشهر الحالي", "كمية الشهر السابق", "الفرق"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Actions
        actions = QtWidgets.QHBoxLayout()
        self.btn_export_html = QtWidgets.QPushButton("تصدير HTML")
        self.btn_print = QtWidgets.QPushButton("طباعة من المتصفح")
        self.btn_export_excel = QtWidgets.QPushButton("تصدير Excel")
        actions.addWidget(self.btn_export_html)
        actions.addWidget(self.btn_print)
        actions.addStretch(1)
        actions.addWidget(self.btn_export_excel)
        layout.addLayout(actions)

        # Signals
        self.btn_refresh.clicked.connect(self._load_report)
        self.year_spin.valueChanged.connect(self._load_report)
        self.month_combo.currentIndexChanged.connect(self._load_report)
        self.btn_export_html.clicked.connect(self._on_export_html)
        self.btn_print.clicked.connect(self._on_print)
        self.btn_export_excel.clicked.connect(self._on_export_excel)

    # ---------------------- Data & Rendering ----------------------
    def _period(self) -> tuple[int, int]:
        return int(self.year_spin.value()), int(self.month_combo.currentData())

    def _load_report(self) -> None:
        year, month = self._period()
        rows = self.db.get_monthly_comparison(year, month)
        self._populate(rows)

    def _populate(self, rows: List[Dict[str, object]]) -> None:
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QtWidgets.QTableWidgetItem(str(r["item_name"]))
            unit_item = QtWidgets.QTableWidgetItem(str(r["unit"]))
            cur_item = QtWidgets.QTableWidgetItem(f"{float(r['current_qty']):,.3f}")
            prev_item = QtWidgets.QTableWidgetItem(f"{float(r['previous_qty']):,.3f}")
            diff = float(r["diff"]) if r["diff"] is not None else 0.0
            sign = "+" if diff > 0 else ("-" if diff < 0 else "")
            diff_item = QtWidgets.QTableWidgetItem(f"{sign}{abs(diff):,.3f}")

            # Color coding
            if diff > 0:
                diff_item.setBackground(QtGui.QColor(LIGHT_GREEN))
            elif diff < 0:
                diff_item.setBackground(QtGui.QColor(LIGHT_RED))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, unit_item)
            self.table.setItem(row, 2, cur_item)
            self.table.setItem(row, 3, prev_item)
            self.table.setItem(row, 4, diff_item)

        self.table.resizeColumnsToContents()

    # ---------------------- Export / Print ----------------------
    def _on_export_html(self) -> None:
        year, month = self._period()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "حفظ تقرير HTML",
            f"report_{year}_{month:02d}.html",
            "HTML Files (*.html)",
        )
        if not path:
            return
        rows = self.db.get_monthly_comparison(year, month)
        try:
            ExportManager.export_html(path, rows, year, month)
            QtWidgets.QMessageBox.information(self, "نجاح", "تم تصدير التقرير إلى HTML")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

    def _on_print(self) -> None:
        year, month = self._period()
        rows = self.db.get_monthly_comparison(year, month)
        try:
            path = ExportManager.export_html_to_temp(rows, year, month)
            PrintManager.open_in_browser(path)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

    def _on_export_excel(self) -> None:
        year, month = self._period()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "حفظ ملف Excel",
            f"report_{year}_{month:02d}.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return
        rows = self.db.get_monthly_comparison(year, month)
        try:
            ExportManager.export_excel(path, rows, year, month)
            QtWidgets.QMessageBox.information(self, "نجاح", "تم تصدير التقرير إلى Excel")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

