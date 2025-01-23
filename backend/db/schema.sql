-- games table to store game metadata
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    executable_path TEXT NOT NULL,
    cover_art_path TEXT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- settings table (optional, for app settings)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
