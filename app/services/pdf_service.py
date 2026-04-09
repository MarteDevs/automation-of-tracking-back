from fpdf import FPDF
import tempfile
import os
from app.services.chart_service import generar_curva_s

def crear_pdf_avance(proyecto, avance, texto_ai):
    pdf = FPDF()
    pdf.add_page()
    
    # Colores corporativos base (Azul oscuro para los titulos)
    pdf.set_text_color(0, 51, 102)
    
    # Header del Documento
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'INFORME DEL PROCESO DE CONTROL DE AVANCES', ln=True, align='C')
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 5, 'Emitido por Sistema Inteligente Derek', ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0) # Black regular
    pdf.ln(10)
    
    # Información General (Usando celdas encuadradas tipo tabla)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(0, 8, ' 1. DATOS DEL PROYECTO', border=1, ln=True, fill=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Nombre Obra/Pry.:', border=1)
    pdf.set_font('Arial', '', 10)
    
    # Remover caracteres especiales que FPDF-Arial no lee directo
    nom_proyecto_safe = proyecto.nombre_proyecto.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 8, f' {nom_proyecto_safe}', border=1, ln=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Fecha Inicial:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 8, f' {proyecto.fecha}', border=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Costo / Prto:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f' {proyecto.costo_total} PEN', border=1, ln=True)
    
    pdf.ln(5)
    
    # Información del Avance
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' 2. SEGUIMIENTO SEMANAL', border=1, ln=True, fill=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Semana Registrada:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 8, f' Nro {avance.semana}', border=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Avance Fisico:', border=1)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 102, 51) # Green
    pdf.cell(0, 8, f' {avance.porcentaje_avance} %', border=1, ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(10)
    
    # Resumen de IA
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' 3. RESUMEN EJECUTIVO (Evaluacion IA)', ln=True)
    pdf.set_font('Arial', 'I', 10)
    
    # Texto de IA
    txt_ia_safe = texto_ai.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, txt_ia_safe)
    pdf.ln(10)
    
    # Observaciones Crudas
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' 4. OBSERVACIONES DE CAMPO', ln=True)
    pdf.set_font('Arial', '', 10)
    
    obs = str(avance.observaciones) if avance.observaciones else "Sin observaciones en esta jornada."
    obs_safe = obs.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, obs_safe)
    pdf.ln(10)
    
    # Fotografias / Evidencias
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' 5. EVIDENCIA FOTOGRAFICA', ln=True)
    pdf.set_font('Arial', '', 10)
    
    if avance.rutas_fotografias:
        rutas = avance.rutas_fotografias.split(',')
        pdf.multi_cell(0, 6, f"Se han adjuntado {len(rutas)} fotografías técnicas en este reporte.")
        pdf.ln(5)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        current_y = pdf.get_y()
        max_h = 0
        
        for idx, foto in enumerate(rutas):
            foto_safe = foto.encode('latin-1', 'replace').decode('latin-1').strip()
            img_path = os.path.join(base_dir, foto_safe.replace('/', os.sep))
            
            if os.path.exists(img_path):
                try:
                    if len(rutas) == 1:
                        # Para 1 foto, se inserta normalmente afectando el cursor Y, sin romper flujo
                        pdf.image(img_path, x=30, w=150)
                    else:
                        # Grid manual iterativo de 2x2. Maximo 4.
                        col_index = idx % 2
                        row_index = idx // 2
                        x_coord = 15 if col_index == 0 else 110
                        # Otorgamos 80 unidades de alto estimado para cada row para evitar overlap vertical
                        y_coord = current_y + (row_index * 80)
                        pdf.image(img_path, x=x_coord, y=y_coord, w=85)
                        max_h = max(max_h, (row_index + 1) * 80)
                except Exception as e:
                    pdf.set_y(current_y + 10)
                    pdf.set_text_color(255, 0, 0)
                    pdf.multi_cell(0, 6, f"(Error acoplando imagen {idx+1})")
                    pdf.set_text_color(0, 0, 0)
            else:
                 pdf.multi_cell(0, 6, f"(No se halló evidencia {idx+1} local)")
                 
        if len(rutas) > 1:
             pdf.set_y(current_y + max_h + 10)
    else:
        pdf.multi_cell(0, 6, "(No se insertaron imagenes fotograficas para esta semana).")
        
    

    # ------------------ PÁGINA 2: ANEXO DE CURVA S ------------------ #
    pdf.add_page()
    pdf.set_text_color(0, 51, 102)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'ANEXO I: ESTADISTICA DE CURVA "S" (PLAN VS REAL)', ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    try:
        # Extraer todo el historico de este proyecto (limitado hasta la semana de este reporte)
        todos_avances = sorted(proyecto.avances, key=lambda x: x.semana)
        semanas_x = [a.semana for a in todos_avances if a.semana <= avance.semana]
        porcentajes_y = [a.porcentaje_avance for a in todos_avances if a.semana <= avance.semana]
        
        # Generar PNG nativo
        sems = proyecto.semanas_estimadas or 1
        nomb = proyecto.nombre_proyecto.encode('latin-1', 'replace').decode('latin-1')
        grafico_rut = generar_curva_s(semanas_x, porcentajes_y, sems, nomb)
        
        # Pegar el PNG en el PDF
        pdf.image(grafico_rut, x=5, w=200)
        
        # Borrar el grafico temporal
        os.remove(grafico_rut)
        
    except Exception as e:
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0, 6, f"(Error generando Anexo Estadistico: {e})")
        pdf.set_text_color(0, 0, 0)
        
    pdf.ln(10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, f"(*) La Curva Logística S (Programada) es calculada asumiendo un avance de forma "
                         f"Normal y Logistica asintotica durante las {proyecto.semanas_estimadas} Semanas pronosticadas de ejecucion general.")
                         
    # ------------------ PÁGINA 3: ANEXO DE MATERIALES ---------------- #
    if proyecto.materiales:
        pdf.add_page()
        pdf.set_text_color(0, 51, 102)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ANEXO II: REPORTE CONSOLIDADO DE MATERIALES', ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Headers Tabla
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(220, 230, 241)
        pdf.cell(95, 8, ' Descripcion del Insumo', border=1, fill=True)
        pdf.cell(30, 8, ' Cantidad', align='C', border=1, fill=True)
        pdf.cell(25, 8, ' Unidad', align='C', border=1, fill=True)
        pdf.cell(40, 8, ' Costo Total Previsto', align='R', border=1, fill=True, ln=True)
        
        pdf.set_font('Arial', '', 9)
        for mat in proyecto.materiales:
            desc_safe = mat.descripcion.encode('latin-1', 'replace').decode('latin-1')
            # Acortar la descripcion si es muy larga para que no desborde la fila (limite ~50 chars para 95 pts)
            if len(desc_safe) > 52:
                 desc_safe = desc_safe[:49] + "..."
                 
            pdf.cell(95, 7, f' {desc_safe}', border=1)
            pdf.cell(30, 7, f' {mat.cantidad}', align='C', border=1)
            pdf.cell(25, 7, f' {mat.unidad}', align='C', border=1)
            pdf.cell(40, 7, f' S/ {mat.total}', align='R', border=1, ln=True)
            
    pdf.ln(25)
    
    # Firmas
    # Las firmas ahora estarán SIEMPRE obligatoriamente en la estructura final de todo el documento
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, '________________________', ln=True, align='C')
    pdf.cell(0, 5, 'Firma y Sello', ln=True, align='C')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, 'Ingeniero Responsable / Inspector', ln=True, align='C')
            
    # Guardar en archivo temporal seguro
    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    pdf.output(temp_path)
    return temp_path
