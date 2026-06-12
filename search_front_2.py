with open(r"d:\vps-program-proyects\control_soldadura\control_soldadura_front\src\views\DetalleProyectoView.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "totalMaterialesPorCategoria" in line:
        print(f"Line {idx+1}: {line.strip()}")
