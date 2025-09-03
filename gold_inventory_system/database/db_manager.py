import os
import shutil
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class DBManager:
    """SQLite database manager for gold inventory system."""

    def __init__(self, app_dir: str) -> None:
        self.app_dir = app_dir
        self.db_path = os.path.join(self.app_dir, "gold_inventory.db")

    # ----------------------
    # Core / Connections
    # ----------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_db(self) -> None:
        os.makedirs(self.app_dir, exist_ok=True)
        with self._connect() as conn:
            cur = conn.cursor()
            # Items table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    unit TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                """
            )
            # Inventory table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    quantity REAL NOT NULL CHECK (quantity >= 0),
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    UNIQUE(item_id, year, month),
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                );
                """
            )
            conn.commit()

    # ----------------------
    # Items CRUD
    # ----------------------
    def list_items(self, search_text: str = "") -> List[sqlite3.Row]:
        sql = "SELECT id, name, unit, created_at FROM items"
        params: Tuple[object, ...] = tuple()
        if search_text:
            sql += " WHERE name LIKE ? OR unit LIKE ?"
            like = f"%{search_text}%"
            params = (like, like)
        sql += " ORDER BY name COLLATE NOCASE ASC"
        with self._connect() as conn:
            return list(conn.execute(sql, params))

    def add_item(self, name: str, unit: str) -> int:
        name = (name or "").strip()
        unit = (unit or "").strip()
        if not name or not unit:
            raise ValueError("يجب إدخال اسم الصنف ووحدة القياس")
        with self._connect() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO items (name, unit) VALUES (?, ?)", (name, unit)
                )
                conn.commit()
                return int(cur.lastrowid)
            except sqlite3.IntegrityError:
                raise ValueError("الصنف موجود مسبقاً")

    def update_item(self, item_id: int, name: str, unit: str) -> None:
        name = (name or "").strip()
        unit = (unit or "").strip()
        if not name or not unit:
            raise ValueError("يجب إدخال اسم الصنف ووحدة القياس")
        with self._connect() as conn:
            try:
                conn.execute(
                    "UPDATE items SET name = ?, unit = ? WHERE id = ?",
                    (name, unit, item_id),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError("اسم الصنف مستخدم بالفعل")

    def delete_item(self, item_id: int) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COUNT(1) AS cnt FROM inventory WHERE item_id = ?",
                (item_id,),
            )
            if int(cur.fetchone()[0]) > 0:
                raise ValueError("لا يمكن حذف الصنف لوجود حركات جرد مرتبطة به")
            conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()

    # ----------------------
    # Inventory Operations
    # ----------------------
    def get_inventory_map(self, year: int, month: int) -> Dict[int, float]:
        """Return a mapping of item_id -> quantity for the given month."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT item_id, quantity FROM inventory WHERE year = ? AND month = ?",
                (year, month),
            ).fetchall()
            return {int(r[0]): float(r[1]) for r in rows}

    def upsert_inventory_bulk(
        self, year: int, month: int, entries: List[Tuple[int, float, Optional[str]]]
    ) -> None:
        """Insert or update inventory quantities for a month.

        entries: list of tuples (item_id, quantity, notes)
        """
        # Validate
        for _, qty, _ in entries:
            if qty is None or qty < 0:
                raise ValueError("القيم المدخلة يجب أن تكون أرقاماً موجبة أو صفراً")

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO inventory (item_id, year, month, quantity, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(item_id, year, month)
                DO UPDATE SET quantity = excluded.quantity, notes = excluded.notes
                """,
                [(i, year, month, float(q), n) for (i, q, n) in entries],
            )
            conn.commit()

    # ----------------------
    # Reporting
    # ----------------------
    def _prev_year_month(self, year: int, month: int) -> Tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    def get_monthly_comparison(
        self, year: int, month: int
    ) -> List[Dict[str, object]]:
        prev_year, prev_month = self._prev_year_month(year, month)
        with self._connect() as conn:
            sql = """
                SELECT
                    it.id AS item_id,
                    it.name AS item_name,
                    it.unit AS unit,
                    COALESCE(cur.quantity, 0) AS current_qty,
                    COALESCE(prev.quantity, 0) AS previous_qty
                FROM items it
                LEFT JOIN inventory cur
                    ON cur.item_id = it.id AND cur.year = ? AND cur.month = ?
                LEFT JOIN inventory prev
                    ON prev.item_id = it.id AND prev.year = ? AND prev.month = ?
                ORDER BY it.name COLLATE NOCASE ASC
            """
            rows = conn.execute(sql, (year, month, prev_year, prev_month)).fetchall()
            result: List[Dict[str, object]] = []
            for r in rows:
                current_qty = float(r["current_qty"]) if r["current_qty"] is not None else 0.0
                previous_qty = float(r["previous_qty"]) if r["previous_qty"] is not None else 0.0
                diff = current_qty - previous_qty
                result.append(
                    {
                        "item_id": int(r["item_id"]),
                        "item_name": str(r["item_name"]),
                        "unit": str(r["unit"]),
                        "current_qty": current_qty,
                        "previous_qty": previous_qty,
                        "diff": diff,
                    }
                )
            return result

    # ----------------------
    # Backup / Restore
    # ----------------------
    def backup_db(self, destination_path: str) -> None:
        """Create a backup copy of the SQLite database to destination_path."""
        # Ensure DB file exists
        if not os.path.exists(self.db_path):
            # Initialize if missing
            self.initialize_db()
        os.makedirs(os.path.dirname(destination_path) or ".", exist_ok=True)
        # Use SQLite's backup API for consistency if possible
        try:
            with self._connect() as src_conn:
                dst_conn = sqlite3.connect(destination_path)
                with dst_conn:
                    src_conn.backup(dst_conn)
                dst_conn.close()
        except Exception:
            shutil.copy2(self.db_path, destination_path)

    def restore_db(self, source_path: str) -> None:
        """Restore database from source_path (overwrites current DB)."""
        if not os.path.exists(source_path):
            raise FileNotFoundError("ملف النسخة الاحتياطية غير موجود")
        # Copy over the existing database
        shutil.copy2(source_path, self.db_path)
        # Touch the DB to ensure it's valid
        with self._connect() as conn:
            conn.execute("PRAGMA integrity_check;")
            conn.commit()

