import pyodbc
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash  # 🔒 Importar función para encriptar contraseñas

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

def get_db_connection():
    conn = pyodbc.connect(current_app.config['CONNECTION_STRING'])
    return conn


@usuarios_bp.route('/usuarios_home')
def usuarios_home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre, email, telefono FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('usuarios_home.html', usuarios=usuarios)


@usuarios_bp.route('/agregar', methods=['POST'])
def agregar_usuario():
    nombre = request.form['nombre']
    contrasena = request.form['contrasena']
    email = request.form['email']
    telefono = request.form['telefono']

    
    contrasena_hash = generate_password_hash(contrasena)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usuarios (nombre, contrasena, email, telefono)
        VALUES (?, ?, ?, ?)
    """, (nombre, contrasena_hash, email, telefono))
    conn.commit()
    conn.close()

    flash('Usuario agregado correctamente', 'success')
    return redirect(url_for('usuarios.usuarios_home'))


@usuarios_bp.route('/eliminar/<int:id_usuario>', methods=['POST'])
def eliminar_usuario(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id_usuario = ?", id_usuario)
    conn.commit()
    conn.close()

    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('usuarios.usuarios_home'))


@usuarios_bp.route('/editar/<int:id_usuario>', methods=['POST'])
def editar_usuario(id_usuario):
    nombre = request.form['nombre']
    contrasena = request.form['contrasena']
    email = request.form['email']
    telefono = request.form['telefono']

    
    contrasena_hash = generate_password_hash(contrasena)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE usuarios
        SET nombre = ?, contrasena = ?, email = ?, telefono = ?
        WHERE id_usuario = ?
    """, (nombre, contrasena_hash, email, telefono, id_usuario))
    conn.commit()
    conn.close()

    flash('Usuario actualizado correctamente', 'success')
    return redirect(url_for('usuarios.usuarios_home'))
