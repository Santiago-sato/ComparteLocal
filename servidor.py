from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
import os
from werkzeug.utils import secure_filename
import socket
import qrcode
import io
from datetime import datetime
import math

UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 5000 * 1024 * 1024  # 5000 MB
ITEMS_PER_PAGE = 24

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_unique_filename(filename):
    """Si el archivo ya existe, agrega _1, _2, etc."""
    base, ext = os.path.splitext(filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    counter = 1
    while os.path.exists(file_path):
        filename = f"{base}_{counter}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        counter += 1
    return filename


def detectar_tipo(filename):
    ext = filename.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
        return 'imagen'
    elif ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
        return 'video'
    elif ext in ['mp3', 'wav', 'ogg', 'm4a', 'aac']:
        return 'audio'
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
        return 'archivo'
    elif ext in ['pdf']:
        return 'pdf'
    elif ext in ['iso']:
        return 'disco'
    else:
        return 'otro'


def get_archivos_ordenados():
    """Obtiene archivos ordenados por fecha de modificacion (más reciente primero)."""
    archivos = []
    if not os.path.exists(UPLOAD_FOLDER):
        return archivos

    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            size_mb = round(size / (1024 * 1024), 2)
            mtime = os.path.getmtime(file_path)
            fecha = datetime.fromtimestamp(mtime)

            archivos.append({
                "nombre": filename,
                "tamaño": size_mb,
                "tipo": detectar_tipo(filename),
                "fecha": fecha.strftime("%d/%m/%Y %H:%M"),
                "fecha_timestamp": int(mtime),
            })

    archivos.sort(key=lambda x: x["fecha_timestamp"], reverse=True)
    return archivos


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/qr")
def qr_code():
    local_ip = get_local_ip()
    port = request.host.split(':')[1] if ':' in request.host else '5000'
    url = f"http://{local_ip}:{port}"
    return render_template("qr.html", url=url)


@app.route("/qr-image")
def qr_image():
    local_ip = get_local_ip()
    port = request.host.split(':')[1] if ':' in request.host else '5000'
    url = f"http://{local_ip}:{port}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


@app.route("/galeria")
def galeria():
    page = request.args.get("page", 1, type=int)
    busqueda = request.args.get("q", "", type=str).strip().lower()
    filtro_tipo = request.args.get("tipo", "", type=str).strip().lower()

    archivos = get_archivos_ordenados()

    if busqueda:
        archivos = [a for a in archivos if busqueda in a["nombre"].lower()]

    if filtro_tipo:
        archivos = [a for a in archivos if a["tipo"] == filtro_tipo]

    total = len(archivos)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    archivos_pagina = archivos[start:end]

    tipos_disponibles = sorted(set(a["tipo"] for a in get_archivos_ordenados()))

    return render_template(
        "galeria.html",
        archivos=archivos_pagina,
        total=total,
        page=page,
        total_pages=total_pages,
        busqueda=busqueda,
        filtro_tipo=filtro_tipo,
        tipos_disponibles=tipos_disponibles,
    )


@app.route("/uploads/<filename>")
def ver_archivo(filename):
    from flask import make_response

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        return "Archivo no encontrado", 404

    ext = filename.lower().split('.')[-1]
    mime_types = {
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'm4a': 'audio/mp4',
        'aac': 'audio/aac',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'pdf': 'application/pdf',
    }

    mimetype = mime_types.get(ext, 'application/octet-stream')

    response = make_response(send_from_directory(app.config["UPLOAD_FOLDER"], filename))
    response.headers['Content-Type'] = mimetype
    response.headers['Accept-Ranges'] = 'bytes'

    return response


@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"message": "Archivo eliminado correctamente"})
        else:
            return jsonify({"error": "Archivo no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        files = [request.files["file"]]
    else:
        files = request.files.getlist("files")

    subidos = []
    errores = []

    for file in files:
        if file.filename == "":
            continue

        filename = secure_filename(file.filename)
        if not filename:
            errores.append("Nombre de archivo inválido")
            continue

        filename = get_unique_filename(filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        try:
            file.save(file_path)
            subidos.append(filename)
        except Exception as e:
            errores.append(f"{filename}: {str(e)}")

    if not subidos and errores:
        return jsonify({"error": "No se pudieron subir los archivos", "detalles": errores}), 500

    return jsonify({
        "message": f"{len(subidos)} archivo(s) subido(s) correctamente",
        "archivos": subidos,
        "errores": errores,
    })


if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 5000
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    url = f"http://{local_ip}:{port}"

    print("\n" + "="*50)
    print("  SERVIDOR INICIADO")
    print("="*50)
    print(f"  Subir archivos:  {url}")
    print(f"  Ver QR:          {url}/qr")
    print(f"  Ver galeria:     {url}/galeria")
    print(f"  Debug:           {'ACTIVADO' if debug else 'DESACTIVADO'}")
    print(f"  Max upload:      5000 MB")
    print("="*50 + "\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
