
import os
import subprocess
import uuid

# Configuración inicial
REPO_LOCAL_PATH = "/Users/carolinahuergo/Documents/youser/queueprobot/passline"  # Cambiar por tu ruta local
GITHUB_USER = "federicocastro"
GITHUB_REPO = "passline"
BRANCH = "main"

git_hub_api_key = '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'


def subir_imagen_y_obtener_url(ruta_imagen_local):
    # Asegurarse de que existe la ruta
    if not os.path.isfile(ruta_imagen_local):
        raise FileNotFoundError(f"No existe la imagen: {ruta_imagen_local}")

    # Generar un nombre único para evitar conflictos
    _, ext = os.path.splitext(ruta_imagen_local)
    nombre_unico = f"{uuid.uuid4().hex}{ext}"

    # Ruta donde quedará la imagen en el repo
    ruta_imagen_repo = os.path.join(REPO_LOCAL_PATH, nombre_unico)

    # Copiar la imagen al repo
    subprocess.run(["cp", ruta_imagen_local, ruta_imagen_repo], check=True)

    # Cambiar directorio al repo
    cwd = os.getcwd()
    os.chdir(REPO_LOCAL_PATH)

    try:
        # Git add, commit y push
        subprocess.run(["git", "add", nombre_unico], check=True)
        subprocess.run(["git", "commit", "-m", f"Añadir imagen {nombre_unico}"], check=True)
        subprocess.run(["git", "push", "origin", BRANCH], check=True)
    finally:
        # Volver al directorio original
        os.chdir(cwd)

    # Construir la URL directa a la imagen (raw)
    url_imagen = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{nombre_unico}"

    return url_imagen

# Ejemplo de uso
if __name__ == "__main__":
    imagen_local = "/Users/fedex/projects/pythonProject/images/sample.png"  # Cambia por tu imagen local
    url = subir_imagen_y_obtener_url(imagen_local)
    print(f"Imagen subida. URL directa:\n{url}")
