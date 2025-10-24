import pyodbc
from flask import Blueprint, request, jsonify, render_template, current_app
from decimal import Decimal
import json

stock_bp = Blueprint('stock', __name__)


def fetch_inventory_data(filters):
    """
    Obtiene los datos del inventario de FarmaD aplicando filtros.
    Muestra solo las columnas: producto, cantidad, precio, y alerta.
    """
    conn = None
    try:
      
        conn = current_app.get_db_connection()
        
        if conn is None:
            
            raise RuntimeError("Error: No se pudo establecer la conexión a la base de datos.")

        
        sql_base = """
            SELECT 
                producto, 
                cantidad, 
                precio,
                alerta -- Columna corregida: Usamos 'alerta' de la tabla dbo.inventario
            FROM dbo.inventario 
        """
        
        where_clauses = []
        params = []
        
        search_type = filters.get('searchType') 
        search_value = filters.get('searchValue')

        if search_value:
            if search_type == 'producto':
               
                where_clauses.append("producto LIKE ?")
                params.append(f"%{search_value}%")
            
            elif search_type == 'precio_mayor':
                
                try:
                   
                    valor = float(search_value)
                    where_clauses.append("precio >= ?")
                    params.append(valor)
                except ValueError:
                    
                    pass 

        sql_query = sql_base
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
            
        sql_query += " ORDER BY producto ASC"

     
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        
        
        columns = [column[0].lower() for column in cursor.description]

        results = []
        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            
            
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)
            
            results.append(item)
            
        return results
        
    except pyodbc.Error as ex:
        
        sqlstate = ex.args[0]
        
        raise RuntimeError(f"Error en la base de datos: {sqlstate}. Verifique la consulta y las columnas.") from ex
    except Exception as e:
        print(f"Error general en fetch_inventory_data: {e}")
        raise RuntimeError(f"Error interno del servidor: {str(e)}") from e
    finally:
        if conn:
            conn.close()



@stock_bp.route('/inventario')
def show_inventory_page():
    """Ruta para mostrar la página web de consulta de stock."""
 
    return render_template('stockconsulta.html')

@stock_bp.route('/api/stock', methods=['GET'])
def api_stock():
    """Ruta API que devuelve los datos del inventario en formato JSON."""
    try:
        
        db_filters = {
            'searchType': request.args.get('searchType'),
            'searchValue': request.args.get('searchValue')
        }

        data_list = fetch_inventory_data(db_filters)
        
        return jsonify({"data": data_list}), 200
        
    except RuntimeError as e:
        
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"ERROR Desconocido en api_stock: {e}")
        return jsonify({"error": "Error desconocido al procesar la solicitud de stock."}), 500
