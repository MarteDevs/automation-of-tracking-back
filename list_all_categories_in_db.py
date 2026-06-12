import sqlite3

def check():
    conn = sqlite3.connect("control_soldadura.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM materiales_equipos WHERE proyecto_id=1")
    cats = cursor.fetchall()
    print("=== ALL CATEGORIES IN DB ===")
    for c in cats:
        cursor.execute("SELECT COUNT(*), SUM(total) FROM materiales_equipos WHERE proyecto_id=1 AND categoria=?", (c[0],))
        cnt, tot = cursor.fetchone()
        print(f"Category: {c[0]!r} | Count: {cnt} | Sum Total: {tot}")
        
    print("\n=== LIST OF ALL ITEMS FOR ID 1 ===")
    cursor.execute("SELECT id, descripcion, categoria, total FROM materiales_equipos WHERE proyecto_id=1")
    for r in cursor.fetchall():
        if any(x in r[1].upper() for x in ["PETROLEO", "GASOLINA", "MEDICINA", "TOPICO"]):
            print(r)
            
    conn.close()

if __name__ == "__main__":
    check()
