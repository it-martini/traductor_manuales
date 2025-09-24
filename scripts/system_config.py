"""
Configuración del sistema de traducción de manuales
"""

import os
from pathlib import Path
from datetime import datetime

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Directorios principales
ORIGINAL_DIR = BASE_DIR / "original"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"
LOGS_DIR = BASE_DIR / "logs"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Archivos de configuración
CACHE_FILE = CACHE_DIR / "translations.json"
CONFIG_FILE = BASE_DIR / "config" / ".env"

# Configuración de traducción
TRANSLATION_CONFIG = {
    'max_retries': 3,
    'timeout_seconds': 60,
    'batch_size': 10,
    'cache_enabled': True,
    'cost_warning_threshold': 5.0,  # USD
    'auto_confirm_under': 1.0       # USD
}

# Configuración de conversión DOCX
DOCX_CONFIG = {
    'title_page_title': {
        'es': 'Campus Virtual\nManual de Usuario',
        'en': 'Virtual Campus\nUser Manual',
        'default': 'Campus Virtual\nUser Manual'
    },
    'footer_copyright': 'e-ducativa Educación Virtual S.A.',
    'footer_year': datetime.now().year,
    'default_font': 'Calibri',
    'styles': {
        'heading1': {'size': 18, 'bold': True, 'color': '000000'},
        'heading2': {'size': 14, 'bold': True, 'color': '000000'},
        'normal': {'size': 11, 'bold': False, 'color': '000000'},
        'hyperlink': {'size': 11, 'bold': False, 'color': '0000FF', 'underline': True}
    }
}

# Patrones de archivos
FILE_PATTERNS = {
    'html': '*.html',
    'css': '*.css',
    'js': '*.js',
    'images': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg'],
    'exclude': ['home.html']  # Archivos a omitir en traducción
}

def ensure_directories():
    """Asegura que existan todos los directorios necesarios"""
    dirs = [ORIGINAL_DIR, OUTPUT_DIR, CACHE_DIR, LOGS_DIR, SCRIPTS_DIR]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_manual_path(manual_name, lang_code=None, format_type=None):
    """
    Construye rutas para manuales con nueva estructura

    Args:
        manual_name: Nombre del manual (ej: 'open_aula_front', 'open_aula_back')
        lang_code: Código de idioma (ej: 'en', 'pt')
        format_type: Tipo de formato ('html', 'docx')

    Returns:
        Path object
    """
    # Importar aquí para evitar dependencias circulares
    from languages_config import LANGUAGES, get_output_path

    if lang_code is None or lang_code == 'es':
        # Ruta original (español)
        return ORIGINAL_DIR / f"{manual_name}_es"

    # Usar la nueva función de languages_config
    relative_path = get_output_path(lang_code, manual_name, format_type)
    if relative_path is None:
        return None

    return BASE_DIR / relative_path

def get_log_file(operation_type, timestamp=None):
    """Genera ruta para archivo de log"""
    if timestamp is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return LOGS_DIR / f"{operation_type}_{timestamp}.log"

def load_api_key():
    """Carga la API key de Claude desde archivo .env"""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('CLAUDE_API_KEY='):
                    return line.split('=', 1)[1].strip()

    # Fallback a variable de entorno
    return os.getenv('CLAUDE_API_KEY')

def estimate_translation_cost(num_elements, avg_length=50):
    """
    Estima el costo de traducción basado en número de elementos

    Args:
        num_elements: Número de elementos a traducir
        avg_length: Longitud promedio de texto por elemento

    Returns:
        float: Costo estimado en USD
    """
    # Estimación basada en precios de Claude API
    # ~$0.50 por cada 1000 elementos de tamaño medio
    tokens_per_element = avg_length * 1.3  # Factor de tokens
    total_tokens = num_elements * tokens_per_element
    cost_per_1k_tokens = 0.015  # USD (input tokens)

    return (total_tokens / 1000) * cost_per_1k_tokens