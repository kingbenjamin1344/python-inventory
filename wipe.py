import sqlite3

conn = sqlite3.connect("data/inventory.db")
conn.execute("DELETE FROM counts")
conn.execute("DELETE FROM reconciliations")
conn.commit()
conn.close()
print("Both tables cleared")