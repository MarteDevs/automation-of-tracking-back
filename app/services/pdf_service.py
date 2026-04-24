from fpdf import FPDF
import tempfile
import os
from collections import defaultdict
from app.services.chart_service import generar_curva_s
from PIL import Image

def get_proportional_dimensions(img_path, max_w, max_h):
    try:
        with Image.open(img_path) as img:
            orig_w, orig_h = img.size
            if orig_w == 0 or orig_h == 0:
                return max_w, 0
            ratio = min(max_w / orig_w, max_h / orig_h)
            return orig_w * ratio, orig_h * ratio
    except Exception:
        return max_w, 0

def crear_pdf_avance(proyecto, avance, texto_ai, texto_balance_ia='', ppto_total_igv=0.0):
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
    
    costo_dir_temp = sum(mo.total for mo in getattr(proyecto, 'mano_de_obra', [])) + sum(mat.total for mat in getattr(proyecto, 'materiales', []))
    util_porc_val = getattr(proyecto, 'utilidad_porcentaje', 10.0) or 10.0
    utilidad_porc = util_porc_val / 100.0 if util_porc_val > 1 else util_porc_val
    otros_porc_val = getattr(proyecto, 'otros_porcentaje', 5.0) or 5.0
    otros_porc = otros_porc_val / 100.0 if otros_porc_val > 1 else otros_porc_val
    subtotal_sin_igv = costo_dir_temp * (1 + utilidad_porc + otros_porc)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Costo / Prto:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f' {subtotal_sin_igv:,.2f} PEN', border=1, ln=True)
    
    pdf.ln(5)
    
    # Información del Avance
    pdf.set_font('Arial', 'B', 11)
    tipo = getattr(avance, 'tipo_periodo', 'SEMANA')
    
    if tipo == 'HORA':
        titulo_sec = ' 2. SEGUIMIENTO POR HORAS'
        label_nro = 'Hora Registrada:'
    elif tipo == 'DIA':
        titulo_sec = ' 2. SEGUIMIENTO DIARIO'
        label_nro = 'Dia Registrado:'
    else:
        titulo_sec = ' 2. SEGUIMIENTO SEMANAL'
        label_nro = 'Semana Registrada:'
        
    pdf.cell(0, 8, titulo_sec, border=1, ln=True, fill=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, label_nro, border=1)
    pdf.set_font('Arial', '', 10)
    tipo = getattr(avance, 'tipo_periodo', 'SEMANA')
    if tipo == 'HORA':
        label = 'Hora Reportada'
    elif tipo == 'DIA':
        label = 'Nro Dia'
    else:
        label = 'Nro Semana'
    pdf.cell(60, 8, f' {label} {avance.semana}', border=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Avance Fisico:', border=1)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 102, 51) # Green
    pdf.cell(0, 8, f' {avance.porcentaje_avance} %', border=1, ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Fecha del Seguimiento:', border=1)
    pdf.set_font('Arial', '', 10)
    fecha_val = getattr(avance, 'fecha_fin', '')
    pdf.cell(60, 8, f' {fecha_val if fecha_val else "No Registrada"}', border=1)
    
    pdf.set_font('Arial', 'B', 10)
    label_trabajo = 'Horas Trabajadas:' if tipo == 'HORA' else 'Dias Trabajados:'
    pdf.cell(40, 8, label_trabajo, border=1)
    pdf.set_font('Arial', '', 10)
    
    dias_val = getattr(avance, 'dias_trabajados', 0)
    dias_text = str(dias_val) if dias_val is not None else '0'
    unidad_text = ' horas' if tipo == 'HORA' else ''
    pdf.cell(0, 8, f' {dias_text}{unidad_text}', border=1, ln=True)
    
    pdf.ln(7)
    
    pdf.ln(7)
    
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
                    final_w, final_h = get_proportional_dimensions(img_path, IMG_W, IMG_H)
                    offset_x = (IMG_W - final_w) / 2
                    offset_y = (IMG_H - final_h) / 2
                    pdf.image(img_path, x=x_coord + offset_x, y=row_y + offset_y, w=final_w, h=final_h)
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

    # --- Facturas ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' 6. EVIDENCIA DE FACTURAS Y COMPROBANTES', ln=True)
    pdf.set_font('Arial', '', 10)
    
    if getattr(avance, 'rutas_facturas', None):
        rutas_fac = [r.strip() for r in avance.rutas_facturas.split(',') if r.strip()]
        pdf.multi_cell(0, 6, f"Se han adjuntado {len(rutas_fac)} facturas/comprobantes.")
        pdf.ln(5)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Compartimos variables de tamaño pero las recalculamos para este bucle
        IMG_W = 88
        IMG_H = 75
        MARGIN_LEFT = 10
        COL_GAP = 7
        PAGE_BOTTOM = 270
        
        valid_fac = []
        for foto in rutas_fac:
            foto_safe = foto.encode('latin-1', 'replace').decode('latin-1').strip()
            img_path = os.path.join(base_dir, foto_safe.replace('/', os.sep))
            if os.path.exists(img_path):
                valid_fac.append(img_path)
                
        for i in range(0, len(valid_fac), 2):
            pair = valid_fac[i:i+2]
            if pdf.get_y() + IMG_H > PAGE_BOTTOM:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 10)
                pdf.set_fill_color(220, 230, 241)
                pdf.cell(0, 7, ' (continuacion - Facturas y Comprobantes)', border=1, ln=True, fill=True)
                pdf.ln(4)
            
            row_y = pdf.get_y()
            for j, img_path in enumerate(pair):
                x_coord = MARGIN_LEFT + j * (IMG_W + COL_GAP)
                try:
                    final_w, final_h = get_proportional_dimensions(img_path, IMG_W, IMG_H)
                    offset_x = (IMG_W - final_w) / 2
                    offset_y = (IMG_H - final_h) / 2
                    pdf.image(img_path, x=x_coord + offset_x, y=row_y + offset_y, w=final_w, h=final_h)
                except Exception as e:
                    pdf.set_xy(x_coord, row_y)
                    pdf.set_text_color(200, 0, 0)
                    pdf.multi_cell(IMG_W, 6, f"(Error imagen {i+j+1}: {str(e)[:40]})")
                    pdf.set_text_color(0, 0, 0)
            
            pdf.set_y(row_y + IMG_H + 5)
        pdf.ln(5)
    else:
        pdf.multi_cell(0, 6, "(No se insertaron facturas o comprobantes).")

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
        unidad_label = 'horas registradas' if tipo == 'HORA' else 'dias netos'
        pdf.cell(50, 7, f' {avance.dias_trabajados} {unidad_label}', align='C', border=1, ln=True)
        
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
            
        total_anexo_ii = 0.0
        for cat, items in grupos_fijos.items():
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, f'  {cat}', border=1, fill=True, ln=True)
            
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
            pdf.cell(30, 7, f' S/ {subtotal_cat:,.2f}', align='R', border=1, fill=True, ln=True)
            pdf.ln(4)
            total_anexo_ii += subtotal_cat

        # Fila de Total Final Anexo II
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(160, 10, ' TOTAL COSTOS FIJOS (ANEXO II):', align='R', border=1, fill=True)
        pdf.cell(30, 10, f' S/ {total_anexo_ii:,.2f}', align='R', border=1, fill=True, ln=True)
        pdf.ln(6)

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
            if cat == 'RRCITA':
                cat = 'MATERIALES'
            grupos_vars[cat].append(mat)
            
        total_anexo_iii = 0.0
        for cat, items in grupos_vars.items():
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, f'  {cat}', border=1, fill=True, ln=True)
            
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
            pdf.cell(30, 7, f' S/ {subtotal_cat:,.2f}', align='R', border=1, fill=True, ln=True)
            pdf.ln(4)
            total_anexo_iii += subtotal_cat

        # Fila de Total Final Anexo III
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(160, 10, ' TOTAL COSTOS VARIABLES (ANEXO III):', align='R', border=1, fill=True)
        pdf.cell(30, 10, f' S/ {total_anexo_iii:,.2f}', align='R', border=1, fill=True, ln=True)
        pdf.ln(6)

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
    # Porcentajes obtenidos del proyecto de forma dinámica
    util_porc_val = getattr(proyecto, 'utilidad_porcentaje', 10.0) or 10.0
    utilidad_porc = util_porc_val / 100.0 if util_porc_val > 1 else util_porc_val
    otros_porc_val = getattr(proyecto, 'otros_porcentaje', 5.0) or 5.0
    otros_porc = otros_porc_val / 100.0 if otros_porc_val > 1 else otros_porc_val
    
    utilidad_moneda = costo_directo * utilidad_porc
    otros_moneda = costo_directo * otros_porc
    
    subtotal_con_indirectos = costo_directo + utilidad_moneda + otros_moneda
    costos_indirectos = utilidad_moneda + otros_moneda
    igv = subtotal_con_indirectos * 0.18
    presupuesto_total = subtotal_con_indirectos + igv
    
    # Dibujar Tabla Centrada
    pdf.set_x(35)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(70, 10, ' COSTO DIRECTO', border=1)
    pdf.cell(50, 10, f' S/ {costo_directo:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_font('Arial', '', 10)
    total_indirectos_pct = int(round((utilidad_porc + otros_porc) * 100))
    pdf.cell(70, 10, f' COSTOS INDIRECTOS ({total_indirectos_pct}%)', border=1)
    pdf.cell(50, 10, f' S/ {costos_indirectos:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(70, 10, ' SUBTOTAL', border=1)
    pdf.cell(50, 10, f' S/ {subtotal_con_indirectos:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_font('Arial', '', 10)
    pdf.cell(70, 10, ' IGV (18%)', border=1)
    pdf.cell(50, 10, f' S/ {igv:,.2f}', border=1, align='R', ln=True)
    
    pdf.set_x(35)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(70, 12, ' PRESUPUESTO TOTAL DEL PROYECTO', border=1, fill=True)
    pdf.cell(50, 12, f' S/ {presupuesto_total:,.2f}', border=1, align='R', fill=True, ln=True)

    # ------------------ ANEXO V: REPORTE POR CONSUMO DE MATERIALES ---------------- #
    if hasattr(avance, 'consumos') and len(avance.consumos) > 0:
        pdf.add_page()
        pdf.set_text_color(0, 51, 102)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ANEXO V: REPORTE POR CONSUMO DE MATERIALES', ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(220, 230, 241)
        pdf.cell(80, 7, ' Material / Insumo', border=1, fill=True)
        pdf.cell(20, 7, ' Cantidad', align='C', border=1, fill=True)
        pdf.cell(20, 7, ' Unidad', align='C', border=1, fill=True)
        pdf.cell(30, 7, ' P. Unitario S/', align='C', border=1, fill=True)
        pdf.cell(40, 7, ' Subtotal S/', align='R', border=1, fill=True, ln=True)
        
        pdf.set_font('Arial', '', 9)
        total_gastado = 0.0
        
        for c in avance.consumos:
            desc_safe = c.nombre_material.encode('latin-1', 'replace').decode('latin-1')
            if len(desc_safe) > 40: desc_safe = desc_safe[:37] + "..."
            
            # Buscar precio unitario en el proyecto maestro
            precio_unitario = 0.0
            if hasattr(proyecto, 'materiales'):
                for mat in proyecto.materiales:
                    if mat.descripcion == c.nombre_material:
                        precio_unitario = getattr(mat, 'precio_unitario', 0.0) or 0.0
                        break
            
            cant = getattr(c, 'cantidad_usada', 0.0) or 0.0
            subtotal = precio_unitario * cant
            total_gastado += subtotal
            
            pdf.cell(80, 7, f' {desc_safe}', border=1)
            pdf.cell(20, 7, f" {cant}", align='C', border=1)
            unidad_safe = (c.unidad or "-").encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(20, 7, f" {unidad_safe}", align='C', border=1)
            pdf.cell(30, 7, f" {precio_unitario:,.2f}", align='C', border=1)
            pdf.cell(40, 7, f" {subtotal:,.2f}", align='R', border=1, ln=True)
        
        # Fila de Total Anexo V
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(150, 7, ' COSTO TOTAL DE BIENES CONSUMIDOS:', align='R', border=1, fill=True)
        pdf.set_text_color(0, 102, 51) # Color verde oscuro
        pdf.cell(40, 7, f' S/ {total_gastado:,.2f}', align='R', border=1, fill=True, ln=True)
        pdf.set_text_color(0, 0, 0) # Restaurar color

    # ------------------ ANEXO VI: RESUMEN ACUMULADO DE MATERIALES ---------------- #
    materiales_lista_vi = [m for m in getattr(proyecto, 'materiales', []) if m.categoria and 'MATERIALES' in m.categoria.upper()]

    if materiales_lista_vi:
        pdf.add_page()
        pdf.set_text_color(0, 51, 102)
        pdf.set_font('Arial', 'B', 12)
        tipo_vi = getattr(avance, 'tipo_periodo', 'SEMANA')
        if tipo_vi == 'HORA':
            semana_label_vi = f'Hora {avance.semana}'
        elif tipo_vi == 'DIA':
            semana_label_vi = f'Dia {avance.semana}'
        else:
            semana_label_vi = f'Semana {avance.semana}'
        pdf.cell(0, 10, f'ANEXO VI: MATERIALES ACUMULADOS HASTA {semana_label_vi.upper()}', ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

        # --- Cálculos para Resumen y Gráfico ---
        consumos_vi = {}
        for av in getattr(proyecto, 'avances', []):
            for c in getattr(av, 'consumos', []):
                consumos_vi[c.nombre_material] = consumos_vi.get(c.nombre_material, 0.0) + c.cantidad_usada

        # Deduplicar por nombre para totales financieros
        precios_unicos = {}
        for m in materiales_lista_vi:
            if m.descripcion not in precios_unicos:
                precios_unicos[m.descripcion] = getattr(m, 'precio_unitario', 0) or 0.0

        total_ppto_mat_vi = sum((m.cantidad or 0) * (m.precio_unitario or 0) for m in materiales_lista_vi)
        total_gast_mat_vi = sum(precios_unicos.get(nom, 0) * cant for nom, cant in consumos_vi.items())
        saldo_global_vi = total_ppto_mat_vi - total_gast_mat_vi
        
        # ======== SUB-SECCION: CUADRO DE RESUMEN ========
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(220, 230, 241)
        pdf.cell(0, 8, ' RESUMEN ESTRATEGICO DE MATERIALES', border=1, fill=True, ln=True)
        pdf.set_font('Arial', '', 9)
        pdf.cell(130, 7, '  Presupuesto Maestro de Materiales', border=1)
        pdf.cell(60, 7, f'  S/ {total_ppto_mat_vi:,.2f}', border=1, align='R', ln=True)
        pdf.cell(130, 7, '  Inversion Real Ejecutada (Acumulada)', border=1)
        pdf.cell(60, 7, f'  S/ {total_gast_mat_vi:,.2f}', border=1, align='R', ln=True)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(130, 8, '  SALDO DISPONIBLE EN MATERIALES PARA USO', border=1, fill=True)
        
        is_completed = getattr(avance, 'porcentaje_avance', 0) >= 100.0
        if saldo_global_vi >= 0:
            pdf.set_text_color(0, 102, 51)
            etiqueta = "(AHORRO CERRADO)" if is_completed else "(A FAVOR / REMANENTE)"
            pdf.cell(60, 8, f'  S/ {saldo_global_vi:,.2f}  {etiqueta}', border=1, fill=True, align='R', ln=True)
        else:
            pdf.set_text_color(200, 0, 0)
            etiqueta = "(PÉRDIDA / EXCESO)" if is_completed else "(SOBREGIRO TEMPORAL)"
            pdf.cell(60, 8, f'  S/ {abs(saldo_global_vi):,.2f}  {etiqueta}', border=1, fill=True, align='R', ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # ======== SUB-SECCION: GRAFICO COMPARATIVO (REDiseño Dual Bar) ========
        pdf.set_fill_color(220, 230, 241)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 7, ' GRAFICO COMPARATIVO: PRESUPUESTO vs GASTADO', border=1, fill=True, ln=True)
        pdf.ln(5)

        # Ajuste de márgenes para que cuadre con las tablas (A4 = 210mm)
        # Margen izquierdo tabla suele ser 10-15. Usaremos 15 para centrar.
        x_base = 15
        x_label_w = 40 
        w_max_bar = 130 # 15 + 40 + 130 = 185 (dentro de los 210mm)
        h_bar = 8
        
        # 1. Fila Presupuesto
        pdf.set_font('Arial', '', 9)
        pdf.set_x(x_base)
        pdf.cell(x_label_w, h_bar, 'Propuesto Total:', align='R')
        
        # Barra Azul (Total)
        pdf.set_fill_color(51, 102, 170) 
        pdf.rect(x_base + x_label_w + 3, pdf.get_y(), w_max_bar, h_bar, 'F')
        
        # Texto dentro de la barra
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_x(x_base + x_label_w + 6)
        pdf.cell(w_max_bar, h_bar, f'S/ {total_ppto_mat_vi:,.2f}', align='L')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(h_bar + 3)

        # 2. Fila Gastado
        pct_uso_global = (total_gast_mat_vi / total_ppto_mat_vi * 100) if total_ppto_mat_vi > 0 else 0
        w_real = min(w_max_bar, (pct_uso_global / 100) * w_max_bar)

        pdf.set_font('Arial', '', 9)
        pdf.set_x(x_base)
        pdf.cell(x_label_w, h_bar, 'Gastado:', align='R')
        
        # Fondo Gris
        pdf.set_fill_color(230, 230, 230)
        pdf.rect(x_base + x_label_w + 3, pdf.get_y(), w_max_bar, h_bar, 'F')
        
        # Barra de Progreso
        if pct_uso_global > 100:
            pdf.set_fill_color(200, 30, 30)
        else:
            pdf.set_fill_color(0, 160, 80)
            
        pdf.rect(x_base + x_label_w + 3, pdf.get_y(), w_real, h_bar, 'F')
        
        # Texto dentro de la barra
        if w_real > 35:
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_x(x_base + x_label_w + 6)
            pdf.cell(w_real, h_bar, f'S/ {total_gast_mat_vi:,.2f}', align='L')
        else:
            pdf.set_text_color(100, 100, 100)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_x(x_base + x_label_w + w_real + 6)
            pdf.cell(w_max_bar - w_real, h_bar, f'S/ {total_gast_mat_vi:,.2f}', align='L')

        pdf.set_text_color(0, 0, 0)
        pdf.ln(h_bar + 5)

        # Texto Resumen
        pdf.set_x(x_base + x_label_w + 3)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f'Uso acumulado total: {pct_uso_global:.1f}% del presupuesto de materiales', ln=True)
        pdf.ln(5)

        # ======== SUB-SECCION: TABLA DETALLADA ========
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(200, 215, 235)
        pdf.cell(65, 7, ' Insumo / Material', border=1, fill=True)
        pdf.cell(14, 7, ' Ped.', align='C', border=1, fill=True)
        pdf.cell(14, 7, ' Usado', align='C', border=1, fill=True)
        
        pdf.set_fill_color(235, 240, 215) # Fondo distinto para columna de saldo
        pdf.cell(15, 7, ' Saldo C.', align='C', border=1, fill=True)
        
        pdf.set_fill_color(200, 215, 235)
        pdf.cell(22, 7, ' Total S/', align='C', border=1, fill=True)
        pdf.cell(22, 7, ' Gast. S/', align='C', border=1, fill=True)
        pdf.cell(15, 7, ' %', align='C', border=1, fill=True)
        
        pdf.set_fill_color(235, 240, 215) # Fondo distinto para columna de saldo
        pdf.cell(23, 7, ' Saldo S/', align='C', border=1, fill=True, ln=True)

        # --- Agrupar presupuesto por nombre de material ---
        materiales_agrupados = {}
        for mat in materiales_lista_vi:
            nombre = mat.descripcion
            if nombre not in materiales_agrupados:
                materiales_agrupados[nombre] = {
                    'cantidad': 0.0,
                    'precio': getattr(mat, 'precio_unitario', 0) or 0.0,
                    'unidad': mat.unidad or ''
                }
            materiales_agrupados[nombre]['cantidad'] += getattr(mat, 'cantidad', 0) or 0.0

        pdf.set_font('Arial', '', 7)
        for nombre, data in materiales_agrupados.items():
            desc_safe = nombre.encode('latin-1', 'replace').decode('latin-1')
            if len(desc_safe) > 36: desc_safe = desc_safe[:33] + '...'
            
            cant_pedida = data['cantidad']
            precio_unit = data['precio']
            cant_usada  = consumos_vi.get(nombre, 0.0)
            
            saldo_cant  = cant_pedida - cant_usada
            costo_ppto  = cant_pedida * precio_unit
            costo_gast  = cant_usada * precio_unit
            saldo_mon   = costo_ppto - costo_gast
            pct_uso_insumo = (cant_usada / cant_pedida * 100) if cant_pedida > 0 else 0

            if cant_usada == 0: pdf.set_text_color(140, 140, 140)
            elif saldo_mon < 0: pdf.set_text_color(200, 0, 0)
            else: pdf.set_text_color(0, 0, 0)

            pdf.cell(65, 6, f' {desc_safe}', border=1)
            pdf.cell(14, 6, f' {cant_pedida:g}', align='C', border=1)
            txt_usado = f' {cant_usada:g}' if cant_usada > 0 else ' -'
            pdf.cell(14, 6, txt_usado, align='C', border=1)
            
            pdf.set_fill_color(248, 250, 235) # Resaltado ligero
            pdf.cell(15, 6, f' {saldo_cant:g}', align='C', border=1, fill=True)
            
            pdf.cell(22, 6, f' {costo_ppto:,.2f}', align='R', border=1)
            pdf.cell(22, 6, f' {costo_gast:,.2f}', align='R', border=1)
            pdf.cell(15, 6, f' {pct_uso_insumo:.0f}%', align='C', border=1)
            
            pdf.set_fill_color(248, 250, 235) # Resaltado ligero
            pdf.cell(23, 6, f' {saldo_mon:,.0f}', align='R', border=1, fill=True, ln=True)

        # Fila de Totales Generales
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0) # <--- Restaurar a negro explícitamente
        pdf.cell(65 + 14 + 14 + 15, 6, ' TOTALES:', align='R', border=1, fill=True)
        pdf.cell(22, 6, f' {total_ppto_mat_vi:,.2f}', align='R', border=1, fill=True)
        pdf.cell(22, 6, f' {total_gast_mat_vi:,.2f}', align='R', border=1, fill=True)
        pct_global = (total_gast_mat_vi / total_ppto_mat_vi * 100) if total_ppto_mat_vi > 0 else 0
        
        pdf.set_text_color(*(0, 102, 51) if pct_global <= 100 else (200, 0, 0))
        pdf.cell(15, 6, f' {pct_global:.0f}%', align='C', border=1, fill=True)
        
        pdf.set_text_color(*(0, 102, 51) if saldo_global_vi >= 0 else (200, 0, 0))
        pdf.set_fill_color(235, 240, 215) # Fondo distinto para columna de saldo final
        pdf.cell(23, 6, f' {saldo_global_vi:,.0f}', align='R', border=1, fill=True, ln=True)

        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

        # ======== SUB-SECCION: ANALISIS IA ========
        if texto_balance_ia:
            pdf.set_font('Arial', 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, ' COMENTARIO EJECUTIVO SOBRE MATERIALES', border=1, fill=True, ln=True)
            pdf.set_font('Arial', 'I', 9)
            txt_ia_safe = texto_balance_ia.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, f' {txt_ia_safe}', border=1, align='J')

    # Firmas
    # Las firmas ahora estarán SIEMPRE obligatoriamente en la estructura final de todo el documento
    if pdf.get_y() > 240:
        pdf.add_page()
        pdf.ln(10)
    else:
        pdf.ln(25)
        
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, '________________________', ln=True, align='C')
    pdf.cell(0, 5, 'Firma y Sello', ln=True, align='C')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, 'Administrador', ln=True, align='C')

    # ---------- EVIDENCIA CONSOLIDADA DE TODOS LOS PERIODOS (solo en PDF final) ---------- #
    ruta_factura_final = getattr(proyecto, 'ruta_foto_final', None)
    es_avance_final = getattr(avance, 'porcentaje_avance', 0) >= 100

    if es_avance_final:
        todos_avances_ord = sorted(getattr(proyecto, 'avances', []), key=lambda x: x.semana)
        base_dir_cons = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        tiene_evidencia = any(
            getattr(av, 'rutas_fotografias', None) or getattr(av, 'rutas_facturas', None)
            for av in todos_avances_ord
        )

        if tiene_evidencia:
            pdf.add_page()
            pdf.set_fill_color(0, 51, 102)
            pdf.rect(0, 0, 210, 20, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_xy(10, 5)
            pdf.cell(0, 10, 'EVIDENCIA CONSOLIDADA DE TODOS LOS PERIODOS', ln=True, align='C')
            pdf.set_text_color(0, 0, 0)
            pdf.ln(15)

            IMG_W = 88
            IMG_H = 75
            MARGIN_LEFT = 10
            COL_GAP = 7
            PAGE_BOTTOM = 270

            for av in todos_avances_ord:
                tipo_av = getattr(av, 'tipo_periodo', 'SEMANA')
                if tipo_av == 'HORA':
                    label_av = f'Hora {av.semana}'
                elif tipo_av == 'DIA':
                    label_av = f'Dia {av.semana}'
                else:
                    label_av = f'Semana {av.semana}'

                rutas_fotos = getattr(av, 'rutas_fotografias', None) or ''
                rutas_fact  = getattr(av, 'rutas_facturas',   None) or ''

                if not rutas_fotos and not rutas_fact:
                    continue

                # Sub-encabezado del periodo
                pdf.set_fill_color(30, 64, 120)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Arial', 'B', 9)
                label_periodo_safe = f'  PERIODO: {label_av.upper()} - {av.porcentaje_avance}% Avance'
                label_periodo_safe = label_periodo_safe.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 8, label_periodo_safe, border=1, fill=True, ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)

                # ── Fotografías del periodo ──
                if rutas_fotos:
                    rutas_foto_list = [r.strip() for r in rutas_fotos.split(',') if r.strip()]
                    valid_imgs = []
                    for foto in rutas_foto_list:
                        foto_safe = foto.encode('latin-1', 'replace').decode('latin-1').strip()
                        img_path = os.path.join(base_dir_cons, foto_safe.replace('/', os.sep))
                        if os.path.exists(img_path):
                            valid_imgs.append(img_path)

                    if valid_imgs:
                        pdf.set_font('Arial', 'B', 8)
                        pdf.set_fill_color(220, 230, 241)
                        pdf.cell(0, 6, f'  Fotografias Tecnicas ({len(valid_imgs)})', border=1, fill=True, ln=True)
                        pdf.ln(2)
                        for i in range(0, len(valid_imgs), 2):
                            pair = valid_imgs[i:i+2]
                            if pdf.get_y() + IMG_H > PAGE_BOTTOM:
                                pdf.add_page()
                            row_y = pdf.get_y()
                            for j, img_p in enumerate(pair):
                                x_coord = MARGIN_LEFT + j * (IMG_W + COL_GAP)
                                try:
                                    final_w, final_h = get_proportional_dimensions(img_p, IMG_W, IMG_H)
                                    offset_x = (IMG_W - final_w) / 2
                                    offset_y = (IMG_H - final_h) / 2
                                    pdf.image(img_p, x=x_coord + offset_x, y=row_y + offset_y, w=final_w, h=final_h)
                                except Exception as e:
                                    pdf.set_xy(x_coord, row_y)
                                    pdf.set_text_color(200, 0, 0)
                                    pdf.multi_cell(IMG_W, 6, f"(Error: {str(e)[:35]})")
                                    pdf.set_text_color(0, 0, 0)
                            pdf.set_y(row_y + IMG_H + 5)
                        pdf.ln(4)

                # ── Facturas/comprobantes del periodo ──
                if rutas_fact:
                    rutas_fac_list = [r.strip() for r in rutas_fact.split(',') if r.strip()]
                    valid_fac = []
                    for fac in rutas_fac_list:
                        fac_safe = fac.encode('latin-1', 'replace').decode('latin-1').strip()
                        fac_path = os.path.join(base_dir_cons, fac_safe.replace('/', os.sep))
                        if os.path.exists(fac_path):
                            valid_fac.append(fac_path)

                    if valid_fac:
                        pdf.set_font('Arial', 'B', 8)
                        pdf.set_fill_color(220, 230, 241)
                        pdf.cell(0, 6, f'  Facturas / Comprobantes ({len(valid_fac)})', border=1, fill=True, ln=True)
                        pdf.ln(2)
                        for i in range(0, len(valid_fac), 2):
                            pair = valid_fac[i:i+2]
                            if pdf.get_y() + IMG_H > PAGE_BOTTOM:
                                pdf.add_page()
                            row_y = pdf.get_y()
                            for j, fac_p in enumerate(pair):
                                x_coord = MARGIN_LEFT + j * (IMG_W + COL_GAP)
                                try:
                                    final_w, final_h = get_proportional_dimensions(fac_p, IMG_W, IMG_H)
                                    offset_x = (IMG_W - final_w) / 2
                                    offset_y = (IMG_H - final_h) / 2
                                    pdf.image(fac_p, x=x_coord + offset_x, y=row_y + offset_y, w=final_w, h=final_h)
                                except Exception as e:
                                    pdf.set_xy(x_coord, row_y)
                                    pdf.set_text_color(200, 0, 0)
                                    pdf.multi_cell(IMG_W, 6, f"(Error: {str(e)[:35]})")
                                    pdf.set_text_color(0, 0, 0)
                            pdf.set_y(row_y + IMG_H + 5)
                        pdf.ln(4)

                pdf.ln(3)

    # ---------- ANEXO VII: FACTURA FINAL DE ENTREGA ---------- #
    if ruta_factura_final and es_avance_final:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        rutas_list = [r.strip() for r in ruta_factura_final.split(',') if r.strip()]
        
        valid_imgs_final = []
        for r_path in rutas_list:
            r_path_safe = r_path.encode('latin-1', 'replace').decode('latin-1').strip()
            full_p = os.path.join(base_dir, r_path_safe.replace('/', os.sep))
            if os.path.exists(full_p):
                valid_imgs_final.append(full_p)

        if valid_imgs_final:
            pdf.add_page()
            # Encabezado azul oscuro
            pdf.set_fill_color(0, 51, 102)
            pdf.rect(0, 0, 210, 20, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 13)
            pdf.set_xy(10, 5)
            pdf.cell(0, 10, 'ANEXO VII: FACTURA FINAL DE ENTREGA DEL PROYECTO', ln=True, align='C')
            pdf.set_text_color(0, 0, 0)
            pdf.ln(15)

            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(240, 248, 240)
            pdf.cell(0, 8, f'  Se adjuntan {len(valid_imgs_final)} evidencias de cierre definitivo de la obra.', border=1, ln=True, fill=True)
            pdf.ln(8)

            for img_p in valid_imgs_final:
                # Verificar espacio
                if pdf.get_y() + 120 > PAGE_BOTTOM:
                    pdf.add_page()
                
                start_y = pdf.get_y()
                try:
                    final_w, final_h = get_proportional_dimensions(img_p, 160, 100)
                    offset_x = (160 - final_w) / 2
                    pdf.image(img_p, x=25 + offset_x, y=start_y, w=final_w, h=final_h)
                    pdf.set_y(start_y + final_h + 5)
                except Exception as e:
                    pdf.set_text_color(200, 0, 0)
                    pdf.multi_cell(0, 6, f"(Error cargando imagen de cierre: {str(e)[:60]})")
                    pdf.set_text_color(0, 0, 0)
                pdf.ln(10)

            pdf.set_font('Arial', 'I', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, 'Documentacion adjuntada al cierre del proyecto.', ln=True, align='C')
            pdf.set_text_color(0, 0, 0)

    # Guardar en archivo temporal seguro
    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    pdf.output(temp_path)
    return temp_path

def crear_pdf_balance_general(proyecto, texto_ia='', ppto_total_igv=0.0) -> str:
    from fpdf import FPDF
    import tempfile
    import os
    from datetime import datetime
    
    pdf = FPDF()
    pdf.add_page()
    
    # ------------------ ENCABEZADO ---------------- #
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 5)
    pdf.cell(0, 10, 'REPORTE GLOBAL: BALANCE ACUMULADO DE MATERIALES', ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.ln(15)
    nom_safe = proyecto.nombre_proyecto.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 8, f'Proyecto: {nom_safe}', ln=True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'Fecha de Emision: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)
    pdf.ln(8)

    # --- Calcular consumos globales (evitar doble conteo en totales) ---
    consumos_historicos = {}
    for av in getattr(proyecto, 'avances', []):
        for c in getattr(av, 'consumos', []):
            consumos_historicos[c.nombre_material] = consumos_historicos.get(c.nombre_material, 0.0) + c.cantidad_usada

    materiales_lista = [m for m in getattr(proyecto, 'materiales', []) if m.categoria and 'MATERIALES' in m.categoria.upper()]

    # Mapear precio unico por nombre (primer match) para calcular el gasto real sin duplicados
    precios_unicos = {}
    for m in materiales_lista:
        if m.descripcion not in precios_unicos:
            precios_unicos[m.descripcion] = getattr(m, 'precio_unitario', 0) or 0.0

    total_ppto = sum((m.cantidad or 0) * (m.precio_unitario or 0) for m in materiales_lista)
    total_gast = sum(precios_unicos.get(nom, 0) * cant for nom, cant in consumos_historicos.items())

    saldo_global = total_ppto - total_gast
    ppto_igv = ppto_total_igv if ppto_total_igv > 0 else total_ppto * 1.18

    # ======== SECCION 1: RESUMEN COMPARATIVO ========
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(0, 8, ' RESUMEN FINANCIERO COMPARATIVO', border=1, fill=True, ln=True)
    pdf.set_font('Arial', '', 9)
    filas = [
        ('Presupuesto Total del Proyecto (con IGV)', f'S/ {ppto_igv:,.2f}'),
        ('Presupuesto de MATERIALES del Proyecto', f'S/ {total_ppto:,.2f}'),
        ('Total Gastado en Materiales (acumulado)', f'S/ {total_gast:,.2f}'),
    ]
    for label, valor in filas:
        pdf.set_fill_color(250, 250, 250)
        pdf.cell(130, 7, f'  {label}', border=1, fill=True)
        pdf.cell(60, 7, f'  {valor}', border=1, fill=True, align='R', ln=True)

    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(130, 8, '  SALDO DISPONIBLE EN MATERIALES PARA USO', border=1, fill=True)
    
    pct_global_fisico = max([av.porcentaje_avance for av in getattr(proyecto, 'avances', [])], default=0.0)
    is_completed = pct_global_fisico >= 100.0

    if saldo_global >= 0:
        pdf.set_text_color(0, 102, 51)
        etiqueta = "(AHORRO CERRADO)" if is_completed else "(A FAVOR / REMANENTE)"
        saldo_txt = f'  S/ {saldo_global:,.2f}  {etiqueta}'
    else:
        pdf.set_text_color(200, 0, 0)
        etiqueta = "(PÉRDIDA / EXCESO)" if is_completed else "(SOBREGIRO TEMPORAL)"
        saldo_txt = f'  S/ {abs(saldo_global):,.2f}  {etiqueta}'
    pdf.cell(60, 8, saldo_txt, border=1, fill=True, align='R', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # ======== SECCION 2: GRAFICO DE BARRAS ========
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(0, 8, ' GRAFICO COMPARATIVO: PRESUPUESTO vs GASTADO', border=1, fill=True, ln=True)
    pdf.ln(4)

    bar_max_w = 140
    bar_h = 10
    bar_x = 50
    barra_y = pdf.get_y()

    if total_ppto > 0:
        # Barra presupuesto
        pdf.set_font('Arial', '', 8)
        pdf.set_xy(10, barra_y)
        pdf.cell(38, bar_h, 'Propuesto Total:', align='R')
        pdf.set_fill_color(52, 100, 163)
        pdf.rect(bar_x, barra_y, bar_max_w, bar_h, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(bar_x + 2, barra_y + 1.5)
        pdf.cell(bar_max_w - 4, bar_h - 3, f'S/ {total_ppto:,.2f}')
        pdf.set_text_color(0, 0, 0)

        # Barra gastado
        barra_y2 = barra_y + bar_h + 4
        gast_ratio = min(total_gast / total_ppto, 1.0)
        gast_w = bar_max_w * gast_ratio
        pdf.set_font('Arial', '', 8)
        pdf.set_xy(10, barra_y2)
        pdf.cell(38, bar_h, 'Gastado:', align='R')
        pdf.set_fill_color(*(0, 153, 76) if saldo_global >= 0 else (200, 50, 50))
        pdf.rect(bar_x, barra_y2, gast_w if gast_w > 0 else 1, bar_h, 'F')
        if gast_w < bar_max_w:
            pdf.set_fill_color(220, 220, 220)
            pdf.rect(bar_x + gast_w, barra_y2, bar_max_w - gast_w, bar_h, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(bar_x + 2, barra_y2 + 1.5)
        pdf.cell(gast_w - 4 if gast_w > 20 else gast_w, bar_h - 3, f'S/ {total_gast:,.2f}')
        pdf.set_text_color(0, 0, 0)

        pdf.set_y(barra_y2 + bar_h + 3)
        pct = (total_gast / total_ppto * 100)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, f'  Uso acumulado total: {pct:.1f}% del presupuesto de materiales', ln=True)
        pdf.set_text_color(0, 0, 0)

    pdf.ln(6)

    # ======== SECCION 3: TABLA DETALLADA ========
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(0, 8, ' DETALLE POR INSUMO', border=1, fill=True, ln=True)

    pdf.set_font('Arial', 'B', 7)
    pdf.set_fill_color(200, 215, 235)
    pdf.cell(60, 7, ' Insumo / Material', border=1, fill=True)
    pdf.cell(15, 7, ' Pedido', align='C', border=1, fill=True)
    pdf.cell(18, 7, ' Usado', align='C', border=1, fill=True)
    pdf.cell(15, 7, ' Saldo', align='C', border=1, fill=True)
    pdf.cell(22, 7, ' Ppto. S/', align='R', border=1, fill=True)
    pdf.cell(22, 7, ' Gastado S/', align='R', border=1, fill=True)
    pdf.cell(22, 7, ' Saldo S/', align='R', border=1, fill=True)
    pdf.cell(16, 7, ' % Uso', align='C', border=1, fill=True, ln=True)

    # --- Agrupar presupuesto por nombre de material ---
    materiales_agrupados = {}
    for mat in materiales_lista:
        nombre = mat.descripcion
        if nombre not in materiales_agrupados:
            materiales_agrupados[nombre] = {
                'cantidad': 0.0,
                'precio': getattr(mat, 'precio_unitario', 0) or 0.0,
                'unidad': mat.unidad or ''
            }
        materiales_agrupados[nombre]['cantidad'] += getattr(mat, 'cantidad', 0) or 0.0

    pdf.set_font('Arial', '', 6)
    for nombre, data in materiales_agrupados.items():
        desc_safe = nombre.encode('latin-1', 'replace').decode('latin-1')
        if len(desc_safe) > 36: desc_safe = desc_safe[:33] + '...'
        
        cant_pedida = data['cantidad']
        precio_unit = data['precio']
        cant_usada = consumos_historicos.get(nombre, 0.0)
        
        saldo_cant = cant_pedida - cant_usada
        costo_ppto = cant_pedida * precio_unit
        costo_gast = cant_usada * precio_unit
        saldo_mon  = costo_ppto - costo_gast
        pct_uso    = (cant_usada / cant_pedida * 100) if cant_pedida > 0 else 0

        if cant_usada == 0:
            pdf.set_text_color(140, 140, 140)
        elif saldo_mon < 0:
            pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(0, 0, 0)

        pdf.cell(60, 6, f' {desc_safe}', border=1)
        pdf.cell(15, 6, f' {cant_pedida:g}', align='C', border=1)
        txt = f' {cant_usada:g}' if cant_usada > 0 else ' No Usado'
        pdf.cell(18, 6, txt, align='C', border=1)
        pdf.cell(15, 6, f' {saldo_cant:g}', align='C', border=1)
        pdf.cell(22, 6, f' {costo_ppto:,.2f}', align='R', border=1)
        pdf.cell(22, 6, f' {costo_gast:,.2f}', align='R', border=1)
        pdf.cell(22, 6, f' {saldo_mon:,.2f}', align='R', border=1)
        pdf.cell(16, 6, f' {pct_uso:.0f}%', align='C', border=1, ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # ======== SECCION 4: INTERPRETACION IA ========
    if texto_ia:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(220, 230, 241)
        pdf.cell(0, 8, ' INTERPRETACION DEL ANALISTA (IA)', border=1, fill=True, ln=True)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_fill_color(248, 248, 248)
        txt_safe = texto_ia.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, f' {txt_safe}', border=1, fill=True, align='J')

    if pdf.get_y() > 240:
        pdf.add_page()
        pdf.ln(10)
    else:
        pdf.ln(20)
        
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, '________________________', ln=True, align='C')
    pdf.cell(0, 5, 'Firma y Sello (Administrador)', ln=True, align='C')
    
    # ------------------ ANEXO VII: FOTO FINAL DEL PROYECTO ---------------- #
    if getattr(proyecto, 'ruta_foto_final', None):
        img_final = getattr(proyecto, 'ruta_foto_final')
        if img_final:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            img_path = os.path.join(base_dir, img_final.replace('/', os.sep))
            if os.path.exists(img_path):
                pdf.add_page()
                pdf.set_text_color(0, 51, 102)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'ANEXO VII: FOTOGRAFIA FINAL DEL PROYECTO', ln=True, align='C')
                pdf.set_text_color(0, 0, 0)
                pdf.ln(10)
                
                try:
                    # w=160 para imagen apaisada y centrada horizontalmente
                    pdf.image(img_path, x=25, w=160, h=0)
                except Exception as e:
                    pdf.set_text_color(200, 0, 0)
                    pdf.multi_cell(0, 6, f"(Error cargando imagen final: {str(e)[:40]})")
                    pdf.set_text_color(0, 0, 0)
    
    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    pdf.output(temp_path)
    return temp_path
