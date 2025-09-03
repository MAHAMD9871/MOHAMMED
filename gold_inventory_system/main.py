import os
import sys
import logging
from datetime import datetime

try:
    from PySide6 import QtWidgets, QtCore, QtGui  # type: ignore
except Exception:  # pragma: no cover - fallback to PyQt5 if PySide6 is unavailable
    from PyQt5 import QtWidgets, QtCore, QtGui  # type: ignore

from database.db_manager import DBManager


def configure_logging(app_dir: str) -> None:
    logs_dir = os.path.join(app_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "app.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def load_stylesheet(app_dir: str) -> str:
    resources_dir = os.path.join(app_dir, "resources")
    qss_path = os.path.join(resources_dir, "styles.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to load stylesheet: %s", exc)
    return ""


def ensure_app_dirs(app_dir: str) -> None:
    for sub in ("resources", "backups", "logs"):
        os.makedirs(os.path.join(app_dir, sub), exist_ok=True)


def auto_backup(db: DBManager, app_dir: str) -> None:
    try:
        # Create one backup per day automatically on startup
        backups_dir = os.path.join(app_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        dest = os.path.join(backups_dir, f"auto_backup_{today_str}.db")
        if not os.path.exists(dest):
            db.backup_db(dest)
            logging.getLogger(__name__).info("Created automatic backup at %s", dest)
    except Exception as exc:
        logging.getLogger(__name__).error("Auto-backup failed: %s", exc)


def main() -> int:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    ensure_app_dirs(app_dir)
    configure_logging(app_dir)

    logging.info("Starting Gold Inventory System UI...")

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("نظام جرد الذهب")
    app.setOrganizationName("مصنع الذهب")
    app.setLayoutDirection(QtCore.Qt.RightToLeft)

    # Prefer an Arabic-friendly font if available
    default_font = QtGui.QFont("Noto Naskh Arabic", 10)
    app.setFont(default_font)

    # Load stylesheet
    qss = load_stylesheet(app_dir)
    if qss:
        app.setStyleSheet(qss)

    # Initialize database
    db = DBManager(app_dir)
    db.initialize_db()
    auto_backup(db, app_dir)

    # Import main window lazily to avoid circular imports
    from ui.main_window import MainWindow

    window = MainWindow(db_manager=db)
    window.resize(1100, 720)
    window.show()

    try:
        return app.exec()
    except AttributeError:
        # PyQt5 compatibility
        return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

