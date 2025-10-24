import pyodbc
from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for


cliente_bp = Blueprint('cliente', __name__)

def register_new_client(client_data):
   
    conn = None
    try:
        conn = current_app.get_db_connection()
        if conn is None:
            raise RuntimeError("Error: No se pudo establecer la conexión a la base de datos.")

        cursor = conn.cursor()
        
        
        sql_insert = """
            INSERT INTO dbo.clientes (nombre, correo, telefono, identidad, edad)
            VALUES (?, ?, ?, ?, ?)
        """
        
    
        params = (
            client_data['nombre'], 
            client_data['correo'], 
            client_data['telefono'], 
            client_data['identidad'], 
            client_data['edad']
        )
        
        cursor.execute(sql_insert, params)
        conn.commit()
        
        return True
        
    except pyodbc.IntegrityError as ex:
 
        if 'UNIQUE' in str(ex):
            
            raise ValueError("El correo o el número de identidad ya están registrados.")
        raise RuntimeError(f"Error de integridad en la base de datos: {str(ex)}") from ex
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error SQL al registrar cliente: {sqlstate}")
        raise RuntimeError(f"Error en la base de datos: {sqlstate}. No se pudo registrar el cliente.") from ex
    except Exception as e:
        print(f"Error general al registrar cliente: {e}")
        raise RuntimeError(f"Error interno del servidor: {str(e)}") from e
    finally:
        if conn:
            conn.close()


@cliente_bp.route('/registro')
def show_registration_page():
    
    
    return render_template('registro_cliente.html')

@cliente_bp.route('/', methods=['GET'])
def home_page_after_registration():
    """
    Ruta de destino final (simula una pantalla de inicio o éxito).
    La URL es http://127.0.0.1:5000/cliente
    """
    return "<h1>Bienvenido(a) a FarmaD. Cliente Registrado con Éxito.</h1><p>Esta es la pantalla de inicio del cliente (ruta /cliente).</p>"


@cliente_bp.route('/api/registro', methods=['POST'])
def api_register_client():
    
    data = request.json
    

    required_fields = ['nombre', 'correo', 'telefono', 'identidad', 'edad']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "message": "Ey, le faltan campos obligatorios."}), 400

    try:
  
        try:
            data['edad'] = int(data['edad'])
        except ValueError:
            return jsonify({"success": False, "message": "La edad debe ser un número entero válido."}), 400
        
       
        register_new_client(data)
        

        return jsonify({
            "success": True, 
            "message": "Cliente registrado exitosamente.", 
            "redirect_url": url_for('cliente.home_page_after_registration')
        }), 201

    except ValueError as e:
        
        return jsonify({"success": False, "message": str(e)}), 409 
    except RuntimeError as e:
       
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        print(f"Error inesperado en el API de registro: {e}")
        return jsonify({"success": False, "message": "Error interno del servidor."}), 500
