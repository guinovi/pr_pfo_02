# PFO 2: Sistema de Gestión de Tareas con API y Base de Datos

Este proyecto implementa una **API REST** desarrollada en **Python con Flask**, persistencia de datos relacionales en **SQLite**, protección criptográfica de contraseñas mediante **hashing con sal** (scrypt/PBKDF2) y un **cliente interactivo por consola** para la administración de usuarios y tareas.

---

## 📌 Tabla de Contenidos
1. [Objetivos y Requisitos Técnicos](#-objetivos-y-requisitos-técnicos)
2. [Estructura del Proyecto](#-estructura-del-proyecto)
3. [Instalación y Configuración](#-instalación-y-configuración)
4. [Ejecución del Servidor y Cliente](#-ejecución-del-servidor-y-cliente)
5. [Endpoints de la API](#-endpoints-de-la-api)
6. [Pruebas con cURL](#-pruebas-con-curl)
7. [Evidencias de Pruebas Exitosas](#-evidencias-de-pruebas-exitosas)
8. [Respuestas a Preguntas Conceptuales](#-respuestas-a-preguntas-conceptuales)
9. [Alojamiento en GitHub Pages](#-alojamiento-en-github-pages)

---

## 🎯 Objetivos y Requisitos Técnicos

- **API REST con endpoints funcionales:** Rutas para registro (`POST /registro`), inicio de sesión (`POST /login`), vista HTML (`GET /tareas`) y gestión de tareas (`/api/tareas`).
- **Autenticación segura:** Manejo de sesiones y cabeceras de autenticación con contraseñas hasheadas (¡nunca en texto plano!) mediante `werkzeug.security`.
- **Persistencia en SQLite:** Base de datos relacional local (`gestor_tareas.db`) con tablas para `usuarios` y `tareas`.
- **Cliente en consola:** Interfaz CLI interactiva (`cliente.py`) con soporte para sesiones HTTP persistentes (`requests.Session`).

---

## 📂 Estructura del Proyecto

```text
tp2/
├── servidor.py          # API REST con Flask y conexión SQLite
├── cliente.py           # Cliente interactivo por consola (menú CLI y modo --demo)
├── test_servidor.py     # Suite de pruebas unitarias automatizadas (unittest)
├── templates/
│   └── tareas.html      # Plantilla HTML de bienvenida para GET /tareas
├── requirements.txt     # Dependencias del proyecto (Flask, Werkzeug, Requests)
├── .gitignore           # Exclusión de entornos virtuales, caches y DB de pruebas
├── index.html           # Documentación web interactiva y simulador para GitHub Pages
├── docs/
│   └── index.html       # Copia para despliegue desde carpeta /docs en GitHub Pages
├── consignas.md         # Consigna oficial de la cátedra
└── README.md            # Documentación general y respuestas conceptuales
```

---

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd tp2
```

### 2. Crear y activar entorno virtual
En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

En Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 🚀 Ejecución del Servidor y Cliente

### Iniciar el Servidor API
En una terminal:
```bash
python3 servidor.py
```
El servidor quedará a la escucha en: `http://127.0.0.1:5000`

### Iniciar el Cliente en Consola (Interactivo)
En otra terminal (con el entorno virtual activo):
```bash
python3 cliente.py
```
Se presentará un menú interactivo:
```text
==================================================
 SISTEMA DE GESTIÓN DE TAREAS - CLIENTE CLI
 [No autenticado]
==================================================
1. Registrar nuevo usuario (POST /registro)
2. Iniciar sesión (POST /login)
3. Ver HTML de bienvenida (GET /tareas)
4. Listar mis tareas (GET /api/tareas)
5. Crear nueva tarea (POST /api/tareas)
6. Marcar tarea como completada (PUT /api/tareas/:id)
7. Eliminar tarea (DELETE /api/tareas/:id)
8. Cerrar sesión (POST /logout)
9. Salir
==================================================
```

### Ejecutar Demo Automatizada del Cliente
Para realizar una prueba completa de principio a fin de forma automática:
```bash
python3 cliente.py --demo
```

### Ejecutar Pruebas Unitarias
```bash
python3 test_servidor.py
```

---

## 📡 Endpoints de la API

| Método | Endpoint | Descripción | Requiere Autenticación |
|---|---|---|---|
| `POST` | `/registro` | Registra usuario con contraseña hasheada en SQLite | No |
| `POST` | `/login` | Valida credenciales e inicia sesión | No |
| `POST` | `/logout` | Cierra la sesión activa | Sí |
| `GET` | `/tareas` | Muestra página HTML de bienvenida (y tareas si está autenticado) | No (opcional para ver tareas) |
| `GET` | `/api/tareas` | Retorna listado de tareas del usuario en formato JSON | Sí |
| `POST` | `/api/tareas` | Crea una nueva tarea para el usuario | Sí |
| `PUT` | `/api/tareas/<id>` | Actualiza estado de una tarea (ej: completada) | Sí |
| `DELETE` | `/api/tareas/<id>` | Elimina una tarea | Sí |

---

## 🧪 Pruebas con cURL

### 1. Registro de Usuario (`POST /registro`)
```bash
curl -i -X POST http://127.0.0.1:5000/registro \
  -H "Content-Type: application/json" \
  -d '{"usuario": "usuario1", "contraseña": "claveSegura123"}'
```
**Respuesta:** `201 Created`
```json
{
  "mensaje": "Usuario registrado exitosamente",
  "usuario": "usuario1"
}
```

### 2. Inicio de Sesión (`POST /login`)
Guardando la cookie de sesión en `cookies.txt`:
```bash
curl -i -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "usuario1", "contraseña": "claveSegura123"}' \
  -c cookies.txt
```
**Respuesta:** `200 OK`
```json
{
  "mensaje": "Inicio de sesión exitoso",
  "usuario": "usuario1"
}
```

### 3. Consulta de Bienvenida (`GET /tareas`)
```bash
curl -i http://127.0.0.1:5000/tareas -b cookies.txt
```
**Respuesta:** `200 OK` con `Content-Type: text/html; charset=utf-8` y el documento HTML renderizado.

### 4. Crear Tarea (`POST /api/tareas`)
```bash
curl -i -X POST http://127.0.0.1:5000/api/tareas \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"titulo": "Hacer informe de redes", "descripcion": "Detallar persistencia y hash"}'
```

### 5. Listar Tareas (`GET /api/tareas`)
```bash
curl -i http://127.0.0.1:5000/api/tareas -b cookies.txt
```

---

## 📸 Evidencias de Pruebas Exitosas

### 1. Suite de Pruebas Automatizadas (`test_servidor.py`)
```text
$ python3 test_servidor.py
.....
----------------------------------------------------------------------
Ran 5 tests in 2.129s

OK
```
*Las 5 pruebas verificaron:*
- Registro correcto.
- Comprobación de contraseña hasheada y verificación criptográfica.
- Bloqueo de duplicados.
- Validación de login correcto y rechazo ante credenciales erróneas.
- Renderizado de `/tareas` (HTML).
- Aislamiento de tareas por usuario.

### 2. Verificación de Contraseña Hasheada en SQLite
Al consultar directamente el archivo `gestor_tareas.db`:
```sql
SELECT id, usuario, contrasenia_hash FROM usuarios;
```
Resultado:
```text
(1, 'estudiante_redes', 'scrypt:32768:8:1$f3KS1LG04KC03Sc7$9ca769fb47820513330674d6f24a746cd4794d89bd7e1587b99d6b298aa0a15bc43536c753a137e41688960ba7b163b3efd352964749d57e0ec1f7d5ea061e2a')
```
> **Nota clave:** La contraseña original ingresada (`segura123`) nunca fue guardada en texto plano; en su lugar, se almacenó un hash criptográfico salteado con algoritmo `scrypt`.

### 3. Ejecución de la Demo Automatizada (`cliente.py --demo`)
```text
============================================================
🚀 EJECUTANDO DEMO AUTOMATIZADA DEL CLIENTE
============================================================

1. Registrando usuario de prueba...
--- [1] REGISTRO DE USUARIO ---
✅ Usuario registrado exitosamente

2. Intentando iniciar sesión con contraseña incorrecta...
--- [2] INICIO DE SESIÓN ---
❌ Error (401): Credenciales inválidas

3. Iniciando sesión con contraseña correcta...
--- [2] INICIO DE SESIÓN ---
✅ Inicio de sesión exitoso - Bienvenido/a, estudiante_redes!

4. Consultando GET /tareas (HTML de bienvenida)...
--- [3] CONSULTA A GET /tareas (HTML DE BIENVENIDA) ---
✅ Respuesta recibida exitosamente (Código 200 OK):
Tipo de contenido: text/html; charset=utf-8

5. Creando tareas de prueba...
--- [5] CREAR NUEVA TAREA ---
✅ Tarea creada exitosamente (ID: 1)
--- [5] CREAR NUEVA TAREA ---
✅ Tarea creada exitosamente (ID: 2)

6. Listando tareas...
--- [4] MIS TAREAS ---
Tareas de estudiante_redes:
  [2] ⏳ [PENDIENTE] Configurar SQLite
  [1] ⏳ [PENDIENTE] Estudiar Flask

7. Completando la primera tarea...
--- [6] COMPLETAR TAREA ---
✅ Tarea marcada como completada.

8. Volviendo a listar tareas...
--- [4] MIS TAREAS ---
Tareas de estudiante_redes:
  [2] ✔ [COMPLETADA] Configurar SQLite
  [1] ⏳ [PENDIENTE] Estudiar Flask

9. Cerrando sesión...
👋 Sesión cerrada en el servidor.
============================================================
✅ DEMO FINALIZADA CON ÉXITO
============================================================
```

---

## 💡 Respuestas a Preguntas Conceptuales

### 1. ¿Por qué hashear contraseñas?

Hashear contraseñas es el estándar fundamental e innegociable de la seguridad informática para la gestión de identidades y credenciales:

1. **Naturaleza Unidireccional (One-Way Function):**
   A diferencia del cifrado (que es bidireccional y posee una clave de descifrado), una función de hash criptográfica está diseñada para ser irreversible. A partir del valor hash resultante es matemáticamente inviable reconstruir la contraseña original.
2. **Protección ante Filtraciones de Base de Datos (Data Breaches):**
   Si la base de datos es vulnerada o filtrada (por fallos de inyección SQL, backups expuestos, acceso no autorizado a los servidores de almacenamiento, etc.), los atacantes únicamente obtienen cadenas de hashes. Las contraseñas reales de los usuarios permanecen protegidas.
3. **Defensa contra la Reutilización de Contraseñas:**
   La gran mayoría de los usuarios utiliza la misma contraseña (o variantes mínimas) en múltiples plataformas (correos, servicios bancarios, redes sociales). Si una aplicación almacena contraseñas en texto plano y sufre una brecha, pone en riesgo directo la identidad del usuario en todos los demás servicios de Internet.
4. **Incorporación de Sal (Salting) contra Rainbow Tables:**
   Librerías como `werkzeug.security` aplican automáticamente una "sal" criptográfica (secuencia aleatoria única por cada usuario) antes de calcular el hash. Esto garantiza dos ventajas cruciales:
   - Si dos usuarios tienen la misma contraseña, sus hashes resultantes serán totalmente distintos.
   - Invalida los ataques mediante **Tablas Arcoíris** (*Rainbow Tables*, diccionarios de hashes precomputados), forzando a cualquier atacante a calcular hashes uno por uno a un costo computacional prohibitivo.

---

### 2. Ventajas de usar SQLite en este proyecto

SQLite es el motor de base de datos relacional más utilizado en el mundo del software y su elección para este trabajo práctico presenta ventajas directas:

1. **Cero Configuración y Arquitectura sin Servidor (Serverless):**
   No requiere instalar, configurar ni mantener un servicio o proceso demonio independiente (a diferencia de MySQL, PostgreSQL o MariaDB). No consume puertos de red adicionales ni requiere gestión de usuarios/privilegios a nivel de servicio de base de datos.
2. **Persistencia en un Archivo Único y Máxima Portabilidad:**
   Toda la base de datos (esquema, tablas de usuarios y tareas, índices y registros) reside en un único archivo físico (`gestor_tareas.db`). Esto permite mover, clonar o compartir el proyecto entero entre diferentes entornos y sistemas operativos (Linux, Windows, macOS) simplemente copiando el repositorio.
3. **Integración Nativa en Python:**
   Python incluye de forma estándar la biblioteca `sqlite3` en su biblioteca base. No se requiere instalar librerías externas ni binarios compilados de terceros para la persistencia de datos.
4. **Cumplimiento de Estándares ACID:**
   A pesar de su ligereza, SQLite es completamente **ACID** (*Atomicidad, Consistencia, Aislamiento y Durabilidad*). Esto asegura que las transacciones (como la creación de usuarios o inserción de tareas) mantengan la consistencia de los datos ante cierres inesperados del servidor o interrupciones de energía.
5. **Rendimiento Excepcional en Entornos Ligeros y Educativos:**
   Para aplicaciones de escala pequeña a mediana, proyectos de desarrollo y prototipado rápido, SQLite ejecuta operaciones de lectura y escritura en disco con un tiempo de respuesta extremadamente bajo y un consumo mínimo de memoria RAM.

---

## 🌐 Alojamiento en GitHub Pages

El proyecto incluye una página estática interactiva (`index.html` y `docs/index.html`) lista para ser alojada en **GitHub Pages**.

### Pasos para publicar en GitHub Pages:
1. Inicializar el repositorio Git local y hacer el commit inicial:
   ```bash
   git init
   git add .
   git commit -m "Entrega PFO 2: Sistema de Gestión de Tareas con API y Base de Datos"
   ```
2. Crear un repositorio en tu cuenta de GitHub (ej: `tp2-gestion-tareas`).
3. Vincular y subir:
   ```bash
   git remote add origin https://github.com/<TU_USUARIO>/<TU_REPOSITORIO>.git
   git branch -M main
   git push -u origin main
   ```
4. En GitHub:
   - Ir a la pestaña **Settings** (Configuración) de tu repositorio.
   - En la barra lateral izquierda, hacer clic en **Pages**.
   - En la sección **Build and deployment**:
     - Source: **Deploy from a branch**
     - Branch: seleccionar `main` y la carpeta `/ (root)` o `/docs`.
     - Hacer clic en **Save**.
5. En unos instantes, la página del proyecto estará disponible en la URL provista por GitHub:
   `https://<TU_USUARIO>.github.io/<TU_REPOSITORIO>/`
