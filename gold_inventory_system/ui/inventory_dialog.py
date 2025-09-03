from datetime import datetime
from typing import Optional, List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QDoubleSpinBox, QMessageBox, QWidget
)
from database.db_manager import DBManager


class InventoryDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('إدخال الجرد الشهري')
        self.resize(800, 550)

        now = datetime.now()
        self.month_combo = QComboBox()
        self.month_combo.addItems(['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'])
        self.month_combo.setCurrentIndex(now.month - 1)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(now.year)

        self.btn_load = QPushButton('تحميل')
        self.btn_save = QPushButton('حفظ الجرد')
        self.btn_close = QPushButton('إغلاق')

        top = QHBoxLayout()
        top.addWidget(QLabel('الشهر'))
        top.addWidget(self.month_combo)
        top.addWidget(QLabel('السنة'))
        top.addWidget(self.year_spin)
        top.addWidget(self.btn_load)
        top.addStretch()
        top.addWidget(self.btn_save)
        top.addWidget(self.btn_close)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['اسم الصنف', 'وحدة القياس', 'الكمية'])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_load.clicked.connect(self.load_items)
        self.month_combo.currentIndexChanged.connect(self.load_items)
        self.year_spin.valueChanged.connect(self.load_items)
        self.btn_save.clicked.connect(self.save_inventory)
        self.btn_close.clicked.connect(self.close)

        self.load_items()

    def get_year_month(self) -> tuple[int, int]:
        return self.year_spin.value(), self.month_combo.currentIndex() + 1

    def load_items(self) -> None:
        self.table.setRowCount(0)
        items = self.db_manager.list_items('')
        year, month = self.get_year_month()
        existing = self.db_manager.get_inventory_for_month(year, month)
        for r in items:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r['name'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(r['unit'])))
            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0, 1_000_000_000)
            qty_spin.setDecimals(3)
            qty_spin.setSingleStep(0.1)
            item_id = int(r['id'])
            if item_id in existing:
                qty_spin.setValue(float(existing[item_id]))
            self.table.setCellWidget(row_idx, 2, qty_spin)
            self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(item_id)))

    def save_inventory(self) -> None:
        year, month = self.get_year_month()
        items_quantities: List[Tuple[int, float]] = []
        for row in range(self.table.rowCount()):
            header_item = self.table.verticalHeaderItem(row)
            if not header_item:
                continue
            item_id = int(header_item.text())
            widget = self.table.cellWidget(row, 2)
            qty = float(widget.value()) if widget else 0.0
            if qty < 0:
                QMessageBox.warning(self, 'تنبيه', 'لا يمكن إدخال قيم سالبة')
                return
            items_quantities.append((item_id, qty))
        try:
            self.db_manager.set_inventory_for_month(year, month, items_quantities)
            QMessageBox.information(self, 'تم', 'تم حفظ الجرد بنجاح')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', f'تعذر حفظ الجرد:\n{exc}')