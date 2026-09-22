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
    with _connect() as conn:
        cur = conn.execute(
,
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
 
 
 
def get_all_listings() -> list[Listing]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM listings").fetchall()
        return [
            Listing(
                id=row["id"],
                address=row["address"],
                email=row["email"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                description=row["description"] or "",
                acreage=row["acreage"],
            )
            for row in rows
        ]
 
 
def delete_listing(listing_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))