import pyodbc
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, jsonify
import math


inventario_bp = Blueprint('inventario', __name__)
ITEMS_PER_PAGE = 10 


def get_db_connection():
    
    try:
        conn_string = current_app.config['CONNECTION_STRING']
        conn = pyodbc.connect(conn_string)
        return conn
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        return None

def get_alerta_status(cantidad):
   
    if cantidad <= 10:
        return 'Stock bajo'
    elif cantidad >= 50:
        return 'Stock sobrepasado'
    else:
        return 'Stock regulado'

def get_productos_names():
    
    conn = get_db_connection()
    if not conn: return []
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT nombre FROM productos ORDER BY nombre")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error al obtener nombres de productos: {e}")
        return []
    finally:
        if conn: conn.close()

def get_inventario_paginado(page, busqueda=''):
    
    conn = get_db_connection()
    if not conn: return [], 0, 0

    try:
        cursor = conn.cursor()
        offset = (page - 1) * ITEMS_PER_PAGE
        
        where_clause = ""
        if busqueda:
            where_clause = f" WHERE producto LIKE '%{busqueda}%'"
        
        
        count_query = f"SELECT COUNT(*) FROM inventario{where_clause}"
        cursor.execute(count_query)
        total_registros = cursor.fetchone()[0]
        total_pages = math.ceil(total_registros / ITEMS_PER_PAGE)

       
        data_query = f"""
            SELECT id_inventario, producto, cantidad, precio, preciomulti, alerta
            FROM inventario
            {where_clause}
            ORDER BY id_inventario
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(data_query, offset, ITEMS_PER_PAGE)
        columnas = [column[0] for column in cursor.description]
        
        inventario_list = []
        for row in cursor.fetchall():
            inventario_list.append(dict(zip(columnas, row)))

        return inventario_list, total_registros, total_pages
        
    except pyodbc.ProgrammingError as pe:
        if 'Invalid object name' in str(pe):
            flash("Error SQL: La tabla 'inventario' no ha sido creada. Ejecuta el script SQL.", 'error')
        print(f"Error de programación SQL: {pe}")
        return [], 0, 0
    except Exception as e:
        print(f"Error al obtener inventario: {e}")
        return [], 0, 0
    finally:
        if conn: conn.close()


@inventario_bp.route('/inventario', methods=['GET', 'POST'])
def inventario_home():
    
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    
    if request.method == 'POST':
        producto = request.form['producto']
      
        try:
            cantidad = int(request.form['cantidad'])
            precio = float(request.form['precio'])
        except ValueError:
            flash("Error: Cantidad y Precio deben ser números válidos.", 'error')
            return redirect(url_for('inventario.inventario_home'))

        preciomulti = cantidad * precio
        alerta = get_alerta_status(cantidad)
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                insert_query = """
                INSERT INTO inventario (producto, cantidad, precio, preciomulti, alerta) 
                VALUES (?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, producto, cantidad, precio, preciomulti, alerta)
                conn.commit()
                flash(f"Artículo '{producto}' agregado al inventario.", 'success')
            except Exception as e:
                flash(f"Error al guardar el artículo: {e}", 'error')
            finally:
                conn.close()
           
            return redirect(url_for('inventario.inventario_home'))

    inventario_list, total_registros, total_pages = get_inventario_paginado(page, busqueda)
    productos_names = get_productos_names()

    return render_template('inventario.html', 
        inventario=inventario_list,
        total_registros=total_registros,
        total_pages=total_pages,
        page=page,
        search_query=busqueda,
        productos_names=productos_names
    )

@inventario_bp.route('/inventario/obtener/<int:id_inventario>', methods=['GET'])
def obtener_articulo(id_inventario):
    
    conn = get_db_connection()
    articulo = None
    if conn:
        try:
            cursor = conn.cursor()
            select_query = """
            SELECT id_inventario, producto, cantidad, precio, preciomulti, alerta
            FROM inventario
            WHERE id_inventario = ?
            """
            cursor.execute(select_query, id_inventario)
            row = cursor.fetchone()
            
            if row:
                columnas = [column[0] for column in cursor.description]
                articulo = dict(zip(columnas, row))

        except Exception as e:
            print(f"Error al obtener artículo para edición: {e}")
        finally:
            conn.close()
            
    
    return jsonify(articulo) if articulo else jsonify({})

@inventario_bp.route('/inventario/editar/<int:id_inventario>', methods=['POST'])
def editar_articulo(id_inventario):
    
    if request.method == 'POST':
        producto = request.form['producto_edit']
        
        try:
            cantidad = int(request.form['cantidad_edit'])
            precio = float(request.form['precio_edit'])
        except ValueError:
            flash("Error: Cantidad y Precio deben ser números válidos.", 'error')
            return redirect(url_for('inventario.inventario_home'))

        # Lógica de negocio (recalculando)
        preciomulti = cantidad * precio
        alerta = get_alerta_status(cantidad)
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                update_query = """
                UPDATE inventario 
                SET producto=?, cantidad=?, precio=?, preciomulti=?, alerta=? 
                WHERE id_inventario=?
                """
                cursor.execute(update_query, producto, cantidad, precio, preciomulti, alerta, id_inventario)
                conn.commit()
                flash(f"Artículo ID {id_inventario} actualizado exitosamente.", 'success')
            except Exception as e:
                flash(f"Error al actualizar el artículo: {e}", 'error')
            finally:
                conn.close()

    
    page = request.form.get('current_page', 1, type=int)
    busqueda = request.form.get('current_busqueda', '').strip()
    return redirect(url_for('inventario.inventario_home', page=page, busqueda=busqueda))

@inventario_bp.route('/inventario/eliminar/<int:id_inventario>', methods=['POST'])
def eliminar_articulo(id_inventario):
   
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            delete_query = "DELETE FROM inventario WHERE id_inventario = ?"
            cursor.execute(delete_query, id_inventario)
            conn.commit()
            flash(f"Artículo ID {id_inventario} eliminado correctamente.", 'success')
        except Exception as e:
            flash(f"Error al eliminar el artículo: {e}", 'error')
        finally:
            conn.close()
    
    
    page = request.form.get('current_page', 1, type=int)
    busqueda = request.form.get('current_busqueda', '').strip()
    return redirect(url_for('inventario.inventario_home', page=page, busqueda=busqueda))