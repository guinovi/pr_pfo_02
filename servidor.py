"""
servidor.py
-----------
API REST con Flask y SQLite para el Sistema de Gestión de Tareas (PFO 2).
Implementa registro con contraseñas hasheadas, login y gestión de tareas.
"""

import os
import sqlite3
from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-clave-secreta-pfo2-redes")

DB_FILE = "gestor_tareas.db"


def get_db_connection():
    """Retorna una conexión a la base de datos SQLite con filas accesibles como dicts."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa las tablas de la base de datos si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasenia_hash TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de tareas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            completada INTEGER DEFAULT 0,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def obtener_usuario_autenticado():
    """
    Obtiene el usuario autenticado ya sea mediante sesión (cookie)
    o mediante autenticación básica HTTP (Basic Auth).
    """
    # 1. Verificar sesión Flask
    if "usuario_id" in session:
        conn = get_db_connection()
        usuario_row = conn.execute(
            "SELECT id, usuario FROM usuarios WHERE id = ?", (session["usuario_id"],)
        ).fetchone()
        conn.close()
        if usuario_row:
            return dict(usuario_row)

    # 2. Verificar HTTP Basic Auth (si se envía en la cabecera Authorization)
    auth = request.authorization
    if auth and auth.username and auth.password:
        conn = get_db_connection()
        usuario_row = conn.execute(
            "SELECT id, usuario, contrasenia_hash FROM usuarios WHERE usuario = ?",
            (auth.username,),
        ).fetchone()
        conn.close()
        if usuario_row and check_password_hash(usuario_row["contrasenia_hash"], auth.password):
            return {"id": usuario_row["id"], "usuario": usuario_row["usuario"]}

    return None


@app.route("/")
def index():
    """Ruta raíz que redirige o informa sobre los endpoints."""
    return jsonify({
        "proyecto": "PFO 2: Sistema de Gestión de Tareas con API y Base de Datos",
        "endpoints": {
            "POST /registro": "Registro de usuarios con contraseña hasheada",
            "POST /login": "Inicio de sesión",
            "GET /tareas": "HTML de bienvenida y visualización de tareas",
            "GET /api/tareas": "Listar tareas del usuario (JSON)",
            "POST /api/tareas": "Crear nueva tarea (JSON)",
            "POST /logout": "Cerrar sesión"
        }
    })


@app.route("/registro", methods=["POST"])
def registro():
    """
    Endpoint: POST /registro
    Recibe: {"usuario": "nombre", "contraseña": "1234"}
    Almacena el usuario con su contraseña hasheada en SQLite.
    """
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario")
    contrasenia = data.get("contraseña") or data.get("contrasenia") or data.get("password")

    if not usuario or not contrasenia:
        return jsonify({
            "error": "Parámetros incompletos. Debe proporcionar 'usuario' y 'contraseña'."
        }), 400

    # Hashear contraseña de forma segura (PBKDF2/scrypt con sal automática)
    contrasenia_hash = generate_password_hash(contrasenia)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (usuario, contrasenia_hash) VALUES (?, ?)",
            (usuario.strip(), contrasenia_hash),
        )
        conn.commit()
        return jsonify({
            "mensaje": "Usuario registrado exitosamente",
            "usuario": usuario.strip()
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"El usuario '{usuario}' ya existe"}), 409
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    """
    Endpoint: POST /login
    Recibe: {"usuario": "nombre", "contraseña": "1234"}
    Verifica credenciales contra el hash almacenado y permite acceso.
    """
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario")
    contrasenia = data.get("contraseña") or data.get("contrasenia") or data.get("password")

    if not usuario or not contrasenia:
        return jsonify({
            "error": "Debe proporcionar 'usuario' y 'contraseña'."
        }), 400

    conn = get_db_connection()
    user_row = conn.execute(
        "SELECT id, usuario, contrasenia_hash FROM usuarios WHERE usuario = ?",
        (usuario.strip(),),
    ).fetchone()
    conn.close()

    if user_row and check_password_hash(user_row["contrasenia_hash"], contrasenia):
        # Establecer sesión
        session["usuario_id"] = user_row["id"]
        session["usuario"] = user_row["usuario"]
        return jsonify({
            "mensaje": "Inicio de sesión exitoso",
            "usuario": user_row["usuario"]
        }), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401


@app.route("/logout", methods=["POST", "GET"])
def logout():
    """Cierra la sesión actual."""
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada correctamente"}), 200


@app.route("/tareas", methods=["GET"])
def tareas_vista():
    """
    Endpoint: GET /tareas
    Muestra un HTML de bienvenida (con las tareas del usuario si está autenticado).
    """
    user = obtener_usuario_autenticado()
    tareas = []

    if user:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT id, titulo, descripcion, completada, fecha_creacion FROM tareas WHERE usuario_id = ? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
        conn.close()
        tareas = [dict(r) for r in rows]

    return render_template(
        "tareas.html",
        usuario=user["usuario"] if user else None,
        tareas=tareas
    )


@app.route("/api/tareas", methods=["GET"])
def api_listar_tareas():
    """Lista las tareas del usuario autenticado en formato JSON."""
    user = obtener_usuario_autenticado()
    if not user:
        return jsonify({"error": "No autorizado. Inicie sesión primero."}), 401

    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, titulo, descripcion, completada, fecha_creacion FROM tareas WHERE usuario_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()
    conn.close()

    tareas = [dict(r) for r in rows]
    return jsonify({
        "usuario": user["usuario"],
        "tareas": tareas
    }), 200


@app.route("/api/tareas", methods=["POST"])
def api_crear_tarea():
    """Crea una nueva tarea para el usuario autenticado."""
    user = obtener_usuario_autenticado()
    if not user:
        return jsonify({"error": "No autorizado. Inicie sesión primero."}), 401

    data = request.get_json(silent=True) or {}
    titulo = data.get("titulo")
    descripcion = data.get("descripcion", "")

    if not titulo:
        return jsonify({"error": "El campo 'titulo' es obligatorio."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tareas (usuario_id, titulo, descripcion) VALUES (?, ?, ?)",
        (user["id"], titulo.strip(), descripcion.strip()),
    )
    tarea_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Tarea creada exitosamente",
        "tarea": {
            "id": tarea_id,
            "titulo": titulo.strip(),
            "descripcion": descripcion.strip(),
            "completada": 0
        }
    }), 201


@app.route("/api/tareas/<int:tarea_id>", methods=["PUT"])
def api_actualizar_tarea(tarea_id):
    """Actualiza una tarea (por ejemplo marcar como completada)."""
    user = obtener_usuario_autenticado()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json(silent=True) or {}
    completada = 1 if data.get("completada") in (1, True, "true", "1") else 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tareas SET completada = ? WHERE id = ? AND usuario_id = ?",
        (completada, tarea_id, user["id"]),
    )
    modificados = cursor.rowcount
    conn.commit()
    conn.close()

    if modificados == 0:
        return jsonify({"error": "Tarea no encontrada o no pertenece al usuario"}), 404

    return jsonify({"mensaje": "Tarea actualizada correctamente"}), 200


@app.route("/api/tareas/<int:tarea_id>", methods=["DELETE"])
def api_eliminar_tarea(tarea_id):
    """Elimina una tarea del usuario autenticado."""
    user = obtener_usuario_autenticado()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tareas WHERE id = ? AND usuario_id = ?",
        (tarea_id, user["id"]),
    )
    modificados = cursor.rowcount
    conn.commit()
    conn.close()

    if modificados == 0:
        return jsonify({"error": "Tarea no encontrada o no pertenece al usuario"}), 404

    return jsonify({"mensaje": "Tarea eliminada correctamente"}), 200


if __name__ == "__main__":
    init_db()
    print("🚀 Servidor de Gestión de Tareas iniciado en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
