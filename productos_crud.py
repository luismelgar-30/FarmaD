import pyodbc
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session

productos = Blueprint('productos', __name__, url_prefix='/productos')


TIPOS = ['Sólido', 'Vacuna', 'Líquido', 'Gel', 'Otro']
ACEPTADO = ['Joven', 'Adulto', 'Mayor', 'Otro']
TIPO_CANTIDAD = ['Litro', 'MG', 'ML', 'Gramo', 'Otro']


def get_db_connection():
    
    
    
    try:
        conn = pyodbc.connect(current_app.config['CONNECTION_STRING'])
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        
        print(f"Error de conexión a la base de datos: {sqlstate}")
        flash('Error al conectar con la base de datos.','error')
        return None

def execute_query(query, params=(), fetch_one=False):
    
    conn = get_db_connection()
    if conn is None:
        return None if fetch_one else []
        
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
            return True 
        
        columns = [column[0] for column in cursor.description]
        if fetch_one:
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        else:
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return data

    except pyodbc.ProgrammingError as pe:
        conn.rollback()
        print(f"Error de programación SQL: {pe}")
        flash('Error al ejecutar la consulta: programación.','error')
        return False 
    except Exception as e:
        conn.rollback()
        print(f"Error general en la consulta: {e}")
        flash('Ocurrió un error inesperado al procesar los datos.','error')
        return False

    finally:
        cursor.close()
        conn.close()

def obtener_producto_por_id(id_producto):
    
    query = "SELECT id_producto, nombre, categoria, tipo, aceptado, tipo_cantidad, cantidad FROM Productos WHERE id_producto = ?"
    return execute_query(query, (id_producto,), fetch_one=True)


@productos.route('/')
def listar_productos():
    
    if 'email' not in session:
        return redirect(url_for('login'))

    try:
    
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page

        total_query = "SELECT COUNT(*) FROM Productos"
        total_productos = execute_query(total_query, fetch_one=True)['']
        total_pages = (total_productos + per_page - 1) // per_page

        productos_query = f"""
            SELECT id_producto, nombre, categoria, tipo, aceptado, tipo_cantidad, cantidad 
            FROM Productos 
            ORDER BY id_producto
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
        """
        data = execute_query(productos_query, (offset, per_page))

        
        if data is False:
             flash('No se pudieron cargar los datos de los productos.', 'error')
             data = []

    except Exception as e:
        print(f"Error en listar_productos: {e}")
        flash('Ocurrió un error al cargar la vista de productos.', 'error')
        data = []
        total_productos = 0
        total_pages = 0

    return render_template(
        'productos.html',
        productos=data,
        tipos=TIPOS,
        aceptado=ACEPTADO,
        tipocantidad=TIPO_CANTIDAD,
        total_productos=total_productos,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@productos.route('/agregar', methods=['POST'])
def agregar_producto():
    
    if 'email' not in session:
        return redirect(url_for('login'))
        
    try:
        
        nombre = request.form['nombre']
        categoria = request.form['categoria']
        tipo = request.form['tipo']
        aceptado = request.form['aceptado']
        tipocantidad = request.form['tipocantidad']
        
        cantidad_str = request.form['cantidad']
        try:
            cantidad = int(cantidad_str)
        except ValueError:
            flash('La cantidad debe ser un número entero válido.', 'warning')
            return redirect(url_for('productos.listar_productos'))


       
        query = """
            INSERT INTO Productos (nombre, categoria, tipo, aceptado, tipo_cantidad, cantidad)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (nombre, categoria, tipo, aceptado, tipocantidad, cantidad)
        
        
        if execute_query(query, params) is True:
            flash(f'Producto "{nombre}" agregado exitosamente.', 'success')
        else:
            flash('Error al agregar el producto. Intente de nuevo.','error')
            
    except Exception as e:
        print(f"Error al agregar producto: {e}")
        flash('Error al procesar la solicitud de agregar producto.','error')

    return redirect(url_for('productos.listar_productos'))


@productos.route('/eliminar/<int:id_producto>', methods=['POST'])
def eliminar_producto(id_producto):
    if 'email' not in session:
        return redirect(url_for('login'))

    query = "DELETE FROM Productos WHERE id_producto = ?"
    if execute_query(query, (id_producto,)) is True:
        flash('Producto eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar el producto.', 'error')
        
    return redirect(url_for('productos.listar_productos'))

 


@productos.route('/editar/<int:id_producto>', methods=['GET', 'POST'])
def editar_producto(id_producto):
    
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            
            nombre = request.form['nombre_edit']
            categoria = request.form['categoria_edit']
            tipo = request.form['tipo_edit']
            aceptado = request.form['aceptado_edit']
            tipocantidad = request.form['tipocantidad_edit']
            
           
            cantidad_str = request.form['cantidad_edit']
            try:
                cantidad = int(cantidad_str)
            except ValueError:
                flash('La cantidad debe ser un número entero válido.', 'warning')
                return redirect(url_for('productos.listar_productos'))


            
            query = """
                UPDATE Productos SET 
                nombre = ?, categoria = ?, tipo = ?, aceptado = ?, tipo_cantidad = ?, cantidad = ?
                WHERE id_producto = ?
            """
            params = (nombre, categoria, tipo, aceptado, tipocantidad, cantidad, id_producto)

            
            if execute_query(query, params) is True:
                flash(f'Producto "{nombre}" actualizado exitosamente.', 'success')
            else:
                flash('Error al actualizar el producto.','error')
                
        except Exception as e:
            print(f"Error al editar producto: {e}")
            flash('Error al procesar la solicitud de edición.','error')

        return redirect(url_for('productos.listar_productos'))

    return redirect(url_for('productos.listar_productos'))


