"""
cliente.py
----------
Cliente interactivo en consola para el Sistema de Gestión de Tareas (PFO 2).
Interactúa con todos los endpoints de la API Flask mediante peticiones HTTP.
"""

import sys
import webbrowser
import requests

API_URL = "http://127.0.0.1:5000"
sesion_http = requests.Session()
usuario_actual = None


def iniciar_sesion():
    global usuario_actual
    print("\n--- [1] INICIO DE SESIÓN (POST /login) ---")
    print("ℹ️ Presione [ENTER] para usar las credenciales de evaluación.")

    usuario = input("Usuario [defecto: usuario]: ").strip()
    if not usuario:
        usuario = "usuario"

    contrasenia = input("Contraseña [defecto: 12345]: ").strip()
    if not contrasenia:
        contrasenia = "12345"

    payload = {"usuario": usuario, "contraseña": contrasenia}

    try:
        resp = sesion_http.post(f"{API_URL}/login", json=payload)
        datos = resp.json()

        if resp.status_code == 200:
            usuario_actual = datos.get("usuario")
            print(f"\n✅ {datos.get('mensaje')}")
            print(f"🎉 ¡Bienvenido/a, {usuario_actual}! Sesión iniciada correctamente.")

            # Derivar a /tareas y abrir navegador
            ver_html_bienvenida(abrir_navegador=True)
            listar_tareas()
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar con el servidor. Ejecuta 'python servidor.py'.")


def registrar_usuario():
    print("\n--- [2] REGISTRAR NUEVO USUARIO (POST /registro) ---")
    usuario = input("Ingrese nombre de usuario: ").strip()
    contrasenia = input("Ingrese contraseña: ").strip()

    if not usuario or not contrasenia:
        print("❌ Error: Ambos campos son obligatorios.")
        return

    payload = {"usuario": usuario, "contraseña": contrasenia}

    try:
        resp = sesion_http.post(f"{API_URL}/registro", json=payload)
        datos = resp.json()

        if resp.status_code == 201:
            print(f"\n✅ {datos.get('mensaje')}")
            print("🔒 Contraseña hasheada criptográficamente con sal y guardada en SQLite.")
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión con el servidor.")


def ver_html_bienvenida(abrir_navegador=True):
    print("\n--- [3] CONSULTAR HTML DE BIENVENIDA (GET /tareas) ---")
    try:
        resp = sesion_http.get(f"{API_URL}/tareas")
        if resp.status_code == 200:
            print("✅ Respuesta recibida exitosamente (Código 200 OK).")
            print(f"Tipo de contenido: {resp.headers.get('Content-Type')}")

            if abrir_navegador:
                print(f"🌐 Abriendo {API_URL}/tareas en tu navegador...")
                try:
                    webbrowser.open(f"{API_URL}/tareas")
                except Exception:
                    pass

            print("\n[Vista previa de la plantilla HTML]:")
            lineas = resp.text.strip().splitlines()
            for linea in lineas[:15]:
                print(linea)
            if len(lineas) > 15:
                print("... (HTML truncado para la consola)")
        else:
            print(f"❌ Error al consultar /tareas: {resp.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión con el servidor.")


def listar_tareas():
    print("\n--- [4] LISTAR MIS TAREAS (GET /api/tareas) ---")
    try:
        resp = sesion_http.get(f"{API_URL}/api/tareas")
        if resp.status_code == 200:
            datos = resp.json()
            tareas = datos.get("tareas", [])
            print(f"📋 Tareas registradas en SQLite de '{datos.get('usuario')}':")
            if tareas:
                for t in tareas:
                    estado = "✔ [REALIZADA]" if t.get("completada") else "⏳ [PENDIENTE]"
                    print(f"   [{t['id']}] {estado} {t['titulo']}")
            else:
                print("   (No hay tareas registradas)")
            return tareas
        elif resp.status_code == 401:
            print("🔒 Debe iniciar sesión primero para ver sus tareas (Opción 1).")
        else:
            print(f"❌ Error ({resp.status_code}): {resp.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión.")
    return []


def crear_tarea():
    print("\n--- [5] CREAR NUEVA TAREA (POST /api/tareas) ---")
    titulo = input("Título de la nueva tarea: ").strip()
    if not titulo:
        print("❌ El título no puede estar vacío.")
        return

    try:
        resp = sesion_http.post(f"{API_URL}/api/tareas", json={"titulo": titulo})
        datos = resp.json()

        if resp.status_code == 201:
            print(f"✅ {datos.get('mensaje')} (ID: {datos['tarea']['id']})")
        elif resp.status_code == 401:
            print("🔒 Debe iniciar sesión primero (Opción 1).")
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión.")


def cambiar_estado_tarea():
    print("\n--- [6] CAMBIAR ESTADO DE TAREA (POST /api/tareas/:id/toggle) ---")
    id_t = input("Ingrese el ID de la tarea a alternar estado (Pendiente ⇄ Realizada): ").strip()
    if not id_t.isdigit():
        print("❌ Debe ingresar un número de ID válido.")
        return

    try:
        resp = sesion_http.post(f"{API_URL}/api/tareas/{id_t}/toggle")
        datos = resp.json()

        if resp.status_code == 200:
            print(f"✅ {datos.get('mensaje')}")
        elif resp.status_code == 401:
            print("🔒 Debe iniciar sesión primero.")
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión.")


def eliminar_tarea():
    print("\n--- [7] ELIMINAR TAREA (DELETE /api/tareas/:id) ---")
    id_t = input("Ingrese el ID de la tarea a eliminar: ").strip()
    if not id_t.isdigit():
        print("❌ Debe ingresar un número de ID válido.")
        return

    try:
        resp = sesion_http.delete(f"{API_URL}/api/tareas/{id_t}")
        datos = resp.json()

        if resp.status_code == 200:
            print("✅ Tarea eliminada exitosamente de SQLite.")
        elif resp.status_code == 401:
            print("🔒 Debe iniciar sesión primero.")
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión.")


def cerrar_sesion():
    global usuario_actual
    print("\n--- [8] CERRAR SESIÓN (POST /logout) ---")
    try:
        resp = sesion_http.post(f"{API_URL}/logout")
        if resp.status_code == 200:
            print("👋 Sesión cerrada exitosamente en el servidor.")
            usuario_actual = None
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión.")


def menu():
    while True:
        sesion_info = f"Sesión activa: {usuario_actual}" if usuario_actual else "No autenticado"
        print("\n" + "=" * 62)
        print(" SISTEMA DE GESTIÓN DE TAREAS - CLIENTE CLI (PFO 2)")
        print(f" [{sesion_info}]")
        print("=" * 62)
        print(" 🔑 Credenciales por defecto: usuario / 12345")
        print("=" * 62)
        print(" 1. Iniciar sesión (POST /login)")
        print(" 2. Registrar nuevo usuario (POST /registro)")
        print(" 3. Ver HTML de bienvenida (GET /tareas)")
        print(" 4. Listar mis tareas (GET /api/tareas)")
        print(" 5. Crear nueva tarea (POST /api/tareas)")
        print(" 6. Cambiar estado de tarea (Pendiente ⇄ Realizada)")
        print(" 7. Eliminar tarea (DELETE /api/tareas/:id)")
        print(" 8. Cerrar sesión (POST /logout)")
        print(" 9. Salir")
        print("=" * 62)

        opcion = input("Seleccione una opción (1-9): ").strip()

        if opcion == "1":
            iniciar_sesion()
        elif opcion == "2":
            registrar_usuario()
        elif opcion == "3":
            ver_html_bienvenida(abrir_navegador=True)
        elif opcion == "4":
            listar_tareas()
        elif opcion == "5":
            crear_tarea()
        elif opcion == "6":
            cambiar_estado_tarea()
        elif opcion == "7":
            eliminar_tarea()
        elif opcion == "8":
            cerrar_sesion()
        elif opcion == "9":
            print("¡Hasta luego!")
            sys.exit(0)
        else:
            print("❌ Opción inválida. Ingrese un número del 1 al 9.")


if __name__ == "__main__":
    menu()
