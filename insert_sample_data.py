# insert_sample_data.py
import sqlite3

conn = sqlite3.connect('tripadvisor.db')
c = conn.cursor()

# Sample destinations
c.executemany('INSERT INTO destinations (city, country, description) VALUES (?, ?, ?)', [
    ('Goa', 'India', 'Beaches, seafood, nightlife and Portuguese heritage.'),
    ('Manali', 'India', 'Himalayan hill station, trekking and nature.'),
    ('Varanasi', 'India', 'Spiritual city on the Ganges, temples and ghats.'),
])

# Attractions (destination_id 1 -> Goa, 2 -> Manali, 3 -> Varanasi)
c.executemany('INSERT INTO attractions (destination_id, name, category, description) VALUES (?, ?, ?, ?)', [
    (1, 'Baga Beach', 'Beach', 'Popular beach with water sports and shacks.'),
    (1, 'Fort Aguada', 'Historical', '17th-century Portuguese fort with lighthouse.'),
    (2, 'Solang Valley', 'Nature', 'Adventure sports, paragliding and snow activities.'),
    (2, 'Hadimba Temple', 'Cultural', 'Ancient wooden temple in scenic forest.'),
    (3, 'Dashashwamedh Ghat', 'Cultural', 'Main ghat with evening aarti ceremonies.'),
    (3, 'Kashi Vishwanath Temple', 'Religious', 'One of the holiest Hindu temples.'),
])

# Hotels
c.executemany('INSERT INTO hotels (destination_id, name, rating, price_per_night, availability, details) VALUES (?, ?, ?, ?, ?, ?)', [
    (1, 'SeaView Resort', 4.2, 3500, 10, 'Close to beach, free breakfast.'),
    (1, 'Budget Inn Goa', 3.6, 1200, 20, 'Cheap rooms, good for backpackers.'),
    (2, 'Himalaya Stay', 4.5, 4200, 5, 'Mountain views and hot water.'),
    (3, 'Ganga Guest House', 4.0, 2000, 8, 'Near ghat, vegetarian meals.'),
])

conn.commit()
conn.close()
print("Sample data inserted.")
