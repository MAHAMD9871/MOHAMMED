import os
import sys
from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QApplication

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(CURRENT_DIR, 'resources')
STYLES_PATH = os.path.join(RES_DIR, 'styles.qss')


def load_stylesheet(app: QApplication) -> None:
    if os.path.exists(STYLES_PATH):
        try:
            with open(STYLES_PATH, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
        except Exception:
            pass


def main() -> None:
    app = QApplication(sys.argv)

    # Arabic UI and RTL
    QLocale.setDefault(QLocale(QLocale.Arabic, QLocale.Egypt))
    app.setLayoutDirection(Qt.RightToLeft)
    app.setApplicationDisplayName('نظام جرد الذهب')

    load_stylesheet(app)

    from ui.main_window import MainWindow
    window = MainWindow()
    window.resize(1100, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()