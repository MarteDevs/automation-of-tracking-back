from fpdf import FPDF
import tempfile
import os
from collections import defaultdict
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
    tipo = getattr(avance, 'tipo_periodo', 'SEMANA')
    label = 'Nro Dia' if tipo == 'DIA' else 'Nro Semana'
    pdf.cell(60, 8, f' {label} {avance.semana}', border=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Avance Fisico:', border=1)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 102, 51) # Green
    pdf.cell(0, 8, f' {avance.porcentaje_avance} %', border=1, ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Fecha Fin:', border=1)
    pdf.set_font('Arial', '', 10)
    fecha_val = getattr(avance, 'fecha_fin', '')
    pdf.cell(60, 8, f' {fecha_val if fecha_val else "No Registrada"}', border=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Dias Trabajados:', border=1)
    pdf.set_font('Arial', '', 10)
    dias_val = getattr(avance, 'dias_trabajados', 0)
    dias_text = str(dias_val) if dias_val is not None else '0'
    pdf.cell(0, 8, f' {dias_text}', border=1, ln=True)
    
    pdf.ln(10)
    
    # Resumen de IA
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' 3. RESUMEN EJECUTIVO', ln=True)
    
    # Texto de IA
    pdf.set_fill_color(242, 242, 242) # Gris claro
    pdf.set_font('Arial', 'I', 10)
    txt_ia_safe = texto_ai.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, txt_ia_safe, border=1, fill=True, align='J')
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
        rutas = [r.strip() for r in avance.rutas_fotografias.split(',') if r.strip()]
        pdf.multi_cell(0, 6, f"Se han adjuntado {len(rutas)} fotografias tecnicas en este reporte.")
        pdf.ln(5)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Configuración del grid adaptativo
        IMG_W = 88          # ancho de cada imagen en mm
        IMG_H = 75          # alto máximo reservado por fila
        MARGIN_LEFT = 10    # margen izquierdo
        COL_GAP = 7         # separación entre columnas
        PAGE_BOTTOM = 270   # límite inferior (A4 = 297mm, margen inferior ~27mm)
        
        valid_images = []
        for foto in rutas:
            foto_safe = foto.encode('latin-1', 'replace').decode('latin-1').strip()
            img_path = os.path.join(base_dir, foto_safe.replace('/', os.sep))
            if os.path.exists(img_path):
                valid_images.append(img_path)
        
        # Insertar de a pares (2 columnas)
        for i in range(0, len(valid_images), 2):
            pair = valid_images[i:i+2]
            
            # Verificar si hay espacio para esta fila; si no, nueva página
            if pdf.get_y() + IMG_H > PAGE_BOTTOM:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 10)
                pdf.set_fill_color(220, 230, 241)
                pdf.cell(0, 7, ' (continuacion - Evidencia Fotografica)', border=1, ln=True, fill=True)
                pdf.ln(4)
            
            row_y = pdf.get_y()
            
            for j, img_path in enumerate(pair):
                x_coord = MARGIN_LEFT + j * (IMG_W + COL_GAP)
                try:
                    pdf.image(img_path, x=x_coord, y=row_y, w=IMG_W, h=0)  # h=0 = mantener proporción
                except Exception as e:
                    # Si la imagen falla, colocar un placeholder de texto
                    pdf.set_xy(x_coord, row_y)
                    pdf.set_text_color(200, 0, 0)
                    pdf.multi_cell(IMG_W, 6, f"(Error imagen {i+j+1}: {str(e)[:40]})")
                    pdf.set_text_color(0, 0, 0)
            
            # Avanzar cursor Y al final de esta fila
            pdf.set_y(row_y + IMG_H + 5)
        
        pdf.ln(5)
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
        
    pdf.ln(5)
    tipo_duracion_str = "Días" if getattr(proyecto, 'tipo_duracion', 'SEMANAS') == "DIAS" else "Semanas"
    porcentaje_actual = avance.porcentaje_avance
    porcentaje_faltante = max(0, 100.0 - porcentaje_actual)

    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 8, "RESUMEN ESTRATEGICO DE PROGRESO DE OBRA", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Dibujar Tabla de Progreso
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(140, 8, ' Indicador de Gestion Física', border=1, fill=True)
    pdf.cell(50, 8, ' Valor Reportado', align='C', border=1, fill=True, ln=True)
    
    pdf.set_font('Arial', '', 9)
    pdf.cell(140, 7, ' Progreso Fisico Total Acumulado (Ejecutado)', border=1)
    pdf.cell(50, 7, f' {porcentaje_actual}%', align='C', border=1, ln=True)
    
    pdf.cell(140, 7, ' Saldo Pendiente por Ejecutar (Brecha)', border=1)
    pdf.cell(50, 7, f' {porcentaje_faltante}%', align='C', border=1, ln=True)
    
    pdf.cell(140, 7, ' Cronograma Total General Programado', border=1)
    pdf.cell(50, 7, f' {proyecto.semanas_estimadas} {tipo_duracion_str}', align='C', border=1, ln=True)
    
    if getattr(avance, 'dias_trabajados', 0) > 0:
        pdf.cell(140, 7, ' Fuerza Laboral Invertida en este Periodo', border=1)
        pdf.cell(50, 7, f' {avance.dias_trabajados} dias netos', align='C', border=1, ln=True)
        
    pdf.ln(3)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, f"(*) La Curva Logistica S programada es proyectada matematicamente asumiendo las {proyecto.semanas_estimadas} {tipo_duracion_str} estimadas según la base inicial.")
                         
    # ------------------ PÁGINA 3: ANEXO DE COSTOS FIJOS ---------------- #
    if proyecto.mano_de_obra:
        pdf.add_page()
        pdf.set_text_color(0, 51, 102)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ANEXO II: REPORTE CONSOLIDADO DE COSTOS FIJOS', ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        grupos_fijos = defaultdict(list)
        for ob in proyecto.mano_de_obra:
            cat = getattr(ob, 'categoria', '') or 'Mano de Obra'
            cat = cat.strip().upper()
            grupos_fijos[cat].append(ob)
            
        for cat, items in grupos_fijos.items():
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, f'  CATEGORIA: {cat}', border=1, fill=True, ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(220, 230, 241)
            pdf.cell(90, 8, ' Descripcion / Rubro', border=1, fill=True)
            pdf.cell(15, 8, ' Und.', align='C', border=1, fill=True)
            pdf.cell(20, 8, ' Cant.', align='C', border=1, fill=True)
            pdf.cell(20, 8, ' P.Unit', align='C', border=1, fill=True)
            pdf.cell(15, 8, ' Dias', align='C', border=1, fill=True)
            pdf.cell(30, 8, ' Total S/.', align='R', border=1, fill=True, ln=True)
            
            subtotal_cat = 0.0
            pdf.set_font('Arial', '', 8)
            for ob in items:
                desc_safe = ob.descripcion.encode('latin-1', 'replace').decode('latin-1')
                if len(desc_safe) > 55: desc_safe = desc_safe[:52] + "..."
                     
                pdf.cell(90, 7, f' {desc_safe}', border=1)
                pdf.cell(15, 7, f" {getattr(ob, 'unidad', '') or '-'}", align='C', border=1)
                pdf.cell(20, 7, f" {ob.cantidad_trabajadores}", align='C', border=1)
                pdf.cell(20, 7, f" {getattr(ob, 'precio_unitario', 0.0):.2f}", align='C', border=1)
                pdf.cell(15, 7, f" {getattr(ob, 'dias', 1.0)}", align='C', border=1)
                pdf.cell(30, 7, f" {ob.total:.2f}", align='R', border=1, ln=True)
                subtotal_cat += ob.total
                
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(160, 7, f' SUBTOTAL {cat}:', align='R', border=1, fill=True)
            pdf.cell(30, 7, f' S/ {subtotal_cat:.2f}', align='R', border=1, fill=True, ln=True)
            pdf.ln(4)

    # ------------------ PÁGINA 4: ANEXO DE COSTOS VARIABLES ---------------- #
    if proyecto.materiales:
        pdf.add_page()
        pdf.set_text_color(0, 51, 102)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ANEXO III: REPORTE CONSOLIDADO DE COSTOS VARIABLES', ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        grupos_vars = defaultdict(list)
        for mat in proyecto.materiales:
            cat = getattr(mat, 'categoria', '') or 'Materiales'
            cat = cat.strip().upper()
            grupos_vars[cat].append(mat)
            
        for cat, items in grupos_vars.items():
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, f'  CATEGORIA: {cat}', border=1, fill=True, ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(220, 230, 241)
            pdf.cell(90, 8, ' Descripcion / Insumo', border=1, fill=True)
            pdf.cell(15, 8, ' Und.', align='C', border=1, fill=True)
            pdf.cell(20, 8, ' Cant.', align='C', border=1, fill=True)
            pdf.cell(20, 8, ' P.Unit', align='C', border=1, fill=True)
            pdf.cell(15, 8, ' Dias', align='C', border=1, fill=True)
            pdf.cell(30, 8, ' Total S/.', align='R', border=1, fill=True, ln=True)
            
            subtotal_cat = 0.0
            pdf.set_font('Arial', '', 8)
            for mat in items:
                desc_safe = mat.descripcion.encode('latin-1', 'replace').decode('latin-1')
                if len(desc_safe) > 55: desc_safe = desc_safe[:52] + "..."
                     
                pdf.cell(90, 7, f' {desc_safe}', border=1)
                pdf.cell(15, 7, f" {getattr(mat, 'unidad', '') or '-'}", align='C', border=1)
                pdf.cell(20, 7, f" {mat.cantidad}", align='C', border=1)
                pdf.cell(20, 7, f" {getattr(mat, 'precio_unitario', 0.0):.2f}", align='C', border=1)
                pdf.cell(15, 7, f" {getattr(mat, 'dias', 1.0)}", align='C', border=1)
                pdf.cell(30, 7, f" {mat.total:.2f}", align='R', border=1, ln=True)
                subtotal_cat += mat.total

            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(160, 7, f' SUBTOTAL {cat}:', align='R', border=1, fill=True)
            pdf.cell(30, 7, f' S/ {subtotal_cat:.2f}', align='R', border=1, fill=True, ln=True)
            pdf.ln(4)

    # ------------------ PÁGINA 5: PRESUPUESTO RESUMEN ---------------- #
    pdf.add_page()
    pdf.set_text_color(0, 51, 102)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'ANEXO IV: PRESUPUESTO RESUMEN DEL PROYECTO', ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # Cálculos Financieros
    costo_mo = sum(mo.total for mo in getattr(proyecto, 'mano_de_obra', []))
    costo_mat = sum(mat.total for mat in getattr(proyecto, 'materiales', []))
    costo_directo = costo_mo + costo_mat
    
    gastos_generales = costo_directo * 0.10
    utilidad_porc = (proyecto.utilidad_porcentaje / 100.0) if proyecto.utilidad_porcentaje else 0.15
    utilidad_moneda = costo_directo * utilidad_porc
    subtotal = costo_directo + gastos_generales + utilidad_moneda
    igv = subtotal * 0.18
    presupuesto_total = subtotal + igv
    
    # Dibujar Tabla Centrada
    pdf.set_x(35)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(70, 10, ' COSTO DIRECTO', border=1)
    pdf.cell(50, 10, f' S/ {costo_directo:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_font('Arial', '', 10)
    pdf.cell(70, 10, ' GASTOS GENERALES (10%)', border=1)
    pdf.cell(50, 10, f' S/ {gastos_generales:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.cell(70, 10, f' UTILIDAD ({(utilidad_porc * 100):.0f}%)', border=1)
    pdf.cell(50, 10, f' S/ {utilidad_moneda:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(70, 10, ' SUBTOTAL', border=1)
    pdf.cell(50, 10, f' S/ {subtotal:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_font('Arial', '', 10)
    pdf.cell(70, 10, ' IGV (18%)', border=1)
    pdf.cell(50, 10, f' S/ {igv:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(70, 12, ' PRESUPUESTO TOTAL DEL PROYECTO', border=1, fill=True)
    pdf.cell(50, 12, f' S/ {presupuesto_total:,.2f}', border=1, align='R', fill=True, ln=True)

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
