# init_db.py
import sqlite3

conn = sqlite3.connect('chat.db')
c = conn.cursor()

# conversation table
c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,       -- 'user' or 'bot'
    text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print("Initialized chat.db")
