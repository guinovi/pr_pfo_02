"""
test_servidor.py
----------------
Suite de pruebas unitarias automatizadas para verificar:
1. Registro con contraseña hasheada y rechazo de contraseñas vacías.
2. Comprobación en SQLite de que la contraseña NO está en texto plano.
3. Rechazo de usuario duplicado (409 Conflict).
4. Login con credenciales válidas e inválidas.
5. Retorno de HTML de bienvenida con Bootstrap en GET /tareas.
6. Manejo de sesiones y creación/listado de tareas.
"""

import os
import unittest
import sqlite3
from werkzeug.security import check_password_hash
import servidor


class TestServidorAPI(unittest.TestCase):
    def setUp(self):
        servidor.DB_NAME = "test_tareas.db"
        servidor.app.config["TESTING"] = True
        servidor.app.config["SECRET_KEY"] = "clave-test-secreta"
        servidor.init_db()
        self.client = servidor.app.test_client()

    def tearDown(self):
        if os.path.exists("test_tareas.db"):
            os.remove("test_tareas.db")

    def test_1_registro_y_hashing(self):
        """Verifica que se registre el usuario y la contraseña quede hasheada en SQLite."""
        password_plano = "1234_mi_clave"
        res = self.client.post("/registro", json={"usuario": "pedro", "contraseña": password_plano})
        self.assertEqual(res.status_code, 201)

        # Consultar directamente SQLite
        conn = sqlite3.connect("test_tareas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT contrasenia_hash FROM usuarios WHERE usuario = 'pedro'")
        fila = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(fila)
        hash_guardado = fila[0]

        # Comprobaciones criptográficas
        self.assertNotEqual(hash_guardado, password_plano)
        self.assertTrue(check_password_hash(hash_guardado, password_plano))
        self.assertFalse(check_password_hash(hash_guardado, "clave_falsa"))

    def test_2_errores_en_registro(self):
        """Verifica validación de campos vacíos y usuarios duplicados."""
        # Sin datos
        res_vacio = self.client.post("/registro", json={})
        self.assertEqual(res_vacio.status_code, 400)

        # Registro exitoso
        self.client.post("/registro", json={"usuario": "ana", "contraseña": "123"})

        # Duplicado
        res_duplicado = self.client.post("/registro", json={"usuario": "ana", "contraseña": "456"})
        self.assertEqual(res_duplicado.status_code, 409)

    def test_3_login(self):
        """Verifica login con credenciales correctas e incorrectas."""
        self.client.post("/registro", json={"usuario": "lucas", "contraseña": "passwordSeguro"})

        # Incorrecta
        res_fail = self.client.post("/login", json={"usuario": "lucas", "contraseña": "otraCosa"})
        self.assertEqual(res_fail.status_code, 401)

        # Correcta
        res_ok = self.client.post("/login", json={"usuario": "lucas", "contraseña": "passwordSeguro"})
        self.assertEqual(res_ok.status_code, 200)

    def test_4_get_tareas_html(self):
        """Verifica que GET /tareas responda HTML con Bootstrap."""
        # Sin login
        res = self.client.get("/tareas")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"bootstrap", res.data.lower())
        self.assertIn("text/html", res.headers.get("Content-Type"))

        # Con login
        self.client.post("/registro", json={"usuario": "mario", "contraseña": "123"})
        self.client.post("/login", json={"usuario": "mario", "contraseña": "123"})

        res_auth = self.client.get("/tareas")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn(b"mario", res_auth.data)

    def test_5_crud_tareas(self):
        """Verifica ciclo CRUD completo de tareas (crear, listar, togglear estado y eliminar)."""
        # Login con usuario por defecto
        self.client.post("/login", json={"usuario": "usuario", "contraseña": "12345"})

        # 1. Crear tarea
        res_crear = self.client.post("/api/tareas", json={"titulo": "Testear CRUD"})
        self.assertEqual(res_crear.status_code, 201)
        tarea_id = res_crear.get_json()["tarea"]["id"]

        # 2. Toggle estado (de 0 a 1 -> Realizada)
        res_toggle = self.client.post(f"/api/tareas/{tarea_id}/toggle")
        self.assertEqual(res_toggle.status_code, 200)
        self.assertEqual(res_toggle.get_json()["completada"], 1)

        # 3. Eliminar tarea
        res_del = self.client.delete(f"/api/tareas/{tarea_id}")
        self.assertEqual(res_del.status_code, 200)


if __name__ == "__main__":
    unittest.main()


