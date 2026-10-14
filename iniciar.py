"""
iniciar.py
----------
Lanzador unificado:
1. Inicia automáticamente el servidor Flask en segundo plano.
2. Espera a que esté activo y listo para recibir peticiones.
3. Abre el navegador web en http://127.0.0.1:5000/tareas.
4. Lanza el cliente interactivo en la consola.
5. Al salir del cliente (o con Ctrl+C), apaga el servidor limpiamente.
"""

import sys
import time
import subprocess
import webbrowser
import requests

API_URL = "http://127.0.0.1:5000"


def main():
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA DE GESTIÓN DE TAREAS (PFO 2)")
    print("=" * 60)
    print("[1/3] Iniciando Servidor Flask en segundo plano...")

    # Usamos sys.executable para garantizar que use el mismo Python (.venv)
    servidor_proc = subprocess.Popen(
        [sys.executable, "servidor.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Esperamos a que el servidor esté listo
    print("[2/3] Esperando que la API esté lista...")
    servidor_listo = False
    for _ in range(20):  # hasta 10 segundos
        try:
            r = requests.get(f"{API_URL}/tareas", timeout=1)
            if r.status_code == 200:
                servidor_listo = True
                break
        except Exception:
            time.sleep(0.5)

    if not servidor_listo:
        print("❌ Error: No se pudo iniciar el servidor. Revisa si el puerto 5000 está ocupado.")
        servidor_proc.terminate()
        sys.exit(1)

    print("✅ Servidor activo en http://127.0.0.1:5000")

    # Abrimos la página web en el navegador
    print("[3/3] Abriendo página web en tu navegador...")
    try:
        webbrowser.open(f"{API_URL}/tareas")
    except Exception:
        pass

    print("\n💻 Iniciando cliente interactivo en consola...")
    time.sleep(1)

    try:
        # Ejecutamos cliente.py en el mismo hilo interactivo
        subprocess.run([sys.executable, "cliente.py"])
    except KeyboardInterrupt:
        print("\nInterrupción detectada...")
    finally:
        print("\n" + "=" * 60)
        print("🛑 Deteniendo el servidor Flask...")
        servidor_proc.terminate()
        servidor_proc.wait()
        print("✅ Servidor detenido correctamente. ¡Hasta luego!")
        print("=" * 60)


if __name__ == "__main__":
    main()

