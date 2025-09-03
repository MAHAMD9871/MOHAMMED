from __future__ import annotations

try:
    from PySide6 import QtWidgets, QtCore  # type: ignore
except Exception:  # pragma: no cover
    from PyQt5 import QtWidgets, QtCore  # type: ignore

from typing import Optional

from database.db_manager import DBManager


class ItemsDialog(QtWidgets.QDialog):
    def __init__(self, db: DBManager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("إدارة الأصناف")
        self.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.resize(700, 500)
        self._build_ui()
        self._load_items()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Search bar
        search_layout = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("بحث بالاسم أو الوحدة...")
        self.search_edit.textChanged.connect(self._load_items)
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

        # Table
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["المعرف", "اسم الصنف", "الوحدة"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # Form
        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.unit_edit = QtWidgets.QLineEdit()
        form.addRow("اسم الصنف:", self.name_edit)
        form.addRow("وحدة القياس:", self.unit_edit)
        layout.addLayout(form)

        # Buttons
        btns = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("إضافة")
        self.btn_update = QtWidgets.QPushButton("تعديل")
        self.btn_delete = QtWidgets.QPushButton("حذف")
        self.btn_close = QtWidgets.QPushButton("إغلاق")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_delete)
        btns.addStretch(1)
        btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        # Signals
        self.btn_add.clicked.connect(self._on_add)
        self.btn_update.clicked.connect(self._on_update)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_close.clicked.connect(self.accept)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    # ---------------------- Data ----------------------
    def _load_items(self) -> None:
        search = self.search_edit.text().strip() if hasattr(self, "search_edit") else ""
        rows = self.db.list_items(search)
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r["id"])) )
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r["name"])) )
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r["unit"])) )
        self.table.resizeColumnsToContents()

    def _current_item_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        return int(self.table.item(row, 0).text())

    # ---------------------- Slots ----------------------
    def _on_selection_changed(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            self.name_edit.clear()
            self.unit_edit.clear()
            return
        row = self.table.currentRow()
        self.name_edit.setText(self.table.item(row, 1).text())
        self.unit_edit.setText(self.table.item(row, 2).text())

    def _on_add(self) -> None:
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip()
        try:
            self.db.add_item(name, unit)
            QtWidgets.QMessageBox.information(self, "نجاح", "تمت الإضافة بنجاح")
            self._load_items()
            self.name_edit.clear()
            self.unit_edit.clear()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

    def _on_update(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QtWidgets.QMessageBox.warning(self, "تنبيه", "يرجى اختيار صنف للتعديل")
            return
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip()
        try:
            self.db.update_item(item_id, name, unit)
            QtWidgets.QMessageBox.information(self, "نجاح", "تم التعديل بنجاح")
            self._load_items()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

    def _on_delete(self) -> None:
        item_id = self._current_item_id()
        if item_id is None:
            QtWidgets.QMessageBox.warning(self, "تنبيه", "يرجى اختيار صنف للحذف")
            return
        confirm = QtWidgets.QMessageBox.question(
            self, "تأكيد", "هل تريد حذف الصنف المحدد؟"
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        try:
            self.db.delete_item(item_id)
            QtWidgets.QMessageBox.information(self, "نجاح", "تم الحذف بنجاح")
            self._load_items()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "خطأ", str(exc))

