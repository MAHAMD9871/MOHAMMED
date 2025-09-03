from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    id: int
    name: str
    unit: str
    created_at: str


@dataclass
class InventoryEntry:
    id: int
    item_id: int
    year: int
    month: int
    quantity: float
    notes: Optional[str]
    created_at: str