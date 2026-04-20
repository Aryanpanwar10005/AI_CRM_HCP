import sqlite3

def list_hcps():
    conn = sqlite3.connect('crm_hcp.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, specialty FROM hcps")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]} - {row[1]}")
    conn.close()

if __name__ == "__main__":
    list_hcps()
