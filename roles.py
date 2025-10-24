from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import pyodbc

roles_bp = Blueprint('roles_bp', __name__, template_folder='templates')

def get_db_connection():
    return current_app.get_db_connection()


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Debes iniciar sesión.", "error")
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM roles WHERE usuario = ?", session['email'])
        user_rol = cursor.fetchone()
        conn.close()
        
        if not user_rol or user_rol.rol != 'administrador':
            flash("No tienes permisos para acceder a esta página.", "error")
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

@roles_bp.route('/roles')
@admin_required
def roles_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT r.id_rol, r.rol, u.email FROM roles r JOIN usuarios u ON r.usuario = u.email")
    roles = cursor.fetchall()
    
    
    cursor.execute("SELECT email FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('roles.html', roles=roles, usuarios=usuarios)

@roles_bp.route('/roles/add', methods=['POST'])
@admin_required
def add_role():
    rol = request.form.get('rol')
    usuario = request.form.get('usuario')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (rol, usuario) VALUES (?, ?)", rol, usuario)
        conn.commit()
        flash("Rol agregado correctamente.", "success")
    except pyodbc.IntegrityError:
        flash("Este usuario ya tiene un rol asignado.", "error")
    finally:
        conn.close()
    return redirect(url_for('roles_bp.roles_list'))

@roles_bp.route('/roles/delete/<int:id_rol>')
@admin_required
def delete_role(id_rol):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roles WHERE id_rol = ?", id_rol)
    conn.commit()
    conn.close()
    flash("Rol eliminado correctamente.", "success")
    return redirect(url_for('roles_bp.roles_list'))

@roles_bp.route('/roles/edit/<int:id_rol>', methods=['GET', 'POST'])
@admin_required
def edit_role(id_rol):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        rol = request.form.get('rol')
        usuario = request.form.get('usuario')
        cursor.execute("UPDATE roles SET rol = ?, usuario = ? WHERE id_rol = ?", rol, usuario, id_rol)
        conn.commit()
        conn.close()
        flash("Rol actualizado correctamente.", "success")
        return redirect(url_for('roles_bp.roles_list'))
    
    cursor.execute("SELECT * FROM roles WHERE id_rol = ?", id_rol)
    role = cursor.fetchone()
    cursor.execute("SELECT email FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('roles.html', edit_role=role, usuarios=usuarios)
