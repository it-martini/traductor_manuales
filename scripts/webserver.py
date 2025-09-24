#!/usr/bin/env python3
"""
Webserver simple para servir los manuales traducidos desde /output
"""

import os
import sys
import json
import signal
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote, unquote

# Agregar el directorio actual al path para imports
sys.path.append(str(Path(__file__).parent))

from system_config import BASE_DIR, OUTPUT_DIR
from languages_config import LANGUAGES, MANUALS, get_language_display_name

class OutputDirectoryHandler(SimpleHTTPRequestHandler):
    """Handler personalizado para servir los archivos de output"""

    def __init__(self, *args, **kwargs):
        # Cambiar al directorio de output
        os.chdir(OUTPUT_DIR)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Maneja las peticiones GET con index personalizado"""
        if self.path == '/' or self.path == '/index.html':
            self.send_custom_index()
        else:
            super().do_GET()

    def send_custom_index(self):
        """Envía una página de índice personalizada"""
        html_content = self.generate_index_page()

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def generate_index_page(self):
        """Genera la página de índice con todos los manuales disponibles"""
        html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manuales Traducidos - Campus Virtual</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            color: #666;
            font-size: 1.2em;
            margin: 10px 0 0 0;
        }
        .manual-section {
            margin-bottom: 40px;
        }
        .manual-title {
            font-size: 1.8em;
            color: #4a5568;
            margin-bottom: 20px;
            padding: 15px;
            background: linear-gradient(45deg, #f7fafc, #edf2f7);
            border-radius: 10px;
            border-left: 5px solid #4299e1;
        }
        .languages-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .language-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
        }
        .language-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-color: #4299e1;
        }
        .language-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 10px;
        }
        .file-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .file-link {
            display: inline-block;
            padding: 8px 15px;
            background: #4299e1;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .file-link:hover {
            background: #3182ce;
            transform: scale(1.05);
        }
        .file-link.html {
            background: #38a169;
        }
        .file-link.html:hover {
            background: #2f855a;
        }
        .file-link.docx {
            background: #d69e2e;
        }
        .file-link.docx:hover {
            background: #b7791f;
        }
        .file-link.pdf {
            background: #e53e3e;
        }
        .file-link.pdf:hover {
            background: #c53030;
        }
        .no-files {
            color: #a0aec0;
            font-style: italic;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            color: #666;
        }
        .server-info {
            background: #e6fffa;
            border: 1px solid #81e6d9;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .server-info h3 {
            margin: 0 0 10px 0;
            color: #234e52;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Manuales Traducidos</h1>
            <p>Campus Virtual - Sistema de Traducción</p>
        </div>

        <div class="server-info">
            <h3>🌐 Servidor Web Local Activo</h3>
            <p>Navegando archivos desde: <code>{output_dir}</code></p>
        </div>
"""

        # Escanear manuales disponibles
        for manual_key, manual_info in MANUALS.items():
            html += f"""
        <div class="manual-section">
            <div class="manual-title">
                {manual_info['emoji']} {manual_info['name']}
            </div>
            <div class="languages-grid">
"""

            # Incluir español como referencia
            spanish_files = self.get_manual_files('es', manual_key)
            if spanish_files:
                html += f"""
                <div class="language-card">
                    <div class="language-name">🇪🇸 Español (Original)</div>
                    <div class="file-links">
"""
                for file_type, file_path in spanish_files.items():
                    if file_path:
                        html += f'<a href="{file_path}" class="file-link {file_type}" target="_blank">{file_type.upper()}</a>'

                html += """
                    </div>
                </div>
"""

            # Otros idiomas
            for lang_code in LANGUAGES.keys():
                if lang_code == 'es':
                    continue

                files = self.get_manual_files(lang_code, manual_key)
                if files and any(files.values()):
                    lang_name = get_language_display_name(lang_code)

                    html += f"""
                <div class="language-card">
                    <div class="language-name">{lang_name}</div>
                    <div class="file-links">
"""

                    for file_type, file_path in files.items():
                        if file_path:
                            html += f'<a href="{file_path}" class="file-link {file_type}" target="_blank">{file_type.upper()}</a>'

                    if not any(files.values()):
                        html += '<span class="no-files">Sin archivos disponibles</span>'

                    html += """
                    </div>
                </div>
"""

            html += """
            </div>
        </div>
"""

        html += f"""
        <div class="footer">
            <p>🚀 Generado automáticamente por el sistema de traducción</p>
            <p>Total de idiomas soportados: {len(LANGUAGES)} | Manuales: {len(MANUALS)}</p>
        </div>
    </div>
</body>
</html>"""

        return html.format(output_dir=str(OUTPUT_DIR))

    def get_manual_files(self, lang_code, manual_key):
        """Obtiene los archivos disponibles para un manual/idioma"""
        files = {'html': None, 'docx': None, 'pdf': None}

        if lang_code == 'es':
            # Para español, buscar en el directorio original
            base_path = OUTPUT_DIR.parent / 'original' / f"{manual_key}_es"
            if base_path.exists():
                # Buscar HTML (cualquier archivo .html)
                html_files = list(base_path.glob('*.html'))
                if html_files:
                    # Usar el path relativo desde OUTPUT_DIR
                    rel_path = os.path.relpath(html_files[0], OUTPUT_DIR)
                    files['html'] = quote(rel_path.replace('\\', '/'))
        else:
            # Para otros idiomas, buscar en output
            lang_info = LANGUAGES.get(lang_code, {})
            output_dir = lang_info.get('output_dir', lang_code)
            manual_dir = OUTPUT_DIR / output_dir / f"{manual_key}_{lang_code}"

            if manual_dir.exists():
                # HTML
                html_dir = manual_dir / 'html'
                if html_dir.exists():
                    html_files = list(html_dir.glob('*.html'))
                    if html_files:
                        # Usar index.html si existe, sino el primero
                        index_file = html_dir / 'index.html'
                        target_file = index_file if index_file.exists() else html_files[0]
                        rel_path = os.path.relpath(target_file, OUTPUT_DIR)
                        files['html'] = quote(rel_path.replace('\\', '/'))

                # DOCX
                docx_dir = manual_dir / 'docx'
                if docx_dir.exists():
                    docx_files = list(docx_dir.glob('*.docx'))
                    if docx_files:
                        rel_path = os.path.relpath(docx_files[0], OUTPUT_DIR)
                        files['docx'] = quote(rel_path.replace('\\', '/'))

                # PDF
                pdf_dir = manual_dir / 'pdf'
                if pdf_dir.exists():
                    pdf_files = list(pdf_dir.glob('*.pdf'))
                    if pdf_files:
                        rel_path = os.path.relpath(pdf_files[0], OUTPUT_DIR)
                        files['pdf'] = quote(rel_path.replace('\\', '/'))

        return files

class WebServer:
    """Clase para manejar el webserver"""

    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.httpd = None
        self.server_thread = None
        self.running = False
        self.pid_file = BASE_DIR / 'webserver.pid'

    def start(self):
        """Inicia el servidor web"""
        if self.is_running():
            print(f"⚠️ El servidor ya está ejecutándose en http://{self.host}:{self.port}")
            return False

        try:
            # Verificar que OUTPUT_DIR existe
            if not OUTPUT_DIR.exists():
                print(f"❌ El directorio de salida no existe: {OUTPUT_DIR}")
                return False

            # Crear servidor HTTP
            self.httpd = HTTPServer((self.host, self.port), OutputDirectoryHandler)

            # Ejecutar en hilo separado
            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()

            self.running = True

            # Guardar PID
            self.save_pid()

            print(f"✅ Servidor web iniciado en http://{self.host}:{self.port}")
            print(f"📁 Sirviendo archivos desde: {OUTPUT_DIR}")
            print("🌐 Abre tu navegador para explorar los manuales traducidos")

            return True

        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"❌ Puerto {self.port} ya está en uso")
                print("💡 Prueba con otro puerto o detén el proceso que lo está usando")
            else:
                print(f"❌ Error iniciando servidor: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

    def stop(self):
        """Detiene el servidor web"""
        if not self.running or not self.httpd:
            print("ℹ️ El servidor no está ejecutándose")
            return False

        try:
            self.httpd.shutdown()
            self.httpd.server_close()

            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2)

            self.running = False
            self.httpd = None
            self.server_thread = None

            # Eliminar archivo PID
            self.remove_pid()

            print("✅ Servidor web detenido")
            return True

        except Exception as e:
            print(f"❌ Error deteniendo servidor: {e}")
            return False

    def is_running(self):
        """Verifica si el servidor está ejecutándose"""
        return self.running and self.httpd is not None

    def get_status(self):
        """Obtiene el estado actual del servidor"""
        if self.is_running():
            return {
                'running': True,
                'url': f"http://{self.host}:{self.port}",
                'host': self.host,
                'port': self.port,
                'directory': str(OUTPUT_DIR)
            }
        else:
            return {
                'running': False,
                'url': None,
                'host': self.host,
                'port': self.port,
                'directory': str(OUTPUT_DIR)
            }

    def save_pid(self):
        """Guarda el PID del servidor"""
        try:
            pid_data = {
                'pid': os.getpid(),
                'host': self.host,
                'port': self.port,
                'start_time': time.time()
            }
            with open(self.pid_file, 'w') as f:
                json.dump(pid_data, f)
        except Exception:
            pass  # No es crítico si falla

    def remove_pid(self):
        """Elimina el archivo PID"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass  # No es crítico si falla

# Instancia global del servidor
_server_instance = None

def get_server_instance():
    """Obtiene la instancia global del servidor"""
    global _server_instance
    if _server_instance is None:
        _server_instance = WebServer()
    return _server_instance

def start_webserver(host='localhost', port=8080):
    """Función para iniciar el webserver"""
    server = get_server_instance()
    server.host = host
    server.port = port
    return server.start()

def stop_webserver():
    """Función para detener el webserver"""
    server = get_server_instance()
    return server.stop()

def is_webserver_running():
    """Verifica si el webserver está ejecutándose"""
    server = get_server_instance()
    return server.is_running()

def get_webserver_status():
    """Obtiene el estado del webserver"""
    server = get_server_instance()
    return server.get_status()

if __name__ == "__main__":
    """Ejecutar como script independiente"""
    import argparse

    parser = argparse.ArgumentParser(description='Servidor web para manuales traducidos')
    parser.add_argument('--host', default='localhost', help='Host del servidor (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Puerto del servidor (default: 8080)')
    parser.add_argument('--stop', action='store_true', help='Detener el servidor')

    args = parser.parse_args()

    if args.stop:
        if stop_webserver():
            print("Servidor detenido exitosamente")
        else:
            print("No se pudo detener el servidor")
        sys.exit(0)

    # Iniciar servidor
    if start_webserver(args.host, args.port):
        print(f"\nServidor web activo en http://{args.host}:{args.port}")
        print("Presiona Ctrl+C para detener...")

        # Manejar señal de interrupción
        def signal_handler(signum, frame):
            print("\n\nDeteniendo servidor...")
            stop_webserver()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Mantener el proceso principal activo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
    else:
        print("No se pudo iniciar el servidor")
        sys.exit(1)