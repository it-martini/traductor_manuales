#!/usr/bin/env python3
"""
Webserver con tabla HTML que funciona correctamente
"""

import os
import sys
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
import mimetypes

# Agregar el directorio actual al path para imports
sys.path.append(str(Path(__file__).parent))

from system_config import OUTPUT_DIR
from languages_config import LANGUAGES, MANUALS, get_language_display_name

class FixedTableHandler(BaseHTTPRequestHandler):
    """Handler que maneja correctamente tanto la tabla como los archivos"""

    def do_GET(self):
        """Maneja peticiones GET"""
        try:
            # Cambiar al directorio output
            original_dir = os.getcwd()
            os.chdir(OUTPUT_DIR)

            path = unquote(self.path)

            # Si es la raíz, mostrar tabla
            if path == '/' or path == '/index.html':
                self.send_table_page()
            else:
                # Servir archivo normal
                self.serve_file(path)

        except Exception as e:
            print(f"Error en do_GET: {e}")
            self.send_error(500, f"Error interno: {e}")
        finally:
            try:
                os.chdir(original_dir)
            except:
                pass

    def send_table_page(self):
        """Envía la página con tabla"""
        html = self.generate_table_html()

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()

        self.wfile.write(html.encode('utf-8'))

    def serve_file(self, path):
        """Sirve un archivo del sistema"""
        try:
            # Remover / inicial
            if path.startswith('/'):
                path = path[1:]

            file_path = Path(OUTPUT_DIR) / path

            if file_path.is_file():
                # Determinar tipo MIME
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    mime_type = 'application/octet-stream'

                # Enviar archivo
                with open(file_path, 'rb') as f:
                    content = f.read()

                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()

                self.wfile.write(content)

            elif file_path.is_dir():
                # Mostrar listado de directorio
                self.send_directory_listing(file_path, path)
            else:
                self.send_error(404, 'Archivo no encontrado')

        except Exception as e:
            print(f"Error sirviendo archivo {path}: {e}")
            self.send_error(500, f"Error: {e}")

    def send_directory_listing(self, dir_path, url_path):
        """Envía listado de directorio"""
        try:
            entries = []
            if url_path:  # No mostrar "subir" para la raíz
                entries.append('<li><a href="../">📁 ..</a></li>')

            for item in sorted(dir_path.iterdir()):
                name = item.name
                if item.is_dir():
                    entries.append(f'<li><a href="{url_path}/{name}/">📁 {name}/</a></li>')
                else:
                    entries.append(f'<li><a href="{url_path}/{name}">📄 {name}</a></li>')

            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directorio: /{url_path}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 5px 0; }}
        a {{ text-decoration: none; color: #007bff; padding: 5px; }}
        a:hover {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>📁 Directorio: /{url_path}</h1>
    <ul>
        {''.join(entries)}
    </ul>
    <hr>
    <p><a href="/">🏠 Volver a la tabla principal</a></p>
</body>
</html>"""

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html.encode('utf-8'))))
            self.end_headers()

            self.wfile.write(html.encode('utf-8'))

        except Exception as e:
            print(f"Error listando directorio: {e}")
            self.send_error(500, f"Error: {e}")

    def generate_table_html(self):
        """Genera la tabla HTML"""

        # Escanear archivos disponibles
        data = self.scan_available_files()

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 Manuales Traducidos - Campus Virtual</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}

        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .info-bar {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 25px;
            text-align: center;
            color: #666;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}

        th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 12px;
            text-align: center;
            font-weight: 600;
        }}

        th.language-header {{
            background: linear-gradient(135deg, #4a90e2, #357abd);
            text-align: left;
            min-width: 200px;
        }}

        td {{
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}

        td.language-name {{
            font-weight: 600;
            color: #333;
            text-align: left;
            background: #f8f9fa;
            border-right: 2px solid #dee2e6;
        }}

        .file-links {{
            display: flex;
            gap: 6px;
            justify-content: center;
            flex-wrap: wrap;
        }}

        .file-link {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            text-decoration: none;
            font-size: 0.85em;
            font-weight: 500;
            transition: all 0.2s ease;
            min-width: 45px;
        }}

        .file-link.html {{
            background: #28a745;
            color: white;
        }}
        .file-link.html:hover {{
            background: #218838;
            transform: scale(1.05);
        }}

        .file-link.docx {{
            background: #ffc107;
            color: #212529;
        }}
        .file-link.docx:hover {{
            background: #e0a800;
            transform: scale(1.05);
        }}

        .file-link.pdf {{
            background: #dc3545;
            color: white;
        }}
        .file-link.pdf:hover {{
            background: #c82333;
            transform: scale(1.05);
        }}

        .no-files {{
            color: #6c757d;
            font-style: italic;
        }}

        tr:hover td:not(.language-name) {{
            background: #f0f8ff;
        }}

        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Manuales Traducidos</h1>
            <p>Campus Virtual - Sistema de Traducción</p>
        </div>

        <div class="info-bar">
            <strong>📁 Directorio:</strong> {OUTPUT_DIR} |
            <strong>🌍 Idiomas:</strong> {len(LANGUAGES)} |
            <strong>📖 Manuales:</strong> {len(MANUALS)}
        </div>

        <table>
            <thead>
                <tr>
                    <th class="language-header">Idioma</th>"""

        # Headers para cada manual
        manual_emojis = {
            'open_aula_front': '👤',
            'open_aula_back': '⚙️'
        }
        for manual_key, manual_info in MANUALS.items():
            emoji = manual_emojis.get(manual_key, '📖')
            html += f'<th>{emoji} {manual_info["name"]}</th>'

        html += """
                </tr>
            </thead>
            <tbody>"""

        # Generar filas
        for lang_code in LANGUAGES.keys():
            lang_name = get_language_display_name(lang_code)
            html += f"""
                <tr>
                    <td class="language-name">{lang_name}</td>"""

            # Para cada manual
            for manual_key in MANUALS.keys():
                files = data.get(lang_code, {}).get(manual_key, {})
                html += '<td>'

                if files and any(files.values()):
                    html += '<div class="file-links">'
                    for file_type, file_path in files.items():
                        if file_path:
                            html += f'<a href="{file_path}" class="file-link {file_type}" target="_blank">{file_type.upper()}</a>'
                    html += '</div>'
                else:
                    html += '<span class="no-files">-</span>'

                html += '</td>'

            html += '</tr>'

        html += """
            </tbody>
        </table>

        <div class="footer">
            <p>🌐 Servidor local activo • Haz clic en los enlaces para abrir archivos</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def scan_available_files(self):
        """Escanea archivos disponibles de forma rápida"""
        data = {}

        try:
            for lang_code in LANGUAGES.keys():
                data[lang_code] = {}

                for manual_key in MANUALS.keys():
                    files = {'html': None, 'docx': None, 'pdf': None}

                    try:
                        if lang_code == 'es':
                            # Español - buscar en original
                            base_path = OUTPUT_DIR.parent / 'original' / f"{manual_key}_es"
                            if base_path.exists():
                                html_files = list(base_path.glob('*.html'))
                                if html_files:
                                    rel_path = os.path.relpath(html_files[0], OUTPUT_DIR)
                                    files['html'] = rel_path.replace('\\', '/')
                        else:
                            # Otros idiomas
                            lang_info = LANGUAGES.get(lang_code, {})
                            output_dir = lang_info.get('output_dir', lang_code)
                            manual_dir = OUTPUT_DIR / output_dir / f"{manual_key}_{lang_code}"

                            if manual_dir.exists():
                                # HTML
                                html_dir = manual_dir / 'html'
                                if html_dir.exists():
                                    html_files = list(html_dir.glob('*.html'))
                                    if html_files:
                                        # Preferir index.html si existe
                                        index_file = html_dir / 'index.html'
                                        target = index_file if index_file.exists() else html_files[0]
                                        rel_path = os.path.relpath(target, OUTPUT_DIR)
                                        files['html'] = rel_path.replace('\\', '/')

                                # DOCX
                                docx_dir = manual_dir / 'docx'
                                if docx_dir.exists():
                                    docx_files = list(docx_dir.glob('*.docx'))
                                    if docx_files:
                                        rel_path = os.path.relpath(docx_files[0], OUTPUT_DIR)
                                        files['docx'] = rel_path.replace('\\', '/')

                                # PDF
                                pdf_dir = manual_dir / 'pdf'
                                if pdf_dir.exists():
                                    pdf_files = list(pdf_dir.glob('*.pdf'))
                                    if pdf_files:
                                        rel_path = os.path.relpath(pdf_files[0], OUTPUT_DIR)
                                        files['pdf'] = rel_path.replace('\\', '/')

                    except Exception as e:
                        print(f"Error escaneando {lang_code}/{manual_key}: {e}")

                    data[lang_code][manual_key] = files

        except Exception as e:
            print(f"Error general escaneando archivos: {e}")

        return data

    def log_message(self, format, *args):
        """Sobrescribir para evitar logs innecesarios"""
        pass

def start_table_webserver(port=8080):
    """Inicia el servidor web con tabla personalizada"""
    try:
        if not OUTPUT_DIR.exists():
            print(f"❌ El directorio {OUTPUT_DIR} no existe")
            return False

        server = HTTPServer(('localhost', port), FixedTableHandler)

        # Ejecutar en hilo separado
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        url = f"http://localhost:{port}"
        print(f"✅ Servidor tabla iniciado en {url}")
        print(f"📁 Sirviendo desde: {OUTPUT_DIR}")

        return server

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando servidor web con tabla...")
    server = start_table_webserver()

    if server:
        try:
            print("Presiona Ctrl+C para detener...")
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo servidor...")
            server.shutdown()
            server.server_close()
            print("✅ Servidor detenido")