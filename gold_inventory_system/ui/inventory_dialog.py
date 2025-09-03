from __future__ import annotations

from typing import Optional, List, Tuple

try:
    from PySide6 import QtWidgets, QtCore  # type: ignore
except Exception:  # pragma: no cover
    from PyQt5 import QtWidgets, QtCore  # type: ignore

from database.db_manager import DBManager


class InventoryDialog(QtWidgets.QDialog):
    def __init__(self, db: DBManager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("إدخال الجرد الشهري")
        self.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.resize(800, 600)
        self._build_ui()
        self._load_items()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Month/Year selectors
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
        layout.addLayout(form)

        # Table of items with quantity entry
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "المعرف", "الصنف", "الوحدة", "الكمية"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Buttons
        btns = QtWidgets.QHBoxLayout()
        self.btn_load_prev = QtWidgets.QPushButton("تحميل كميات الشهر السابق")
        self.btn_save = QtWidgets.QPushButton("حفظ الجرد")
        self.btn_close = QtWidgets.QPushButton("إغلاق")
        btns.addWidget(self.btn_load_prev)
        btns.addStretch(1)
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        # Signals
        self.btn_close.clicked.connect(self.accept)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load_prev.clicked.connect(self._on_load_previous)
        self.year_spin.valueChanged.connect(self._on_period_changed)
        self.month_combo.currentIndexChanged.connect(self._on_period_changed)

    # ---------------------- Data ----------------------
    def _load_items(self) -> None:
        items = self.db.list_items("")
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r["id"])) )
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r["name"])) )
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r["unit"])) )
            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(0.0, 10_000_000.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)
            spin.setValue(0.0)
            self.table.setCellWidget(row, 3, spin)
        self._load_quantities_for_period()

    def _current_year_month(self) -> tuple[int, int]:
        year = int(self.year_spin.value())
        month = int(self.month_combo.currentData())
        return year, month

    def _load_quantities_for_period(self) -> None:
        year, month = self._current_year_month()
        inv_map = self.db.get_inventory_map(year, month)
        for row in range(self.table.rowCount()):
            item_id = int(self.table.item(row, 0).text())
            qty = inv_map.get(item_id, 0.0)
            spin = self.table.cellWidget(row, 3)
            if isinstance(spin, QtWidgets.QDoubleSpinBox):
                spin.setValue(float(qty))

    # ---------------------- Slots ----------------------
    def _on_period_changed(self) -> None:
        self._load_quantities_for_period()

    def _on_load_previous(self) -> None:
        year, month = self._current_year_month()
        prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
        prev_map = self.db.get_inventory_map(prev_year, prev_month)
        for row in range(self.table.rowCount()):
            item_id = int(self.table.item(row, 0).text())
            qty = float(prev_map.get(item_id, 0.0))
            spin = self.table.cellWidget(row, 3)
            if isinstance(spin, QtWidgets.QDoubleSpinBox):
                spin.setValue(qty)

    def _collect_entries(self) -> List[Tuple[int, float, Optional[str]]]:
        entries: List[Tuple[int, float, Optional[str]]] = []
        for row in range(self.table.rowCount()):
            item_id = int(self.table.item(row, 0).text())
            spin = self.table.cellWidget(row, 3)
            qty = 0.0
            if isinstance(spin, QtWidgets.QDoubleSpinBox):
                qty = float(spin.value())
            if qty < 0:
                raise ValueError("لا يمكن إدخال قيم سالبة")
            entries.append((item_id, qty, None))
        return entries

    def _on_save(self) -> None:
        year, month = self._current_year_month()
        try:
            entries = self._collect_entries()
            self.db.upsert_inventory_bulk(year, month, entries)
            QtWidgets.QMessageBox.information(self, "نجاح", "تم حفظ بيانات الجرد")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

