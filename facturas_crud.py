import pyodbc, json, io
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, jsonify, send_file
from datetime import datetime
from fpdf import FPDF

facturas_bp = Blueprint('facturas', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['CONNECTION_STRING'])

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 20)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, 'FARMACIA MELGAR', ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50)
        self.cell(0, 5, 'Barrio Los Angeles, San Sebastian, Lempira', ln=True, align='C')
        self.cell(0, 5, 'Telefono: 32228808 | Correo: farmaciamelgar30@gmail.com', ln=True, align='C')
        self.ln(10)
        self.line(10, 35, 200, 35)


@facturas_bp.route('/facturacion', methods=['GET', 'POST'])
def factura_home():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            
            num_fact = request.form['numero_factura']
            id_cai = request.form['cai_selector']
            subtotal = float(request.form['subtotal_hidden'])
            impuesto = float(request.form['impuesto_hidden'])
            total_f = float(request.form['total_final_hidden'])
            
            
            productos_json = json.loads(request.form['productos_data'])

            
            cursor.execute("""
                INSERT INTO facturas (numero_factura, id_cai_fk, subtotal, impuesto, total_final, fecha_emision)
                OUTPUT INSERTED.id_factura
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, (num_fact, id_cai, subtotal, impuesto, total_f))
            id_nueva_factura = cursor.fetchone()[0]

          
            for p in productos_json:
                cursor.execute("""
                    INSERT INTO factura_detalle (id_factura_fk, producto_nombre, cantidad, precio_unitario, total_linea)
                    VALUES (?, ?, ?, ?, ?)
                """, (id_nueva_factura, p['nombre'], p['cantidad'], p['precio'], p['total']))
                
                
                cursor.execute("UPDATE inventario SET cantidad = cantidad - ? WHERE producto = ?", (p['cantidad'], p['nombre']))

            
            cursor.execute("SELECT cai_numero, rtn, fecha_final, rango_inicio, rango_final FROM cai WHERE id_cai = ?", id_cai)
            cai = cursor.fetchone()
            conn.commit()

            
            pdf = PDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'FACTURA No: {num_fact}', ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 6, f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")} | RTN: {cai.rtn}', ln=True)
            
         
            pdf.multi_cell(190, 6, f'CAI: {cai.cai_numero}')
            pdf.multi_cell(190, 6, f'Rango Autorizado: {cai.rango_inicio} al {cai.rango_final}')
            
            pdf.cell(0, 6, f'Limite Emision: {cai.fecha_final}', ln=True)
            pdf.ln(5)

            
            pdf.set_fill_color(0, 102, 204); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 10)
            pdf.cell(85, 8, ' Producto', 1, 0, 'L', True)
            pdf.cell(25, 8, ' Cant.', 1, 0, 'C', True)
            pdf.cell(40, 8, ' Precio U.', 1, 0, 'C', True)
            pdf.cell(40, 8, ' Total', 1, 1, 'C', True)

            pdf.set_text_color(0); pdf.set_font('Arial', '', 10)
            for p in productos_json:
                pdf.cell(85, 8, f" {p['nombre']}", 1)
                pdf.cell(25, 8, f" {p['cantidad']}", 1, 0, 'C')
                pdf.cell(40, 8, f" L. {float(p['precio']):,.2f}", 1, 0, 'R')
                pdf.cell(40, 8, f" L. {float(p['total']):,.2f}", 1, 1, 'R')

         
            pdf.ln(2); pdf.set_x(140)
            pdf.cell(30, 7, 'Subtotal:', 0); pdf.cell(30, 7, f'L. {subtotal:,.2f}', 0, 1, 'R')
            pdf.set_x(140)
            pdf.cell(30, 7, 'ISV (25%):', 0); pdf.cell(30, 7, f'L. {impuesto:,.2f}', 0, 1, 'R')
            pdf.set_x(140); pdf.set_font('Arial', 'B', 12)
            pdf.cell(30, 10, 'TOTAL:', 0); pdf.cell(30, 10, f'L. {total_f:,.2f}', 0, 1, 'R')
            
            pdf.ln(10); pdf.set_font('Arial', 'I', 12); pdf.cell(0, 10, 'Gracias por su compra', 0, 0, 'C')

            output = io.BytesIO()
            pdf_str = pdf.output(dest='S')
            output.write(pdf_str); output.seek(0)
            return send_file(output, download_name=f"Factura_{num_fact}.pdf", as_attachment=False)

        except Exception as e:
            if conn: conn.rollback()
            return f"Error procesando factura: {str(e)}", 400
        finally:
            conn.close()

    
    cursor.execute("SELECT id_cai, cai_numero FROM cai WHERE estado = 'Activo'")
    cais = cursor.fetchall()
    cursor.execute("SELECT producto, precio, cantidad FROM inventario WHERE cantidad > 0")
    prods = cursor.fetchall()
    conn.close()
    return render_template('factura.html', cais=cais, productos=prods)


@facturas_bp.route('/historial')
def historial_facturas():
    fecha_filtro = request.args.get('fecha')
    conn = get_db_connection()
    cursor = conn.cursor()
    

    query = """
        SELECT f.id_factura, f.numero_factura, f.fecha_emision, f.total_final, c.cai_numero
        FROM facturas f
        JOIN cai c ON f.id_cai_fk = c.id_cai
    """
    params = []
    if fecha_filtro:
        query += " WHERE CAST(f.fecha_emision AS DATE) = ?"
        params.append(fecha_filtro)
    
    query += " ORDER BY f.fecha_emision DESC"
    
    cursor.execute(query, params)
    facturas = cursor.fetchall()
    conn.close()
    return render_template('historial_facturas.html', facturas=facturas, fecha_sel=fecha_filtro)


@facturas_bp.route('/reimprimir/<int:id_factura>')
def reimprimir_factura(id_factura):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.numero_factura, f.subtotal, f.impuesto, f.total_final, 
               c.cai_numero, c.rtn, c.fecha_final, c.rango_inicio, c.rango_final, f.fecha_emision
        FROM facturas f
        JOIN cai c ON f.id_cai_fk = c.id_cai
        WHERE f.id_factura = ?
    """, id_factura)
    f = cursor.fetchone()

    cursor.execute("SELECT producto_nombre, cantidad, precio_unitario, total_linea FROM factura_detalle WHERE id_factura_fk = ?", id_factura)
    detalles = cursor.fetchall()
    conn.close()

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'COPIA DE FACTURA No: {f[0]}', ln=True)
    pdf.set_font('Arial', '', 10)
    
    
    f_origen = f[9].strftime("%d/%m/%Y %H:%M") if f[9] else "N/A"
    pdf.cell(0, 6, f'Fecha Origen: {f_origen} | RTN: {f[5]}', ln=True)
    
    pdf.multi_cell(190, 6, f'CAI: {f[4]}')
    pdf.multi_cell(190, 6, f'Rango Autorizado: {f[7]} al {f[8]}')
    pdf.cell(0, 6, f'Vence: {f[6]}', ln=True)
    pdf.ln(5)

    pdf.set_fill_color(0, 102, 204); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 10)
    pdf.cell(85, 8, ' Producto', 1, 0, 'L', True)
    pdf.cell(25, 8, ' Cant.', 1, 0, 'C', True)
    pdf.cell(40, 8, ' Precio U.', 1, 0, 'C', True)
    pdf.cell(40, 8, ' Total', 1, 1, 'C', True)

    pdf.set_text_color(0); pdf.set_font('Arial', '', 10)
    for d in detalles:
        pdf.cell(85, 8, f" {d[0]}", 1)
        pdf.cell(25, 8, f" {d[1]}", 1, 0, 'C')
        pdf.cell(40, 8, f" L. {float(d[2]):,.2f}", 1, 0, 'R')
        pdf.cell(40, 8, f" L. {float(d[3]):,.2f}", 1, 1, 'R')

    pdf.ln(2); pdf.set_x(140); pdf.set_font('Arial', 'B', 12)
    pdf.cell(30, 7, 'TOTAL:', 0); pdf.cell(30, 7, f'L. {float(f[3]):,.2f}', 0, 1, 'R')
    
    pdf.ln(10); pdf.set_font('Arial', 'I', 12); pdf.cell(0, 10, 'Reimpresion de Documento', 0, 0, 'C')

    output = io.BytesIO()
    pdf_str = pdf.output(dest='S')
    output.write(pdf_str); output.seek(0)
    return send_file(output, download_name=f"Copia_Factura_{f[0]}.pdf", as_attachment=False)


@facturas_bp.route('/get_cai_data/<int:id_cai>')
def get_cai_data(id_cai):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT rtn, rango_inicio, rango_final, fecha_final FROM cai WHERE id_cai = ?", id_cai)
    row = cursor.fetchone()
    
    cursor.execute("SELECT TOP 1 numero_factura FROM facturas WHERE id_cai_fk = ? ORDER BY id_factura DESC", id_cai)
    last_fact = cursor.fetchone()
    conn.close()
    
    if row:
        rango_partes = row[1].split('-')
        ultimo_num = int(rango_partes[-1])
        if last_fact:
            ultimo_num = int(last_fact[0].split('-')[-1]) + 1
            
        return jsonify({
            'rtn': row[0], 'rango_i': row[1], 'rango_f': row[2],
            'fecha_f': str(row[3]), 'proximo': str(ultimo_num).zfill(8)
        })
    return jsonify({})