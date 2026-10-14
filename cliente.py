"""
cliente.py
----------
Cliente en consola interactivo simplificado para evaluación de PFO 2.
- Da la bienvenida e indica las credenciales por defecto.
- Permite iniciar sesión y deriva directamente a /tareas.
- Permite registrar nuevos usuarios por consola.
"""

import sys
import webbrowser
import requests

API_URL = "http://127.0.0.1:5000"
sesion_http = requests.Session()


def mostrar_bienvenida_y_tareas(usuario):
    """Consulta GET /tareas y abre el navegador con la vista de bienvenida."""
    print(f"\n🌐 Derivando a /tareas para {usuario}...")
    try:
        resp = sesion_http.get(f"{API_URL}/tareas")
        if resp.status_code == 200:
            print("✅ Respuesta HTTP 200 OK recibida de /tareas.")
            print(f"🖥️ Abriendo vista HTML con Bootstrap en tu navegador: {API_URL}/tareas")
            try:
                webbrowser.open(f"{API_URL}/tareas")
            except Exception:
                pass

        # Menú interactivo de gestión CRUD de tareas
        while True:
            resp_api = sesion_http.get(f"{API_URL}/api/tareas")
            if resp_api.status_code == 200:
                tareas = resp_api.json().get("tareas", [])
                print(f"\n📋 Tareas de '{usuario}' en SQLite:")
                if tareas:
                    for t in tareas:
                        estado = "✔ [REALIZADA]" if t.get("completada") else "⏳ [PENDIENTE]"
                        print(f"   [{t['id']}] {estado} {t['titulo']}")
                else:
                    print("   (No hay tareas registradas)")

            print("\nAcciones disponibles:")
            print("   [1] Crear nueva tarea")
            print("   [2] Cambiar estado (Pendiente ⇄ Realizada)")
            print("   [3] Eliminar tarea")
            print("   [ENTER] Volver al menú principal")

            accion = input("Seleccione acción: ").strip()
            if accion == "1":
                nueva = input("Título de la nueva tarea: ").strip()
                if nueva:
                    r = sesion_http.post(f"{API_URL}/api/tareas", json={"titulo": nueva})
                    if r.status_code == 201:
                        print(f"✅ Tarea '{nueva}' creada con éxito.")
            elif accion == "2":
                id_t = input("Ingrese el ID de la tarea a alternar estado: ").strip()
                if id_t.isdigit():
                    r = sesion_http.post(f"{API_URL}/api/tareas/{id_t}/toggle")
                    if r.status_code == 200:
                        print(f"✅ {r.json().get('mensaje')}")
                    else:
                        print("❌ Error al cambiar estado.")
            elif accion == "3":
                id_t = input("Ingrese el ID de la tarea a eliminar: ").strip()
                if id_t.isdigit():
                    r = sesion_http.delete(f"{API_URL}/api/tareas/{id_t}")
                    if r.status_code == 200:
                        print("✅ Tarea eliminada de SQLite.")
                    else:
                        print("❌ Error al eliminar tarea.")
            else:
                break

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: ¿El servidor está encendido?")


def iniciar_sesion():
    print("\n--- [1] INICIO DE SESIÓN ---")
    print("Presione [ENTER] para usar las credenciales por defecto.")
    
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
            print(f"\n✅ {datos.get('mensaje')}")
            print(f"🎉 ¡Bienvenido/a, {datos.get('usuario')}! Acceso autorizado a tareas.")
            mostrar_bienvenida_y_tareas(datos.get("usuario"))
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar con http://127.0.0.1:5000. Inicia el servidor con 'python servidor.py'.")


def registrar_usuario():
    print("\n--- [2] REGISTRAR NUEVO USUARIO ---")
    usuario = input("Ingrese nuevo nombre de usuario: ").strip()
    contrasenia = input("Ingrese nueva contraseña: ").strip()

    if not usuario or not contrasenia:
        print("❌ Error: Debe ingresar tanto usuario como contraseña.")
        return

    payload = {"usuario": usuario, "contraseña": contrasenia}

    try:
        resp = sesion_http.post(f"{API_URL}/registro", json=payload)
        datos = resp.json()

        if resp.status_code == 201:
            print(f"\n✅ {datos.get('mensaje')}")
            print("🔒 La contraseña ha sido hasheada criptográficamente y guardada en SQLite.")
            
            # Preguntar si desea iniciar sesión de inmediato
            auto = input(f"\n¿Desea iniciar sesión como '{usuario}' y entrar a /tareas ahora? (S/n): ").strip().lower()
            if auto in ("", "s", "si", "y", "yes"):
                resp_login = sesion_http.post(f"{API_URL}/login", json=payload)
                if resp_login.status_code == 200:
                    mostrar_bienvenida_y_tareas(usuario)
        else:
            print(f"❌ Error ({resp.status_code}): {datos.get('error')}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar con el servidor.")


def menu():
    while True:
        print("\n" + "=" * 62)
        print(" 👋 BIENVENIDO AL SISTEMA DE GESTIÓN DE TAREAS (PFO 2)")
        print("=" * 62)
        print(" 🔑 Credenciales por defecto para evaluación:")
        print("    • Usuario:    usuario")
        print("    • Contraseña: 12345")
        print("=" * 62)
        print("1. Iniciar sesión y entrar a /tareas (por defecto: usuario / 12345)")
        print("2. Registrar un nuevo usuario por consola (POST /registro)")
        print("3. Salir")
        print("=" * 62)

        opcion = input("Seleccione una opción (1-3): ").strip()

        if opcion == "1":
            iniciar_sesion()
        elif opcion == "2":
            registrar_usuario()
        elif opcion == "3":
            print("¡Hasta luego!")
            sys.exit(0)
        else:
            print("❌ Opción inválida. Ingrese 1, 2 o 3.")


if __name__ == "__main__":
    menu()
