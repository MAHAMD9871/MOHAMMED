from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QFormLayout, QDialogButtonBox, QComboBox, QWidget
)
from database.db_manager import DBManager


class ItemFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, name: str = '', unit: str = '') -> None:
        super().__init__(parent)
        self.setWindowTitle('بيانات الصنف')
        self.name_edit = QLineEdit(name)
        self.unit_edit = QLineEdit(unit)

        form = QFormLayout()
        form.addRow('اسم الصنف', self.name_edit)
        form.addRow('وحدة القياس', self.unit_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_values(self) -> tuple[str, str]:
        return self.name_edit.text().strip(), self.unit_edit.text().strip()


class ItemsDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle('إدارة الأصناف')
        self.resize(700, 500)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('بحث بالاسم...')
        self.btn_search = QPushButton('بحث')
        self.btn_add = QPushButton('إضافة')
        self.btn_edit = QPushButton('تعديل')
        self.btn_delete = QPushButton('حذف')
        self.btn_close = QPushButton('إغلاق')

        top = QHBoxLayout()
        top.addWidget(self.search_edit)
        top.addWidget(self.btn_search)
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_delete)
        top.addWidget(self.btn_close)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['اسم الصنف', 'وحدة القياس', 'تاريخ الإنشاء'])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_search.clicked.connect(self.refresh_table)
        self.search_edit.returnPressed.connect(self.refresh_table)
        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_delete.clicked.connect(self.delete_item)
        self.btn_close.clicked.connect(self.close)

        self.refresh_table()

    def refresh_table(self) -> None:
        term = self.search_edit.text().strip()
        rows = self.db_manager.list_items(term)
        self.table.setRowCount(0)
        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r['name'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(r['unit'])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(r['created_at'])))
            self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(r['id'])))

    def get_selected_item_id(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        header_item = self.table.verticalHeaderItem(row)
        return int(header_item.text()) if header_item and header_item.text().isdigit() else None

    def add_item(self) -> None:
        dlg = ItemFormDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, unit = dlg.get_values()
            if not name or not unit:
                QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال اسم ووحدة القياس')
                return
            try:
                self.db_manager.add_item(name, unit)
                self.refresh_table()
            except Exception as exc:
                QMessageBox.critical(self, 'خطأ', f'تعذر إضافة الصنف:\n{exc}')

    def edit_item(self) -> None:
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.information(self, 'تنبيه', 'الرجاء اختيار صنف للتعديل')
            return
        row = self.table.currentRow()
        current_name = self.table.item(row, 0).text()
        current_unit = self.table.item(row, 1).text()
        dlg = ItemFormDialog(self, current_name, current_unit)
        if dlg.exec() == QDialog.Accepted:
            name, unit = dlg.get_values()
            if not name or not unit:
                QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال اسم ووحدة القياس')
                return
            try:
                self.db_manager.update_item(item_id, name, unit)
                self.refresh_table()
            except Exception as exc:
                QMessageBox.critical(self, 'خطأ', f'تعذر تعديل الصنف:\n{exc}')

    def delete_item(self) -> None:
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.information(self, 'تنبيه', 'الرجاء اختيار صنف للحذف')
            return
        if not self.db_manager.can_delete_item(item_id):
            QMessageBox.warning(self, 'تنبيه', 'لا يمكن حذف الصنف لوجود سجلات جرد مرتبطة به')
            return
        confirm = QMessageBox.question(self, 'تأكيد', 'هل تريد حذف الصنف المحدد؟')
        if confirm == QMessageBox.Yes:
            try:
                self.db_manager.delete_item(item_id)
                self.refresh_table()
            except Exception as exc:
                QMessageBox.critical(self, 'خطأ', f'تعذر حذف الصنف:\n{exc}')