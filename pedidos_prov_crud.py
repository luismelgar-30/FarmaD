from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import date
import pyodbc

pedidos_prov = Blueprint('pedidos_prov', __name__, template_folder='templates', url_prefix='/pedidos_proveedor')

def get_db_connection():
    
    try:
        
        connection_string = current_app.config['CONNECTION_STRING']
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        
        print(f"ERROR DE CONEXIÓN EN pedidos_prov_crud: {e}")
        return None

@pedidos_prov.route('/', methods=['GET'])
def listar_pedidos():
    
    conn = get_db_connection()
    pedidos = []
    productos = []
    proveedores = []
    
    if not conn:
        
        flash('Error de conexión a la base de datos. No se pueden cargar datos ni guardar pedidos.', 'danger')
        return render_template('pedidos_prov.html', 
                               pedidos=pedidos, 
                               productos=productos, 
                               proveedores=proveedores)
    
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("""
            SELECT id_pedido_prov, proveedor, producto, precio, cantidad, suma_total, 
                   CONVERT(VARCHAR, fecha, 103) as fecha, estipulado, alerta 
            FROM pedido_prov 
            ORDER BY id_pedido_prov DESC
        """)
        columnas = [column[0] for column in cursor.description]
        pedidos = [dict(zip(columnas, row)) for row in cursor.fetchall()]
    except pyodbc.ProgrammingError as e:
        flash(f"Error al cargar pedidos: {e}", 'danger')
    
   
    try:
        
        cursor.execute("SELECT nombre FROM Proveedores")
        proveedores = [{'nombre': row[0]} for row in cursor.fetchall()]
    except pyodbc.ProgrammingError:
        flash("Advertencia: La tabla 'Proveedores' o la columna 'nombre' no se encuentra.", 'warning')
    
    
    try:
        
        cursor.execute("SELECT producto as nombre, precio FROM Inventario")
        columnas_prod = [column[0] for column in cursor.description]
        
        productos = [dict(zip(columnas_prod, row)) for row in cursor.fetchall()]
    except pyodbc.ProgrammingError:
        flash("Advertencia: La tabla 'Inventario' o las columnas 'producto'/'precio' no se encuentran.", 'warning')
        
    conn.close()

    return render_template('pedidos_prov.html', 
                           pedidos=pedidos, 
                           productos=productos, 
                           proveedores=proveedores)

@pedidos_prov.route('/agregar', methods=['POST'])
def agregar_pedido():
   
    conn = get_db_connection()
    if not conn:
        flash('Error de conexión al guardar el pedido.', 'danger')
        return redirect(url_for('pedidos_prov.listar_pedidos'))

    try:
        
        proveedor = request.form['proveedor']
        producto = request.form['producto']
        precio = float(request.form['precio']) 
        cantidad = int(request.form['cantidad'])
        estipulado = request.form['estipulado']
        
        suma_total = precio * cantidad
        fecha_actual = date.today().isoformat()
        alerta = 'En proceso' 
        
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO pedido_prov (proveedor, producto, precio, cantidad, suma_total, fecha, estipulado, alerta) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, proveedor, producto, precio, cantidad, suma_total, fecha_actual, estipulado, alerta)
        conn.commit()
        
        flash(f'Pedido a {proveedor} por {producto} agregado exitosamente. Total: ${suma_total:.2f}', 'success')

    except Exception as e:
        conn.rollback()
        print(f"Error al agregar el pedido: {e}")
        flash(f'Error al procesar el pedido. Detalle: {e}', 'danger')
        
    finally:
        if conn:
            conn.close()
            
    return redirect(url_for('pedidos_prov.listar_pedidos'))


@pedidos_prov.route('/actualizar_estado/<int:id_pedido>', methods=['POST'])
def actualizar_estado(id_pedido):
   
    conn = get_db_connection()
    if not conn:
        flash('Error de conexión al actualizar el estado.', 'danger')
        return redirect(url_for('pedidos_prov.listar_pedidos'))

    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado not in ['Recibido', 'Cancelado']:
        flash('Estado no válido.', 'danger')
        if conn: conn.close()
        return redirect(url_for('pedidos_prov.listar_pedidos'))

    try:
        cursor = conn.cursor()
        
        if nuevo_estado == 'Recibido':
            
            cursor.execute("SELECT producto, cantidad, alerta FROM pedido_prov WHERE id_pedido_prov = ?", id_pedido)
            pedido = cursor.fetchone()

            if not pedido:
                flash(f'Pedido ID {id_pedido} no encontrado.', 'danger')
                if conn: conn.close()
                return redirect(url_for('pedidos_prov.listar_pedidos'))
            
            producto_nombre = pedido[0]
            cantidad_recibida = pedido[1]
            estado_actual = pedido[2]
            
            
            if estado_actual == 'Recibido':
                flash('Este pedido ya fue marcado como Recibido.', 'warning')
                if conn: conn.close()
                return redirect(url_for('pedidos_prov.listar_pedidos'))

            update_inventario_sql = """
            UPDATE Inventario 
            SET cantidad = cantidad + ? 
            WHERE producto = ?
            """
            cursor.execute(update_inventario_sql, cantidad_recibida, producto_nombre)
            
            if cursor.rowcount == 0:
                flash(f'Advertencia: El producto "{producto_nombre}" no existe en Inventario. No se actualizó el stock.', 'warning')
            else:
                flash(f'Inventario actualizado: se agregaron {cantidad_recibida} unidades de {producto_nombre}.', 'success')
        
        update_pedido_sql = "UPDATE pedido_prov SET alerta = ? WHERE id_pedido_prov = ?"
        cursor.execute(update_pedido_sql, nuevo_estado, id_pedido)
        
        conn.commit()
        
        flash(f'Estado del Pedido ID {id_pedido} actualizado a "{nuevo_estado}".', 'info')

    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar el estado o inventario: {e}")
        flash(f'Error al actualizar el estado o inventario: {e}', 'danger')
        
    finally:
        if conn:
            conn.close()
            
    return redirect(url_for('pedidos_prov.listar_pedidos'))
