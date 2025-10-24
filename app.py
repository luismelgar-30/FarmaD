import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash  # 🔒 Agregado para encriptar y verificar contraseñas

from flask import Flask, request, render_template, redirect, url_for, session, flash

from productos_crud import productos 
from proveedores_crud import proveedores 
from inventario_crud import inventario_bp
from pedidos_prov_crud import pedidos_prov

from stockconsulta  import stock_bp 
from cliente  import cliente_bp 

app = Flask(__name__)
app.secret_key = '12345' 

DRIVER = '{ODBC Driver 17 for SQL Server}'
SERVER = r'DESKTOP-06O6LRP\SQLEXPRESS' 
DATABASE = 'FarmaD'
USERNAME = 'sa'
PASSWORD = '12345' 

connection_string = (
    f'DRIVER={DRIVER};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    f'UID={USERNAME};'
    f'PWD={PASSWORD};'
)

app.config['CONNECTION_STRING'] = connection_string

def get_db_connection():
    """
    Establece la conexión a la base de datos SQL Server.
    """
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        return None

app.get_db_connection = get_db_connection 

app.register_blueprint(productos, url_prefix='/productos')
app.register_blueprint(proveedores, url_prefix='/proveedores')
app.register_blueprint(inventario_bp) 
app.register_blueprint(pedidos_prov)
app.register_blueprint(stock_bp, url_prefix='/stock') 
app.register_blueprint(cliente_bp, url_prefix='/cliente') 

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('home'))
    return render_template('inicio_menu.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password'] 
        telefono = request.form.get('telefono', None) 

        
        password_hash = generate_password_hash(password)
        
        conn = app.get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                insert_query = """
                INSERT INTO usuarios (nombre, contrasena, email, telefono) 
                VALUES (?, ?, ?, ?)
                """
                cursor.execute(insert_query, nombre, password_hash, email, telefono)
                conn.commit()
                
                
                cursor.execute("INSERT INTO roles (rol, usuario) VALUES (?, ?)", "administrador", email)
                conn.commit()

                session['email'] = email
                session['nombre'] = nombre
                session['rol'] = 'administrador'
                
                return redirect(url_for('home')) 
            except pyodbc.IntegrityError:
                flash("Error: El email ya está registrado.", 'error')
                return render_template('register.html')
            except Exception as e:
                return f"Error al registrar: {e}", 500
            finally:
                conn.close()
        return "Error de conexión a la base de datos.", 500

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el inicio de sesión."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = app.get_db_connection()
        if conn:
            cursor = conn.cursor()
            select_query = "SELECT nombre, contrasena FROM usuarios WHERE email = ?"
            cursor.execute(select_query, email)
            user = cursor.fetchone()
            
            if user and check_password_hash(user.contrasena, password):
                session['email'] = email
                session['nombre'] = user.nombre

                
                cursor.execute("SELECT rol FROM roles WHERE usuario = ?", email)
                row = cursor.fetchone()
                session['rol'] = row[0] if row else 'vendedor'
                
                conn.close()
                return redirect(url_for('home'))
            else:
                conn.close()
                flash("Email o Contraseña incorrectos.", 'error')
                return render_template('login.html')
        
        return "Error de conexión a la base de datos.", 500

    return render_template('login.html')

@app.route('/home')
def home():
    if 'email' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM roles WHERE usuario = ?", session['email'])
        row = cursor.fetchone()
        conn.close()

        user_rol = row[0] if row else 'vendedor'  
        session['rol'] = user_rol

        return render_template(
            'admin_cards.html',
            nombre=session.get('nombre', 'Usuario'),
            user_rol=user_rol
        )

    return redirect(url_for('index'))

@app.route('/cliente')
def cliente():
    """Ruta para la tienda online del cliente."""
    return render_template('cliente_tienda.html')
    
@app.route('/chat_ia.html')
def chat_ia():
    return render_template('chat_ia.html')

@app.route('/proveedores_inicio')
def proveedores_inicio():
    return redirect(url_for('proveedores.proveedores_home'))

@app.route('/inventario_inicio')
def inventario_inicio():
    return redirect(url_for('stock.show_inventory_page')) 

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('email', None)
    session.pop('nombre', None)
    session.pop('rol', None)
    return redirect(url_for('index')) 

@app.route('/conocenos.html')
def conocenos():
    return render_template('conocenos.html')

@app.route('/stockconsulta.html')
def stockconsulta():
    return render_template('stockconsulta.html')

@app.route('/registro_cliente.html')
def clientes():
    return render_template('registro_cliente.html')

@app.route('/creditos')
def creditos():
    return render_template('creditos.html')

@app.route('/manual')
def manual():
    return render_template('manual.html')


from historico_prov import historico_prov_bp
app.register_blueprint(historico_prov_bp)

from historico_inventario import historico_inventario_bp
app.register_blueprint(historico_inventario_bp)

from roles import roles_bp  
app.register_blueprint(roles_bp)  

from usuarios_crud import usuarios_bp
app.register_blueprint(usuarios_bp)

from clientes_crud import clientes
app.register_blueprint(clientes)

if __name__ == '__main__':
    app.run(debug=True)
