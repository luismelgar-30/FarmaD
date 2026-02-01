import pyodbc
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

clientes = Blueprint('clientes', __name__, url_prefix='/clientes')

def get_db_connection():
    return pyodbc.connect(current_app.config['CONNECTION_STRING'])

@clientes.route('/')
def listar_clientes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_cliente, nombre, correo, telefono, identidad, edad, fecha_registro FROM clientes")
    clientes_data = cursor.fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes_data)
 

@clientes.route('/agregar', methods=['POST'])
def agregar_cliente():
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    identidad = request.form['identidad']
    edad = request.form['edad']
    fecha_registro = request.form['fecha_registro']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (nombre, correo, telefono, identidad, edad, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, correo, telefono, identidad, edad, fecha_registro))
    conn.commit()
    conn.close()

    flash('Cliente agregado correctamente', 'success')
    return redirect(url_for('clientes.listar_clientes'))


@clientes.route('/editar/<int:id_cliente>', methods=['POST'])
def editar_cliente(id_cliente):
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    identidad = request.form['identidad']
    edad = request.form['edad']
    fecha_registro = request.form['fecha_registro']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clientes 
        SET nombre=?, correo=?, telefono=?, identidad=?, edad=?, fecha_registro=?
        WHERE id_cliente=?
    """, (nombre, correo, telefono, identidad, edad, fecha_registro, id_cliente))
    conn.commit()
    conn.close()

    flash('Cliente actualizado correctamente', 'info')
    return redirect(url_for('clientes.listar_clientes'))


@clientes.route('/eliminar/<int:id_cliente>')
def eliminar_cliente(id_cliente):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id_cliente=?", (id_cliente,))
    conn.commit()
    conn.close()

    flash('Cliente eliminado correctamente', 'danger')
    return redirect(url_for('clientes.listar_clientes'))
