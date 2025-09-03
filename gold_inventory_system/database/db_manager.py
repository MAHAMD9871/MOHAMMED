import os
import sqlite3
import shutil
import logging
from datetime import datetime
from typing import List, Optional, Dict, Tuple

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_ROOT, 'data')
BACKUP_DIR = os.path.join(APP_ROOT, 'backups')
LOGS_DIR = os.path.join(APP_ROOT, 'logs')
EXPORTS_DIR = os.path.join(APP_ROOT, 'exports')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, 'app.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

DB_PATH = os.path.join(DATA_DIR, 'gold_inventory.db')


class DBManager:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _ensure_db(self) -> None:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    '''CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        unit TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )'''
                )
                cur.execute(
                    '''CREATE TABLE IF NOT EXISTS inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        month INTEGER NOT NULL,
                        quantity REAL NOT NULL CHECK (quantity >= 0),
                        notes TEXT,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(item_id, year, month),
                        FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT
                    )'''
                )
                conn.commit()
        except Exception as exc:
            logging.exception('Failed to ensure database: %s', exc)
            raise

    def backup_database(self) -> str:
        if not os.path.exists(self.db_path):
            return ''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'gold_inventory_{timestamp}.db'
        dst = os.path.join(BACKUP_DIR, backup_name)
        try:
            shutil.copy2(self.db_path, dst)
            logging.info('Database backup created at %s', dst)
        except Exception as exc:
            logging.exception('Failed to backup database: %s', exc)
        return dst

    def add_item(self, name: str, unit: str) -> int:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO items(name, unit) VALUES (?, ?)', (name.strip(), unit.strip()))
                conn.commit()
                item_id = cur.lastrowid
                self.backup_database()
                return item_id
        except sqlite3.IntegrityError as exc:
            logging.warning('Integrity error adding item %s: %s', name, exc)
            raise
        except Exception as exc:
            logging.exception('Error adding item: %s', exc)
            raise

    def update_item(self, item_id: int, name: str, unit: str) -> None:
        try:
            with self._connect() as conn:
                conn.execute('UPDATE items SET name = ?, unit = ? WHERE id = ?', (name.strip(), unit.strip(), item_id))
                conn.commit()
                self.backup_database()
        except sqlite3.IntegrityError as exc:
            logging.warning('Integrity error updating item %s: %s', item_id, exc)
            raise
        except Exception as exc:
            logging.exception('Error updating item: %s', exc)
            raise

    def can_delete_item(self, item_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute('SELECT COUNT(1) AS c FROM inventory WHERE item_id = ?', (item_id,))
            row = cur.fetchone()
            return (row['c'] or 0) == 0

    def delete_item(self, item_id: int) -> None:
        if not self.can_delete_item(item_id):
            raise ValueError('لا يمكن حذف الصنف لوجود سجلات جرد مرتبطة به')
        try:
            with self._connect() as conn:
                conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
                conn.commit()
                self.backup_database()
        except Exception as exc:
            logging.exception('Error deleting item: %s', exc)
            raise

    def list_items(self, search: str = '') -> List[sqlite3.Row]:
        query = 'SELECT id, name, unit, created_at FROM items'
        params: Tuple = ()
        if search.strip():
            query += ' WHERE name LIKE ?'
            params = (f'%{search.strip()}%',)
        query += ' ORDER BY name'
        with self._connect() as conn:
            cur = conn.execute(query, params)
            return cur.fetchall()

    def set_inventory_for_month(self, year: int, month: int, items_quantities: List[Tuple[int, float]], notes: Optional[str] = None) -> None:
        if not (1 <= month <= 12):
            raise ValueError('Month must be in 1..12')
        try:
            with self._connect() as conn:
                for item_id, qty in items_quantities:
                    if qty is None:
                        continue
                    if qty < 0:
                        raise ValueError('الكمية لا يمكن أن تكون سالبة')
                    conn.execute(
                        '''INSERT INTO inventory(item_id, year, month, quantity, notes)
                           VALUES (?, ?, ?, ?, ?)
                           ON CONFLICT(item_id, year, month)
                           DO UPDATE SET quantity = excluded.quantity, notes = excluded.notes, created_at = CURRENT_TIMESTAMP''',
                        (item_id, year, month, qty, notes)
                    )
                conn.commit()
                self.backup_database()
        except Exception as exc:
            logging.exception('Error setting inventory for %04d-%02d: %s', year, month, exc)
            raise

    def get_inventory_for_month(self, year: int, month: int) -> Dict[int, float]:
        with self._connect() as conn:
            cur = conn.execute(
                '''SELECT item_id, quantity FROM inventory WHERE year = ? AND month = ?''',
                (year, month)
            )
            result: Dict[int, float] = {}
            for row in cur.fetchall():
                result[int(row['item_id'])] = float(row['quantity'])
            return result

    def get_monthly_comparison(self, year: int, month: int) -> List[Dict[str, object]]:
        prev_year = year if month > 1 else year - 1
        prev_month = month - 1 if month > 1 else 12
        with self._connect() as conn:
            cur = conn.execute('SELECT id, name, unit FROM items ORDER BY name')
            items = cur.fetchall()
            current = self.get_inventory_for_month(year, month)
            previous = self.get_inventory_for_month(prev_year, prev_month)

            rows: List[Dict[str, object]] = []
            for item in items:
                item_id = int(item['id'])
                name = str(item['name'])
                unit = str(item['unit'])
                qty_curr = float(current.get(item_id, 0.0))
                qty_prev = float(previous.get(item_id, 0.0))
                diff = qty_curr - qty_prev
                rows.append({
                    'item_id': item_id,
                    'name': name,
                    'unit': unit,
                    'qty_curr': qty_curr,
                    'qty_prev': qty_prev,
                    'diff': diff,
                    'year': year,
                    'month': month,
                    'prev_year': prev_year,
                    'prev_month': prev_month,
                })
            return rows