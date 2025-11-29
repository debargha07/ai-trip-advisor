# database_setup.py
import sqlite3

conn = sqlite3.connect('tripadvisor.db')
c = conn.cursor()

# users
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
''')

# destinations
c.execute('''
CREATE TABLE IF NOT EXISTS destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    country TEXT,
    description TEXT
);
''')

# attractions
c.execute('''
CREATE TABLE IF NOT EXISTS attractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER,
    name TEXT,
    category TEXT,
    description TEXT,
    FOREIGN KEY(destination_id) REFERENCES destinations(id)
);
''')

# hotels
c.execute('''
CREATE TABLE IF NOT EXISTS hotels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER,
    name TEXT,
    rating REAL,
    price_per_night INTEGER,
    availability INTEGER,
    details TEXT,
    FOREIGN KEY(destination_id) REFERENCES destinations(id)
);
''')

# bookings
c.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    booking_type TEXT,
    item_id INTEGER,
    start_date TEXT,
    end_date TEXT,
    amount INTEGER,
    status TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
''')

conn.commit()
conn.close()
print("Database created: tripadvisor.db")
