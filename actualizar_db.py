import sqlite3

def add_columns():
    conn = sqlite3.connect('control_soldadura.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE proyectos ADD COLUMN ruta_pdf TEXT")
        print("Agregado ruta_pdf a proyectos")
    except Exception as e:
        print(f"Nota: {e}")

    try:
        cursor.execute("ALTER TABLE avances_semanales ADD COLUMN ruta_pdf TEXT")
        print("Agregado ruta_pdf a avances_semanales")
    except Exception as e:
        print(f"Nota: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
