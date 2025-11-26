from flask import Flask, request, jsonify, render_template, Response
import pymysql
import os
import time
import subprocess  # Importamos subprocess para ejecutar comandos de Linux

app = Flask(__name__)

# --- INICIO: Tu código de Base de Datos (Sin cambios) ---
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "flaskuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "flaskpw")
DB_NAME = os.getenv("DB_NAME", "flaskdb")

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    for i in range(10):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS members (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100),
                        phone VARCHAR(20),
                        position VARCHAR(50)
                    )
                """)
            conn.commit()
            conn.close()
            print(" Database initialized successfully.")
            break
        except Exception as e:
            print(f" Waiting for database... ({i+1}/10): {e}")
            time.sleep(3)

init_db()
# --- FIN: Tu código de Base de Datos ---


# --- INICIO: Nueva funcionalidad de Cámara LIGERA (fswebcam) ---

def obtener_frame():
    """Captura un frame usando el comando ligero fswebcam."""
    # Comando optimizado para Raspberry Pi Zero:
    # -r 320x240: Resolución baja para máxima velocidad
    # --no-banner: Quita la barra de texto inferior
    # --jpeg 85: Compresión JPEG calidad 85
    # -D 0: Retraso 0
    # - : Enviar a stdout (memoria) en lugar de guardar archivo
    comando = ['fswebcam', '-r', '320x240', '--no-banner', '--jpeg', '85', '-D', '0', '-']
    try:
        # Ejecutamos el comando y capturamos la salida
        proceso = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        # Si el comando devolvió datos (la imagen en bytes)
        if proceso.stdout:
            return proceso.stdout
        else:
            return None
    except Exception as e:
        print(f"Error cámara: {e}")
        return None

def generar_stream():
    """Generador de stream para enviar al navegador."""
    while True:
        frame_bytes = obtener_frame()
        if frame_bytes:
            # Enviamos el frame en formato multipart
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # Si falla, esperamos un poco para no saturar el CPU
            time.sleep(0.5)

@app.route('/video_feed')
def video_feed():
    """Ruta para el stream de video."""
    return Response(generar_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/light', methods=['POST'])
def control_light():
    """Ruta para controlar el foco (placeholder)."""
    data = request.json
    color = data.get('color')
    if color == 'green':
        # Aquí irá la lógica para cambiar el foco a verde
        print(" Foco cambiado a VERDE")
        message = "Foco cambiado a Verde"
    elif color == 'red':
        # Aquí irá la lógica para cambiar el foco a rojo
        print(" Foco cambiado a ROJO")
        message = "Foco cambiado a Rojo"
    else:
        message = "Color no reconocido"
    return jsonify({"message": message})

# --- FIN: Nueva funcionalidad de Cámara ---


# --- INICIO: Tus rutas de API (Sin cambios) ---

@app.route('/members', methods=['GET'])
def get_members():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM members")
        result = cursor.fetchall()
    conn.close()
    return jsonify(result)

@app.route('/members', methods=['POST'])
def add_member():
    data = request.json
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO members (name, email, phone, position) VALUES (%s, %s, %s, %s)",
            (data['name'], data['email'], data['phone'], data['position'])
        )
    conn.commit()
    conn.close()
    return jsonify({"message": "Member added successfully"}), 201

@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    data = request.json
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE members SET name=%s, email=%s, phone=%s, position=%s WHERE id=%s",
            (data['name'], data['email'], data['phone'], data['position'], id)
        )
    conn.commit()
    conn.close()
    return jsonify({"message": "Member updated successfully"})

@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM members WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Member deleted successfully"})

@app.route('/')
def index():
    """Sirve la página principal con la cámara y los botones."""
    return render_template('index.html')

# --- FIN: Tus rutas de API ---

if __name__ == '__main__':
    # Debug=False es importante en producción, pero True ayuda a ver errores
    app.run(host='0.0.0.0', port=5000)
