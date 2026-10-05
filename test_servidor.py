"""
test_servidor.py
----------------
Suite de pruebas automatizadas para verificar:
1. Registro con contraseña hasheada en SQLite.
2. Comprobación de que la contraseña NO se guarda en texto plano.
3. Login exitoso y rechazo de credenciales incorrectas.
4. Consulta a GET /tareas (HTML de bienvenida).
5. Persistencia y aislamiento de tareas en SQLite.
"""

import os
import unittest
import sqlite3
from werkzeug.security import check_password_hash
import servidor

class TestServidorAPI(unittest.TestCase):
    def setUp(self):
        # Base de datos de prueba en memoria o archivo temporal
        servidor.DB_FILE = "test_gestor_tareas.db"
        servidor.app.config["TESTING"] = True
        servidor.app.config["SECRET_KEY"] = "clave-test"
        servidor.init_db()
        self.client = servidor.app.test_client()

    def tearDown(self):
        if os.path.exists("test_gestor_tareas.db"):
            os.remove("test_gestor_tareas.db")

    def test_1_registro_y_hashing_seguro(self):
        """Verifica que el usuario se registre y que la contraseña esté hasheada (no en texto plano)."""
        password_original = "1234_mi_clave_secreta"
        response = self.client.post("/registro", json={
            "usuario": "carlos",
            "contraseña": password_original
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("registrado exitosamente", response.get_json()["mensaje"])

        # Verificar directamente en la base de datos SQLite
        conn = sqlite3.connect("test_gestor_tareas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT contrasenia_hash FROM usuarios WHERE usuario = 'carlos'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        stored_hash = row[0]

        # 1. NO debe ser igual a la contraseña en texto plano
        self.assertNotEqual(stored_hash, password_original)
        # 2. Debe verificarse correctamente usando check_password_hash
        self.assertTrue(check_password_hash(stored_hash, password_original))
        # 3. No debe coincidir con otra contraseña
        self.assertFalse(check_password_hash(stored_hash, "clave_incorrecta"))

    def test_2_registro_usuario_duplicado(self):
        """Verifica que no se permita registrar el mismo usuario dos veces."""
        self.client.post("/registro", json={"usuario": "ana", "contraseña": "123"})
        response = self.client.post("/registro", json={"usuario": "ana", "contraseña": "456"})
        self.assertEqual(response.status_code, 409)

    def test_3_login_correcto_e_incorrecto(self):
        """Verifica el endpoint de login con credenciales válidas e inválidas."""
        self.client.post("/registro", json={"usuario": "lucia", "contraseña": "miPassword123"})

        # Login incorrecto
        res_fail = self.client.post("/login", json={"usuario": "lucia", "contraseña": "passwordErroneo"})
        self.assertEqual(res_fail.status_code, 401)

        # Login correcto
        res_ok = self.client.post("/login", json={"usuario": "lucia", "contraseña": "miPassword123"})
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn("Inicio de sesión exitoso", res_ok.get_json()["mensaje"])

    def test_4_get_tareas_html(self):
        """Verifica que GET /tareas devuelva el HTML de bienvenida."""
        # Sin iniciar sesión
        res = self.client.get("/tareas")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Bienvenido al Gestor de Tareas", res.data)
        self.assertIn(b"text/html", res.headers["Content-Type"].encode())

        # Con sesión iniciada
        self.client.post("/registro", json={"usuario": "martin", "contraseña": "123"})
        self.client.post("/login", json={"usuario": "martin", "contraseña": "123"})

        res_auth = self.client.get("/tareas")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn(b"martin", res_auth.data)

    def test_5_gestion_tareas_api(self):
        """Verifica creación y consulta de tareas protegidas por autenticación."""
        # Intento sin autenticar
        res_unauth = self.client.get("/api/tareas")
        self.assertEqual(res_unauth.status_code, 401)

        # Autenticar
        self.client.post("/registro", json={"usuario": "pedro", "contraseña": "123"})
        self.client.post("/login", json={"usuario": "pedro", "contraseña": "123"})

        # Crear tarea
        res_crear = self.client.post("/api/tareas", json={
            "titulo": "Preparar informe de redes",
            "descripcion": "Completar entrega de PFO 2"
        })
        self.assertEqual(res_crear.status_code, 201)
        tarea_id = res_crear.get_json()["tarea"]["id"]

        # Listar tareas
        res_lista = self.client.get("/api/tareas")
        self.assertEqual(res_lista.status_code, 200)
        tareas = res_lista.get_json()["tareas"]
        self.assertEqual(len(tareas), 1)
        self.assertEqual(tareas[0]["titulo"], "Preparar informe de redes")


if __name__ == "__main__":
    unittest.main()
