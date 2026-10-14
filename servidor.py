import sqlite3
from flask import Flask, request, jsonify, session, render_template, redirect
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "gestor_tareas.db"

app = Flask(__name__)
# secret_key es obligatoria en Flask para poder firmar cookies de sesión
app.secret_key = "clave-secreta-para-sesiones-pfo2"


@app.route("/")
def inicio():
    """Redirige automáticamente la ruta raíz a /tareas."""
    return redirect("/tareas")


def get_db():
    """Retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas necesarias y el usuario por defecto si no existen."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasenia_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            completada INTEGER DEFAULT 0,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    # -------------------------------------------------------------
    # USUARIO Y CONTRASEÑA POR DEFECTO PARA EVALUACIÓN
    # Usuario: usuario | Contraseña: 12345 (almacenada como hash)
    # -------------------------------------------------------------
    cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", ("usuario",))
    user_existente = cursor.fetchone()
    if not user_existente:
        hash_default = generate_password_hash("12345")
        cursor.execute(
            "INSERT INTO usuarios (usuario, contrasenia_hash) VALUES (?, ?)",
            ("usuario", hash_default)
        )
        usuario_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
            (usuario_id, "Completar entrega de PFO 2 en GitHub Pages")
        )
        cursor.execute(
            "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
            (usuario_id, "Revisar endpoints /registro, /login y /tareas")
        )

    conn.commit()
    conn.close()


def obtener_usuario_actual():
    """
    Obtiene el usuario autenticado a través de:
    1. Sesión Flask (cookies).
    2. HTTP Basic Auth (cabecera Authorization para Thunder Client / cURL).
    """
    # 1. Verificar sesión activa
    if "usuario_id" in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, usuario FROM usuarios WHERE id = ?",
            (session["usuario_id"],)
        )
        usuario_row = cursor.fetchone()
        conn.close()
        if usuario_row:
            return dict(usuario_row)

    # 2. Verificar HTTP Basic Auth (soporte para Thunder Client / APIs)
    auth = request.authorization
    if auth and auth.username and auth.password:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, usuario, contrasenia_hash FROM usuarios WHERE usuario = ?",
            (auth.username.strip(),)
        )
        usuario_row = cursor.fetchone()
        conn.close()
        if usuario_row and check_password_hash(usuario_row["contrasenia_hash"], auth.password.strip()):
            return {"id": usuario_row["id"], "usuario": usuario_row["usuario"]}

    return None


# -------------------------------------------------------------
# ENDPOINT 1: REGISTRO DE USUARIOS CON MANEJO DE ERRORES
# -------------------------------------------------------------
@app.route("/registro", methods=["POST"])
def registro():
    """
    Endpoint: POST /registro
    Recibe: {"usuario": "nombre", "contraseña": "1234"}
    (Soporta tanto JSON como formulario web).
    """
    if request.is_json:
        datos = request.get_json(silent=True) or {}
    else:
        datos = request.form

    usuario = datos.get("usuario")
    contrasenia = datos.get("contraseña") or datos.get("contrasenia") or datos.get("password")

    # Error: ¿Campos vacíos o faltantes?
    if not usuario or not str(usuario).strip():
        return jsonify({"error": "El campo 'usuario' es obligatorio y no puede estar vacío"}), 400

    if not contrasenia or not str(contrasenia).strip():
        return jsonify({"error": "El campo 'contraseña' es obligatorio y no puede estar vacío"}), 400

    usuario = str(usuario).strip()
    contrasenia = str(contrasenia).strip()

    # Hashear contraseña (¡nunca en texto plano!)
    hash_seguro = generate_password_hash(contrasenia)

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (usuario, contrasenia_hash) VALUES (?, ?)",
            (usuario, hash_seguro)
        )
        nuevo_id = cursor.lastrowid
        # Tarea de bienvenida inicial
        cursor.execute(
            "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
            (nuevo_id, f"¡Bienvenido {usuario}! Esta es tu primera tarea.")
        )
        conn.commit()

        # Si la petición fue JSON (Thunder Client / cliente.py)
        if request.is_json:
            return jsonify({
                "mensaje": "Usuario registrado exitosamente",
                "usuario": usuario,
                "siguiente_paso": "Inicia sesión en POST /login para acceder a /tareas"
            }), 201

        # Si vino de formulario web, inicia sesión y deriva a /tareas
        session["usuario_id"] = nuevo_id
        session["usuario"] = usuario
        return redirect("/tareas")

    except sqlite3.IntegrityError:
        return jsonify({"error": f"El usuario '{usuario}' ya se encuentra registrado"}), 409

    except Exception as e:
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500

    finally:
        if conn:
            conn.close()


# -------------------------------------------------------------
# ENDPOINT 2: INICIO DE SESIÓN CON MANEJO DE ERRORES
# -------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Endpoint: POST /login
    Recibe: {"usuario": "nombre", "contraseña": "1234"}
    Verifica credenciales y deriva el acceso a las tareas.
    """
    if request.method == "GET":
        return redirect("/tareas")

    if request.is_json:
        datos = request.get_json(silent=True) or {}
    else:
        datos = request.form

    usuario = datos.get("usuario")
    contrasenia = datos.get("contraseña") or datos.get("contrasenia") or datos.get("password")

    # Error: Campos faltantes
    if not usuario or not contrasenia:
        if request.is_json:
            return jsonify({"error": "Debe proporcionar 'usuario' y 'contraseña'"}), 400
        return redirect("/tareas?error=campos_faltantes")

    usuario = str(usuario).strip()
    contrasenia = str(contrasenia).strip()

    # Buscar usuario en SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, usuario, contrasenia_hash FROM usuarios WHERE usuario = ?",
        (usuario,)
    )
    fila_usuario = cursor.fetchone()
    conn.close()

    # Validar si existe y si la contraseña coincide con el hash
    if not fila_usuario or not check_password_hash(fila_usuario["contrasenia_hash"], contrasenia):
        if request.is_json:
            return jsonify({"error": "Credenciales inválidas"}), 401
        return redirect("/tareas?error=credenciales_invalidas")

    # Éxito: Guardar datos en la sesión
    session["usuario_id"] = fila_usuario["id"]
    session["usuario"] = fila_usuario["usuario"]

    # Si fue petición JSON (Thunder Client / cliente.py)
    if request.is_json:
        return jsonify({
            "mensaje": "Inicio de sesión exitoso. Credenciales verificadas.",
            "usuario": fila_usuario["usuario"],
            "acceso_tareas": "Permitido",
            "derivacion": "/tareas",
            "url_completa": "http://127.0.0.1:5000/tareas"
        }), 200

    # Si vino de formulario web, redirige directamente a /tareas
    return redirect("/tareas")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Cierra la sesión actual del usuario y deriva a /tareas."""
    session.clear()
    if request.is_json:
        return jsonify({"mensaje": "Sesión cerrada exitosamente"}), 200
    return redirect("/tareas")


# -------------------------------------------------------------
# ENDPOINT 3: GESTIÓN DE TAREAS (HTML DE BIENVENIDA)
# -------------------------------------------------------------
@app.route("/tareas", methods=["GET"])
def tareas_vista():
    """
    Endpoint: GET /tareas
    Muestra un HTML de bienvenida estilizado con Bootstrap por CDN.
    Si el usuario tiene sesión activa (o Basic Auth), muestra sus tareas en SQLite.
    """
    usuario_info = obtener_usuario_actual()
    lista_tareas = []

    if usuario_info:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, titulo, completada FROM tareas WHERE usuario_id = ? ORDER BY id DESC",
            (usuario_info["id"],)
        )
        lista_tareas = cursor.fetchall()
        conn.close()

    error_param = request.args.get("error")

    # Renderiza la plantilla con Bootstrap
    return render_template(
        "tareas.html",
        usuario=usuario_info["usuario"] if usuario_info else None,
        tareas=lista_tareas,
        error=error_param
    )


# -------------------------------------------------------------
# ENDPOINTS REST PARA GESTIÓN DE TAREAS (JSON)
# -------------------------------------------------------------
@app.route("/api/tareas", methods=["GET"])
def api_listar_tareas():
    """Retorna las tareas del usuario logueado en formato JSON."""
    usuario_info = obtener_usuario_actual()
    if not usuario_info:
        return jsonify({"error": "No autorizado. Inicie sesión primero"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, titulo, completada, fecha_creacion FROM tareas WHERE usuario_id = ? ORDER BY id DESC",
        (usuario_info["id"],)
    )
    filas = cursor.fetchall()
    conn.close()

    return jsonify({
        "usuario": usuario_info["usuario"],
        "tareas": [dict(f) for f in filas]
    }), 200


@app.route("/api/tareas", methods=["POST"])
def api_crear_tarea():
    """Crea una nueva tarea para el usuario autenticado."""
    usuario_info = obtener_usuario_actual()
    if not usuario_info:
        return jsonify({"error": "No autorizado. Inicie sesión primero"}), 401

    datos = request.get_json(silent=True) or {}
    titulo = datos.get("titulo")

    if not titulo or not str(titulo).strip():
        return jsonify({"error": "El título de la tarea es obligatorio"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
        (usuario_info["id"], str(titulo).strip())
    )
    nueva_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Tarea creada exitosamente",
        "tarea": {"id": nueva_id, "titulo": str(titulo).strip(), "completada": 0}
    }), 201


@app.route("/api/tareas/<int:tarea_id>", methods=["PUT", "PATCH"])
def api_actualizar_tarea(tarea_id):
    """Actualiza título o estado de una tarea perteneciente al usuario."""
    usuario_info = obtener_usuario_actual()
    if not usuario_info:
        return jsonify({"error": "No autorizado"}), 401

    datos = request.get_json(silent=True) or {}
    completada = datos.get("completada")
    titulo = datos.get("titulo")

    conn = get_db()
    cursor = conn.cursor()

    # Verificar que la tarea existe y pertenece al usuario
    cursor.execute("SELECT id, titulo, completada FROM tareas WHERE id = ? AND usuario_id = ?", (tarea_id, usuario_info["id"]))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        return jsonify({"error": "Tarea no encontrada o no pertenece al usuario"}), 404

    nuevo_titulo = str(titulo).strip() if titulo else tarea["titulo"]
    nuevo_estado = 1 if completada in (1, True, "1", "true") else (0 if completada in (0, False, "0", "false") else tarea["completada"])

    cursor.execute(
        "UPDATE tareas SET titulo = ?, completada = ? WHERE id = ? AND usuario_id = ?",
        (nuevo_titulo, nuevo_estado, tarea_id, usuario_info["id"])
    )
    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Tarea actualizada exitosamente",
        "tarea": {"id": tarea_id, "titulo": nuevo_titulo, "completada": nuevo_estado}
    }), 200


@app.route("/api/tareas/<int:tarea_id>/toggle", methods=["POST"])
def api_toggle_tarea(tarea_id):
    """Alterna el estado de una tarea entre pendiente (0) y realizada (1)."""
    usuario_info = obtener_usuario_actual()
    if not usuario_info:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, completada FROM tareas WHERE id = ? AND usuario_id = ?",
        (tarea_id, usuario_info["id"])
    )
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        return jsonify({"error": "Tarea no encontrada"}), 404

    nuevo_estado = 0 if tarea["completada"] == 1 else 1
    cursor.execute(
        "UPDATE tareas SET completada = ? WHERE id = ? AND usuario_id = ?",
        (nuevo_estado, tarea_id, usuario_info["id"])
    )
    conn.commit()
    conn.close()

    if request.is_json or not request.form:
        return jsonify({
            "mensaje": f"Estado cambiado a {'Realizada' if nuevo_estado else 'Pendiente'}",
            "completada": nuevo_estado
        }), 200

    return redirect("/tareas")


@app.route("/api/tareas/<int:tarea_id>", methods=["DELETE"])
@app.route("/api/tareas/<int:tarea_id>/eliminar", methods=["POST", "DELETE"])
def api_eliminar_tarea(tarea_id):
    """Elimina una tarea perteneciente al usuario autenticado."""
    usuario_info = obtener_usuario_actual()
    if not usuario_info:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tareas WHERE id = ? AND usuario_id = ?",
        (tarea_id, usuario_info["id"])
    )
    afectados = cursor.rowcount
    conn.commit()
    conn.close()

    if afectados == 0:
        return jsonify({"error": "Tarea no encontrada o no pertenece al usuario"}), 404

    if request.is_json or not request.form or request.method == "DELETE":
        return jsonify({"mensaje": "Tarea eliminada exitosamente"}), 200

    return redirect("/tareas")



if __name__ == "__main__":
    init_db()
    print("🚀 Servidor iniciado en http://127.0.0.1:5000")
    print("📌 Credenciales por defecto: usuario / 12345")
    app.run(host="0.0.0.0", port=5000, debug=True)

