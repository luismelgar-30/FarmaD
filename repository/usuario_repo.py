import pyodbc
from datetime import datetime


SERVER = 'localhost\\SQLEXPRESS' 
DATABASE = 'FarmaDigital'
USERNAME = 'sa'
PASSWORD = '12345'
CONNECTION_STRING = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    f'UID={USERNAME};'
    f'PWD={PASSWORD}'
)

class UsuarioRepo:
    def __init__(self):
        self.conn = pyodbc.connect(CONNECTION_STRING)
        self.cursor = self.conn.cursor()

    def verificar_credenciales(self, email, contrasena):
        
        
        query = "SELECT id_usuario, id_rol FROM Usuarios WHERE email = ? AND contrasena = ?"
        
        self.cursor.execute(query, (email, contrasena))
        resultado = self.cursor.fetchone()
        
        if resultado:
            
            return {'id': resultado[0], 'id_rol': resultado[1]}
        return None

    def crear_usuario(self, nombre_usuario, contrasena, id_rol, email, telefono):
        
        
        
        fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        
        insert_query = """
        INSERT INTO Usuarios (nombre_usuario, contrasena, id_rol, email, fecha_creacion, telefono)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            
            self.cursor.execute(insert_query, (nombre_usuario, contrasena, id_rol, email, fecha_creacion, telefono))
            self.conn.commit()
            return True
        except Exception as e:
           
            print(f"Error al crear usuario: {e}")
            self.conn.rollback()
            return False