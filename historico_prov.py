import pyodbc
from flask import Blueprint, render_template, request, current_app

historico_prov_bp = Blueprint('historico_prov', __name__, template_folder='templates', static_folder='static')

@historico_prov_bp.route('/historico_prov', methods=['GET', 'POST'])
def historico_prov():
    conn = current_app.get_db_connection()
    if not conn:
        return "Error de conexión a la base de datos.", 500

    cursor = conn.cursor()

    
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        query = """
            SELECT * FROM historico_prov
            WHERE fecha_accion BETWEEN ? AND ?
            ORDER BY fecha_accion DESC
        """
        cursor.execute(query, fecha_inicio, fecha_fin)
    else:
        query = "SELECT * FROM historico_prov ORDER BY fecha_accion DESC"
        cursor.execute(query)

    historico = cursor.fetchall()
    conn.close()

    
    accion_map = {
        'INSERT': 'Agregó',
        'DELETE': 'Eliminó',
        'UPDATE': 'Modificó'
    }

    historico_list = []
    for row in historico:
        historico_list.append({
            'id_historico': row.id_historico,
            'id_pedido_prov': row.id_pedido_prov,
            'proveedor': row.proveedor,
            'producto': row.producto,
            'precio': row.precio,
            'cantidad': row.cantidad,
            'suma_total': row.suma_total,
            'fecha': row.fecha,
            'estipulado': row.estipulado,
            'alerta': row.alerta,
            'accion': accion_map.get(row.accion, row.accion), 
            'fecha_accion': row.fecha_accion
        })

    return render_template('historico_prov.html', historico=historico_list)
