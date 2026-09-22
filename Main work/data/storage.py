import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

#Making sure data storage
DB_PATH = Path(__file__).parent / "ridgeline.db"

@dataclass
class Listing:
    address: str
    email: str
    latitude: float
    longitude: float
    description: str = ""
    acreage: Optional[float] = None
    id: Optional[int] = field(default=None)
 
 
