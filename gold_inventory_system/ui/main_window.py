from __future__ import annotations

import os
import logging
from datetime import datetime

try:
    from PySide6 import QtWidgets, QtCore, QtGui  # type: ignore
except Exception:  # pragma: no cover
    from PyQt5 import QtWidgets, QtCore, QtGui  # type: ignore

from database.db_manager import DBManager


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, db_manager: DBManager) -> None:
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("نظام الجرد الشهري - مصنع الذهب")
        self.setLayoutDirection(QtCore.Qt.RightToLeft)

        self._build_ui()
        self._build_menu()
        self._build_toolbar()

        self.statusBar().showMessage("جاهز")

    # ---------------------- UI Building ----------------------
    def _build_ui(self) -> None:
        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)

        title = QtWidgets.QLabel("نظام الجرد الشهري لمصنع الذهب")
        title.setAlignment(QtCore.Qt.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)

        info = QtWidgets.QLabel(
            "مرحباً بك! استخدم القوائم العلوية لإدارة الأصناف والجرد والتقارير."
        )
        info.setAlignment(QtCore.Qt.AlignCenter)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(info)
        layout.addStretch(2)

        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        menubar.setLayoutDirection(QtCore.Qt.RightToLeft)

        # ملف
        file_menu = menubar.addMenu("ملف")

        act_backup = QtWidgets.QAction("نسخ احتياطي", self)
        act_backup.triggered.connect(self._on_backup)
        file_menu.addAction(act_backup)

        act_restore = QtWidgets.QAction("استعادة نسخة", self)
        act_restore.triggered.connect(self._on_restore)
        file_menu.addAction(act_restore)

        file_menu.addSeparator()

        act_exit = QtWidgets.QAction("خروج", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # إدارة
        mgmt_menu = menubar.addMenu("الإدارة")
        act_items = QtWidgets.QAction("إدارة الأصناف", self)
        act_items.triggered.connect(self._open_items_dialog)
        mgmt_menu.addAction(act_items)

        act_inventory = QtWidgets.QAction("إدخال الجرد الشهري", self)
        act_inventory.triggered.connect(self._open_inventory_dialog)
        mgmt_menu.addAction(act_inventory)

        # تقارير
        reports_menu = menubar.addMenu("التقارير")
        act_reports = QtWidgets.QAction("تقرير المقارنة الشهري", self)
        act_reports.triggered.connect(self._open_reports_dialog)
        reports_menu.addAction(act_reports)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("main")
        toolbar.setMovable(False)

        btn_items = QtWidgets.QAction("الأصناف", self)
        btn_items.triggered.connect(self._open_items_dialog)
        toolbar.addAction(btn_items)

        btn_inventory = QtWidgets.QAction("الجرد", self)
        btn_inventory.triggered.connect(self._open_inventory_dialog)
        toolbar.addAction(btn_inventory)

        btn_reports = QtWidgets.QAction("التقارير", self)
        btn_reports.triggered.connect(self._open_reports_dialog)
        toolbar.addAction(btn_reports)

    # ---------------------- Slots / Actions ----------------------
    def _open_items_dialog(self) -> None:
        try:
            from ui.items_dialog import ItemsDialog

            dlg = ItemsDialog(self.db, self)
            dlg.exec()
        except AttributeError:
            # PyQt5 compatibility
            dlg = ItemsDialog(self.db, self)
            dlg.exec_()
        except Exception as exc:
            logging.getLogger(__name__).exception("فشل فتح شاشة الأصناف: %s", exc)
            QtWidgets.QMessageBox.critical(self, "خطأ", "فشل فتح شاشة الأصناف")

    def _open_inventory_dialog(self) -> None:
        try:
            from ui.inventory_dialog import InventoryDialog

            dlg = InventoryDialog(self.db, self)
            dlg.exec()
        except AttributeError:
            dlg = InventoryDialog(self.db, self)
            dlg.exec_()
        except Exception as exc:
            logging.getLogger(__name__).exception("فشل فتح شاشة الجرد: %s", exc)
            QtWidgets.QMessageBox.critical(self, "خطأ", "فشل فتح شاشة الجرد")

    def _open_reports_dialog(self) -> None:
        try:
            from ui.reports_dialog import ReportsDialog

            dlg = ReportsDialog(self.db, self)
            dlg.exec()
        except AttributeError:
            dlg = ReportsDialog(self.db, self)
            dlg.exec_()
        except Exception as exc:
            logging.getLogger(__name__).exception("فشل فتح شاشة التقارير: %s", exc)
            QtWidgets.QMessageBox.critical(self, "خطأ", "فشل فتح شاشة التقارير")

    def _on_backup(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "اختر مجلد النسخ الاحتياطي"
        )
        if not directory:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(directory, f"gold_inventory_backup_{timestamp}.db")
        try:
            self.db.backup_db(dest)
            self.statusBar().showMessage("تم إنشاء النسخة الاحتياطية بنجاح", 5000)
            QtWidgets.QMessageBox.information(
                self, "نجاح", f"تم حفظ النسخة الاحتياطية في:\n{dest}"
            )
        except Exception as exc:
            logging.getLogger(__name__).exception("Backup failed: %s", exc)
            QtWidgets.QMessageBox.critical(self, "خطأ", "فشل إنشاء النسخة الاحتياطية")

    def _on_restore(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "اختر ملف النسخة الاحتياطية", filter="SQLite DB (*.db)"
        )
        if not file_path:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "تأكيد",
            "سيتم استبدال قاعدة البيانات الحالية. هل أنت متأكد؟",
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        try:
            self.db.restore_db(file_path)
            self.statusBar().showMessage("تم استعادة النسخة الاحتياطية", 5000)
            QtWidgets.QMessageBox.information(self, "نجاح", "تمت الاستعادة بنجاح")
        except Exception as exc:
            logging.getLogger(__name__).exception("Restore failed: %s", exc)
            QtWidgets.QMessageBox.critical(self, "خطأ", "فشل استعادة النسخة الاحتياطية")

