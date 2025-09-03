import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from database.db_manager import DBManager
from ui.items_dialog import ItemsDialog
from ui.inventory_dialog import InventoryDialog
from ui.reports_dialog import ReportsDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('نظام الجرد الشهري لمصنع الذهب')

        self.db_manager = DBManager()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        central_widget.setLayout(layout)

        title = QLabel('لوحة التحكم')
        title.setAlignment(Qt.AlignRight)
        title.setStyleSheet('font-size:18px; font-weight:bold;')
        layout.addWidget(title)

        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        self.btn_items = QPushButton('إدارة الأصناف')
        self.btn_inventory = QPushButton('إدخال الجرد الشهري')
        self.btn_reports = QPushButton('التقارير والمقارنات')
        self.btn_exit = QPushButton('خروج')

        buttons_layout.addWidget(self.btn_items)
        buttons_layout.addWidget(self.btn_inventory)
        buttons_layout.addWidget(self.btn_reports)
        buttons_layout.addWidget(self.btn_exit)

        self.btn_items.clicked.connect(self.open_items)
        self.btn_inventory.clicked.connect(self.open_inventory)
        self.btn_reports.clicked.connect(self.open_reports)
        self.btn_exit.clicked.connect(self.close)

        self.items_dialog = None
        self.inventory_dialog = None
        self.reports_dialog = None

    def open_items(self) -> None:
        if self.items_dialog is None:
            self.items_dialog = ItemsDialog(self.db_manager, self)
        self.items_dialog.refresh_table()
        self.items_dialog.show()
        self.items_dialog.raise_()
        self.items_dialog.activateWindow()

    def open_inventory(self) -> None:
        if self.inventory_dialog is None:
            self.inventory_dialog = InventoryDialog(self.db_manager, self)
        self.inventory_dialog.load_items()
        self.inventory_dialog.show()
        self.inventory_dialog.raise_()
        self.inventory_dialog.activateWindow()

    def open_reports(self) -> None:
        if self.reports_dialog is None:
            self.reports_dialog = ReportsDialog(self.db_manager, self)
        self.reports_dialog.refresh_report()
        self.reports_dialog.show()
        self.reports_dialog.raise_()
        self.reports_dialog.activateWindow()