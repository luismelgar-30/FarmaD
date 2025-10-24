import pyodbc
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, jsonify
import math


proveedores = Blueprint('proveedores', __name__)

DEPARTAMENTOS_HONDURAS = [
    'Atlántida', 'Colón', 'Comayagua', 'Copán', 'Cortés', 'Choluteca', 'El Paraíso',
    'Francisco Morazán', 'Gracias a Dios', 'Intibucá', 'Islas de la Bahía', 'La Paz',
    'Lempira', 'Ocotepeque', 'Olancho', 'Santa Bárbara', 'Valle', 'Yoro'
]

OPCIONES_DISTANCIA = [
    'un día', 'medio día', 'dos días', 'horas', 'otro'
]

REGISTROS_POR_PAGINA = 10 


def get_db_connection():
    
    try:
        conn_string = current_app.config['CONNECTION_STRING']
        conn = pyodbc.connect(conn_string)
        return conn
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        return None

def get_proveedores_paginados(page=1, busqueda=''):
    
    conn = get_db_connection()
    if not conn:
        return [], 0, 1

    try:
        cursor = conn.cursor()
        
        
        where_clause = ""
        if busqueda:
            where_clause = f" WHERE nombre LIKE '%{busqueda}%' OR nombre_contacto LIKE '%{busqueda}%'"
        
        
        count_query = "SELECT COUNT(*) FROM proveedores"
        cursor.execute(count_query + where_clause)
        total_registros = cursor.fetchone()[0]

        
        total_pages = math.ceil(total_registros / REGISTROS_POR_PAGINA)
        offset = (page - 1) * REGISTROS_POR_PAGINA
        
        
        data_query = f"""
            SELECT id_proveedor, nombre, nombre_contacto, numero, distancia, departamento
            FROM proveedores
            {where_clause}
            ORDER BY id_proveedor 
            OFFSET {offset} ROWS 
            FETCH NEXT {REGISTROS_POR_PAGINA} ROWS ONLY
        """
        cursor.execute(data_query)
        columnas = [column[0] for column in cursor.description]
        
        proveedores_list = []
        for row in cursor.fetchall():
            proveedores_list.append(dict(zip(columnas, row)))

        
        return proveedores_list, total_registros, total_pages
        
    except pyodbc.ProgrammingError as pe:
        if 'Invalid object name' in str(pe):
            flash("Error SQL: La tabla 'proveedores' no ha sido creada. Ejecuta el script SQL.", 'error')
        print(f"Error de programación SQL: {pe}")
        return [], 0, 1
    except Exception as e:
        print(f"Error al obtener proveedores: {e}")
        return [], 0, 1
    finally:
        if conn:
            conn.close()


@proveedores.route('/', methods=['GET', 'POST'])
def proveedores_home():
    
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        nombre_contacto = request.form['nombre_contacto']
        numero = request.form['numero']
        distancia = request.form['distancia']
        departamento = request.form['departamento']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                insert_query = """
                INSERT INTO proveedores (nombre, nombre_contacto, numero, distancia, departamento) 
                VALUES (?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, nombre, nombre_contacto, numero, distancia, departamento)
                conn.commit()
                flash(f"Proveedor '{nombre}' agregado exitosamente.", 'success')
            except Exception as e:
                flash(f"Error al guardar el proveedor: {e}", 'error')
            finally:
                conn.close()

            return redirect(url_for('proveedores.proveedores_home'))

    proveedores_list, total_registros, total_pages = get_proveedores_paginados(page, busqueda)

    return render_template('proveedores.html', 
        proveedores=proveedores_list,
        total_registros=total_registros,
        total_pages=total_pages,  
        page=page,                
        search_query=busqueda,
        departamentos=DEPARTAMENTOS_HONDURAS,
        distancias=OPCIONES_DISTANCIA
    )

@proveedores.route('/editar/<int:id_proveedor>', methods=['POST'])
def editar_proveedor(id_proveedor):
    
    if request.method == 'POST':
        nombre = request.form['nombre_edit']
        nombre_contacto = request.form['nombre_contacto_edit']
        numero = request.form['numero_edit']
        distancia = request.form['distancia_edit']
        departamento = request.form['departamento_edit']

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                update_query = """
                UPDATE proveedores 
                SET nombre=?, nombre_contacto=?, numero=?, distancia=?, departamento=? 
                WHERE id_proveedor=?
                """
                cursor.execute(update_query, nombre, nombre_contacto, numero, distancia, departamento, id_proveedor)
                conn.commit()
                flash(f"Proveedor con ID {id_proveedor} actualizado exitosamente.", 'success')
            except Exception as e:
                flash(f"Error al actualizar el proveedor: {e}", 'error')
            finally:
                conn.close()

    
    current_page = request.form.get('current_page', 1)
    busqueda = request.form.get('current_busqueda', '')
    return redirect(url_for('proveedores.proveedores_home', page=current_page, busqueda=busqueda))

@proveedores.route('/eliminar/<int:id_proveedor>', methods=['POST'])
def eliminar_proveedor(id_proveedor):
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            delete_query = "DELETE FROM proveedores WHERE id_proveedor = ?"
            cursor.execute(delete_query, id_proveedor)
            conn.commit()
            flash(f"Proveedor con ID {id_proveedor} eliminado correctamente.", 'success')
        except Exception as e:
            flash(f"Error al eliminar el proveedor: {e}", 'error')
        finally:
            conn.close()
    
    
    current_page = request.form.get('current_page', 1)
    busqueda = request.form.get('current_busqueda', '')
    return redirect(url_for('proveedores.proveedores_home', page=current_page, busqueda=busqueda))


@proveedores.route('/obtener_proveedor/<int:id_proveedor>', methods=['GET'])
def obtener_proveedor(id_proveedor):
    
    conn = get_db_connection()
    proveedor = None
    if conn:
        try:
            cursor = conn.cursor()
            select_query = """
            SELECT id_proveedor, nombre, nombre_contacto, numero, distancia, departamento
            FROM proveedores
            WHERE id_proveedor = ?
            """
            cursor.execute(select_query, id_proveedor)
            row = cursor.fetchone()
            
            if row:
                columnas = [column[0] for column in cursor.description]
                proveedor = dict(zip(columnas, row))

        except Exception as e:
            print(f"Error al obtener proveedor para edición: {e}")
        finally:
            conn.close()
            
    
    return jsonify(proveedor) if proveedor else jsonify({})