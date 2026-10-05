"""
cliente.py
----------
Cliente en consola interactivo que interactúa con la API REST de Gestión de Tareas.
Permite registro, inicio de sesión y administración de tareas.
"""

import sys
import requests

API_URL = "http://127.0.0.1:5000"


class ClienteAPI:
    def __init__(self, base_url=API_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.usuario_actual = None

    def registrarse(self, usuario=None, contrasenia=None):
        print("\n--- [1] REGISTRO DE USUARIO ---")
        if not usuario:
            usuario = input("Ingrese nombre de usuario: ").strip()
        if not contrasenia:
            contrasenia = input("Ingrese contraseña: ").strip()

        payload = {"usuario": usuario, "contraseña": contrasenia}
        try:
            resp = self.session.post(f"{self.base_url}/registro", json=payload)
            data = resp.json()
            if resp.status_code == 201:
                print(f"✅ {data.get('mensaje')}")
                return True
            else:
                print(f"❌ Error ({resp.status_code}): {data.get('error', resp.text)}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con el servidor: {e}")
            return False

    def iniciar_sesion(self, usuario=None, contrasenia=None):
        print("\n--- [2] INICIO DE SESIÓN ---")
        if not usuario:
            usuario = input("Ingrese usuario: ").strip()
        if not contrasenia:
            contrasenia = input("Ingrese contraseña: ").strip()

        payload = {"usuario": usuario, "contraseña": contrasenia}
        try:
            resp = self.session.post(f"{self.base_url}/login", json=payload)
            data = resp.json()
            if resp.status_code == 200:
                self.usuario_actual = data.get("usuario", usuario)
                print(f"✅ {data.get('mensaje')} - Bienvenido/a, {self.usuario_actual}!")
                return True
            else:
                print(f"❌ Error ({resp.status_code}): {data.get('error', resp.text)}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False

    def ver_bienvenida_html(self):
        print("\n--- [3] CONSULTA A GET /tareas (HTML DE BIENVENIDA) ---")
        try:
            resp = self.session.get(f"{self.base_url}/tareas")
            if resp.status_code == 200:
                print("✅ Respuesta recibida exitosamente (Código 200 OK):")
                print("Tipo de contenido:", resp.headers.get("Content-Type"))
                print("\n[Vista previa del HTML recibido]:")
                # Mostrar primeras líneas del HTML
                preview = "\n".join(resp.text.strip().splitlines()[:25])
                print(preview)
                if len(resp.text.strip().splitlines()) > 25:
                    print("... (contenido HTML truncado para la consola)")
            else:
                print(f"❌ Error al consultar /tareas: {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")

    def listar_tareas(self):
        print("\n--- [4] MIS TAREAS ---")
        try:
            resp = self.session.get(f"{self.base_url}/api/tareas")
            if resp.status_code == 200:
                datos = resp.json()
                tareas = datos.get("tareas", [])
                if not tareas:
                    print("ℹ️ No hay tareas registradas todavía.")
                    return []
                print(f"Tareas de {datos.get('usuario')}:")
                for t in tareas:
                    estado = "✔ [COMPLETADA]" if t.get("completada") else "⏳ [PENDIENTE]"
                    print(f"  [{t['id']}] {estado} {t['titulo']}")
                    if t.get("descripcion"):
                        print(f"      Descripción: {t['descripcion']}")
                    print(f"      Creada: {t.get('fecha_creacion')}")
                return tareas
            elif resp.status_code == 401:
                print("🔒 Debe iniciar sesión para ver sus tareas.")
            else:
                print(f"❌ Error: {resp.status_code} - {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        return []

    def crear_tarea(self, titulo=None, descripcion=None):
        print("\n--- [5] CREAR NUEVA TAREA ---")
        if not titulo:
            titulo = input("Título de la tarea: ").strip()
        if not descripcion:
            descripcion = input("Descripción (opcional): ").strip()

        payload = {"titulo": titulo, "descripcion": descripcion}
        try:
            resp = self.session.post(f"{self.base_url}/api/tareas", json=payload)
            if resp.status_code == 201:
                data = resp.json()
                print(f"✅ {data.get('mensaje')} (ID: {data['tarea']['id']})")
                return True
            elif resp.status_code == 401:
                print("🔒 Debe iniciar sesión para crear tareas.")
            else:
                print(f"❌ Error: {resp.status_code} - {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        return False

    def completar_tarea(self, tarea_id=None):
        print("\n--- [6] COMPLETAR TAREA ---")
        if not tarea_id:
            try:
                tarea_id = int(input("Ingrese el ID de la tarea a completar: "))
            except ValueError:
                print("❌ ID inválido")
                return False

        try:
            resp = self.session.put(
                f"{self.base_url}/api/tareas/{tarea_id}",
                json={"completada": 1}
            )
            if resp.status_code == 200:
                print("✅ Tarea marcada como completada.")
                return True
            else:
                print(f"❌ Error: {resp.status_code} - {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        return False

    def eliminar_tarea(self, tarea_id=None):
        print("\n--- [7] ELIMINAR TAREA ---")
        if not tarea_id:
            try:
                tarea_id = int(input("Ingrese el ID de la tarea a eliminar: "))
            except ValueError:
                print("❌ ID inválido")
                return False

        try:
            resp = self.session.delete(f"{self.base_url}/api/tareas/{tarea_id}")
            if resp.status_code == 200:
                print("✅ Tarea eliminada correctamente.")
                return True
            else:
                print(f"❌ Error: {resp.status_code} - {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        return False

    def cerrar_sesion(self):
        try:
            resp = self.session.post(f"{self.base_url}/logout")
            print("👋 Sesión cerrada en el servidor.")
        except Exception:
            pass
        self.usuario_actual = None
        self.session = requests.Session()


def ejecutar_demo():
    """Ejecuta una demostración automatizada de todas las funciones."""
    print("=" * 60)
    print("🚀 EJECUTANDO DEMO AUTOMATIZADA DEL CLIENTE")
    print("=" * 60)
    cliente = ClienteAPI()

    usuario_demo = "estudiante_redes"
    clave_demo = "segura123"

    print("\n1. Registrando usuario de prueba...")
    cliente.registrarse(usuario_demo, clave_demo)

    print("\n2. Intentando iniciar sesión con contraseña incorrecta...")
    cliente.iniciar_sesion(usuario_demo, "clave_erronea")

    print("\n3. Iniciando sesión con contraseña correcta...")
    cliente.iniciar_sesion(usuario_demo, clave_demo)

    print("\n4. Consultando GET /tareas (HTML de bienvenida)...")
    cliente.ver_bienvenida_html()

    print("\n5. Creando tareas de prueba...")
    cliente.crear_tarea("Estudiar Flask", "Aprender routing, sesiones y plantillas")
    cliente.crear_tarea("Configurar SQLite", "Verificar persistencia de datos y tablas")

    print("\n6. Listando tareas...")
    tareas = cliente.listar_tareas()

    if tareas:
        print("\n7. Completando la primera tarea...")
        cliente.completar_tarea(tareas[0]["id"])

        print("\n8. Volviendo a listar tareas...")
        cliente.listar_tareas()

    print("\n9. Cerrando sesión...")
    cliente.cerrar_sesion()

    print("\n" + "=" * 60)
    print("✅ DEMO FINALIZADA CON ÉXITO")
    print("=" * 60)


def menu_interactivo():
    cliente = ClienteAPI()
    while True:
        sesion_info = f"Logueado como: {cliente.usuario_actual}" if cliente.usuario_actual else "No autenticado"
        print("\n" + "=" * 50)
        print(" SISTEMA DE GESTIÓN DE TAREAS - CLIENTE CLI")
        print(f" [{sesion_info}]")
        print("=" * 50)
        print("1. Registrar nuevo usuario (POST /registro)")
        print("2. Iniciar sesión (POST /login)")
        print("3. Ver HTML de bienvenida (GET /tareas)")
        print("4. Listar mis tareas (GET /api/tareas)")
        print("5. Crear nueva tarea (POST /api/tareas)")
        print("6. Marcar tarea como completada (PUT /api/tareas/:id)")
        print("7. Eliminar tarea (DELETE /api/tareas/:id)")
        print("8. Cerrar sesión (POST /logout)")
        print("9. Salir")
        print("=" * 50)

        opcion = input("Seleccione una opción (1-9): ").strip()
        if opcion == "1":
            cliente.registrarse()
        elif opcion == "2":
            cliente.iniciar_sesion()
        elif opcion == "3":
            cliente.ver_bienvenida_html()
        elif opcion == "4":
            cliente.listar_tareas()
        elif opcion == "5":
            cliente.crear_tarea()
        elif opcion == "6":
            cliente.completar_tarea()
        elif opcion == "7":
            cliente.eliminar_tarea()
        elif opcion == "8":
            cliente.cerrar_sesion()
        elif opcion == "9":
            print("¡Hasta luego!")
            sys.exit(0)
        else:
            print("Opción inválida. Intente de nuevo.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        ejecutar_demo()
    else:
        menu_interactivo()
