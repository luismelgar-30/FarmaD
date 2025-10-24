import pyodbc
from flask import Blueprint, render_template, request, current_app, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

historico_inventario_bp = Blueprint('historico_inventario', __name__, template_folder='templates', static_folder='static')


@historico_inventario_bp.route('/historico_inventario', methods=['GET', 'POST'])
def historico_inventario():
    conn = current_app.get_db_connection()
    if not conn:
        return "Error de conexión a la base de datos.", 500

    cursor = conn.cursor()

    
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        query = """
            SELECT * FROM historico_inventario
            WHERE fecha_accion BETWEEN ? AND ?
            ORDER BY fecha_accion DESC
        """
        cursor.execute(query, fecha_inicio, fecha_fin)
    else:
        query = "SELECT * FROM historico_inventario ORDER BY fecha_accion DESC"
        cursor.execute(query)

    historico = cursor.fetchall()

    
    accion_map = {'INSERT': 'Agregó', 'DELETE': 'Eliminó', 'UPDATE': 'Modificó'}
    accion_color = {'Agregó': 'accion-agrego', 'Eliminó': 'accion-elimino', 'Modificó': 'accion-modifico'}

    historico_list = []
    for row in historico:
        accion_text = accion_map.get(row.accion, row.accion)
        historico_list.append({
            'id_historico': row.id_historico,
            'id_inventario': row.id_inventario,
            'producto': row.producto,
            'cantidad': row.cantidad,
            'precio': row.precio,
            'preciomulti': row.preciomulti,
            'alerta': row.alerta,
            'accion': accion_text,
            'accion_class': accion_color.get(accion_text, ''),
            'fecha_accion': row.fecha_accion
        })

    return render_template('historico_inventario.html', historico=historico_list)


@historico_inventario_bp.route('/historico_inventario/pdf', methods=['GET'])
def historico_inventario_pdf():
    conn = current_app.get_db_connection()
    if not conn:
        return "Error de conexión a la base de datos.", 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico_inventario ORDER BY fecha_accion DESC")
    historico = cursor.fetchall()

    accion_map = {'INSERT': 'Agregó', 'DELETE': 'Eliminó', 'UPDATE': 'Modificó'}

    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, height - 40, "Histórico de Inventario")

    c.setFont("Helvetica", 10)
    y = height - 70

    
    headers = ["ID Hist.", "ID Inv.", "Producto", "Cantidad", "Precio", "Precio Multi", "Alerta", "Acción", "Fecha Acción"]
    x_positions = [30, 70, 120, 250, 300, 360, 410, 460, 520]

    for i, h in enumerate(headers):
        c.drawString(x_positions[i], y, h)
    y -= 20

    for row in historico:
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 50
        data = [
            str(row.id_historico),
            str(row.id_inventario),
            str(row.producto),
            str(row.cantidad),
            str(row.precio),
            str(row.preciomulti),
            str(row.alerta),
            accion_map.get(row.accion, row.accion),
            row.fecha_accion.strftime('%Y-%m-%d %H:%M:%S')
        ]
        for i, d in enumerate(data):
            c.drawString(x_positions[i], y, d)
        y -= 15

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="historico_inventario.pdf", mimetype='application/pdf')
