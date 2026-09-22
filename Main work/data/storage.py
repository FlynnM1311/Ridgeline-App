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
 
 
def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
 
def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                email TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                description TEXT,
                acreage REAL
            )
            """
        )
 
 def add_listing(listing: Listing) -> int:
    """Insert a new listing and return its id."""
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO listings (address, email, latitude, longitude, description, acreage)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                listing.address,
                listing.email,
                listing.latitude,
                listing.longitude,
                listing.description,
                listing.acreage,
            ),
        )
        return cur.lastrowid
 
 