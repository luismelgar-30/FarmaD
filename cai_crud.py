import pyodbc
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app

cai_bp = Blueprint('cai', __name__)

def get_db_connection():
    """Establece la conexión usando el string configurado en app.py"""
    try:
        conn_string = current_app.config['CONNECTION_STRING']
        return pyodbc.connect(conn_string)
    except Exception as e:
        print(f"Error de conexión en CAI: {e}")
        return None

@cai_bp.route('/gestion', methods=['GET', 'POST'])
def cai_home():
    conn = get_db_connection()
    if not conn:
        flash("Error: No se pudo conectar a la base de datos.", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        
        usuario = request.form['usuario']
        rtn = request.form['rtn']
        fecha_inicio = request.form['fecha_inicio']
        fecha_final = request.form['fecha_final']
        cai_numero = request.form['cai_numero'].upper() 
        rango_inicio = request.form['rango_inicio']
        rango_final = request.form['rango_final']
        estado = request.form['estado']
        
        datos = (usuario, rtn, fecha_inicio, fecha_final, cai_numero, rango_inicio, rango_final, estado)
        
        try:
            cursor = conn.cursor()
            query = """INSERT INTO cai (usuario, rtn, fecha_inicio, fecha_final, cai_numero, rango_inicio, rango_final, estado)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            cursor.execute(query, datos)
            conn.commit()
            flash("Registro CAI guardado con éxito", "success")
        except Exception as e:
            flash(f"Error al guardar en SQL Server: {e}", "error")
        finally:
            conn.close()
        return redirect(url_for('cai.cai_home'))

    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_cai, usuario, rtn, fecha_inicio, fecha_final, cai_numero, rango_inicio, rango_final, estado FROM cai ORDER BY id_cai DESC")
        columnas = [column[0] for column in cursor.description]
        registros = [dict(zip(columnas, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error al leer tabla CAI: {e}")
        registros = []
    finally:
        conn.close()
    
    return render_template('cai.html', registros=registros)

@cai_bp.route('/eliminar/<int:id_cai>', methods=['POST'])
def eliminar_cai(id_cai):
    """Elimina un registro específico por su ID"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cai WHERE id_cai = ?", id_cai)
            conn.commit()
            flash(f"Registro ID {id_cai} eliminado correctamente.", "success")
        except Exception as e:
            flash(f"Error al eliminar: {e}", "error")
        finally:
            conn.close()
    return redirect(url_for('cai.cai_home'))