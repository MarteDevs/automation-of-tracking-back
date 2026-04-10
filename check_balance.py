import sqlite3

conn = sqlite3.connect('control_soldadura.db')
cursor = conn.cursor()

print('=== MATERIALES EN BD (categoria MATERIALES) ===')
cursor.execute("SELECT id, descripcion, cantidad, precio_unitario, total, categoria FROM materiales_equipos WHERE UPPER(categoria) LIKE '%MATERIALES%' LIMIT 20")
for m in cursor.fetchall():
    print(m)

print('\n=== CONSUMOS CON CALCULOS ===')
cursor.execute('SELECT nombre_material, cantidad_usada FROM consumos_materiales')
consumos = cursor.fetchall()
total_calc = 0.0
for nombre, cant in consumos:
    c2 = conn.cursor()
    c2.execute("SELECT precio_unitario FROM materiales_equipos WHERE descripcion=? AND UPPER(categoria) LIKE '%MATERIALES%'", (nombre,))
    row = c2.fetchone()
    precio = row[0] if row else None
    subtotal = cant * precio if precio is not None else 0
    total_calc += subtotal
    print(f'{nombre[:40]!r:42} | cant={cant} | precio={precio} | subtotal={subtotal}')

print(f'\nTotal gastado calculado: S/ {total_calc:.2f}')

print('\n=== TOTAL PRESUPUESTO MATERIALES ===')
cursor.execute("SELECT SUM(cantidad * precio_unitario) FROM materiales_equipos WHERE UPPER(categoria) LIKE '%MATERIALES%'")
ppto = cursor.fetchone()[0]
print(f'Total presupuesto materiales: S/ {ppto:.2f}')

conn.close()
