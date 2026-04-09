import matplotlib
matplotlib.use('Agg') # backend obligatorio para entornos multi-hilo como FastAPI sin interfaz de ventana (soluciona crash de tkinter)
import matplotlib.pyplot as plt
import numpy as np
import os
import tempfile

def generar_curva_s(avance_real_semanas, avance_real_porcentajes, semanas_estimadas, proyecto_nomb):
    plt.figure(figsize=(10, 5))
    
    # 1. Generar Curva S Teórica (Función Logística estándar)
    # Si semanas_estimadas <= 0, asumiremos 1 para no romper la matemática
    total_semanas = max(semanas_estimadas, 1)
    
    # Eje X ideal desde Semana 0 a N
    x_ideal = np.linspace(0, total_semanas, 100)
    
    # Ecuacion logística ajustable a la longitud del proyecto
    k = 8.0 / total_semanas  # Steepness proporcional al tiempo total
    x0 = total_semanas / 2.0 # Punto de inflexión en el medio de la obra
    
    y_ideal = 100 / (1 + np.exp(-k * (x_ideal - x0)))
    
    # Normalizar para que arranque en (0,0) exacto
    y_ideal_0 = 100 / (1 + np.exp(-k * (0 - x0)))
    y_ideal = (y_ideal - y_ideal_0) / (100 - y_ideal_0) * 100
    
    # Dibujar la curva S maestra (Planeado)
    plt.plot(x_ideal, y_ideal, '--', color='#1e3a8a', linewidth=2.5, label='Curva Logística S (Programado)')
    
    # 2. Generar Curva Real
    # Siempre empezamos por la semana 0 = 0% para todas las graficas de avance
    x_real = [0] + avance_real_semanas
    y_real = [0] + avance_real_porcentajes
    
    plt.plot(x_real, y_real, 'o-', color='#e11d48', linewidth=3, markersize=8, label='Avance Físico (Puntos Reales)')
    
    # Sombra para dar aspecto premium
    plt.fill_between(x_real, y_real, color='#e11d48', alpha=0.1)

    # 3. Configuraciones gráficas corporativas
    plt.title(f"CURVA DE CONTROL Y RENDIMIENTO (S-CURVE) - {proyecto_nomb}", fontsize=13, fontweight='bold', color='#1e293b')
    plt.xlabel("Cronología de Ejecución (Semanas)", fontsize=11, fontweight='bold')
    plt.ylabel("Progreso Físico Acumulado (%)", fontsize=11, fontweight='bold')
    
    # Topes del grafico
    tope_x = max(total_semanas, max(x_real) if x_real else 1)
    plt.xlim(0, tope_x + 0.5)
    plt.ylim(0, 105)
    
    # Reticula guiada
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc="lower right", fontsize=10)
    
    # Añadir valores exactos de % al lado de cada pico ejecutado
    for i, txt in enumerate(y_real):
        if i > 0: # Excluir el cero
            plt.annotate(f"{txt}%", (x_real[i], y_real[i]), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9, fontweight='bold', color='#e11d48')
            
    plt.tight_layout()
    
    # Generar Snapshot
    fd, temp_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    plt.savefig(temp_path, dpi=150, transparent=False, facecolor='#f8fafc')
    plt.close()
    
    return temp_path
