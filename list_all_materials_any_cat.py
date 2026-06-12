import sqlite3

def check():
    conn = sqlite3.connect("control_soldadura.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, descripcion, categoria, cantidad, precio_unitario, total FROM materiales_equipos WHERE proyecto_id=1")
    rows = cursor.fetchall()
    print(f"Total materials in database for Project 1: {len(rows)}")
    for r in rows:
        print(f"ID: {r[0]} | Desc: {r[1]:45} | Cat: {r[2]:30} | Cant: {r[3]} | P.U: {r[4]} | Total: {r[5]}")
    conn.close()

if __name__ == "__main__":
    check()
