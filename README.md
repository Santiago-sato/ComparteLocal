# ComparteLocal

Servidor web Flask para compartir archivos en red local. Permite subir, visualizar y descargar archivos desde cualquier dispositivo conectado a la misma red mediante un código QR.

## Características

- Subida de archivos (hasta 5000 MB)
- Soporte para múltiples archivos simultáneamente
- Galería con paginación, búsqueda y filtros por tipo
- Visualización directa de imágenes, videos, audio y PDF
- Generación de código QR para acceso rápido desde el móvil
- Interfaces limpias y responsivas

## Requisitos

- Python 3.8 o superior

## Instalación y uso

```bash
# Clonar o copiar los archivos
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
python servidor.py
```

Luego abre la URL que aparece en la terminal o escanea el código QR en `/qr`.

## Estructura

```
ComparteLocal/
├── servidor.py          # Aplicación principal
├── requirements.txt     # Dependencias
├── templates/           # Plantillas HTML
│   ├── index.html       # Página de inicio (subida)
│   ├── galeria.html     # Galería de archivos
│   └── qr.html          # Página del código QR
├── uploads/             # Archivos subidos (ignorado por git)
└── .gitignore
```

## Licencia

MIT
