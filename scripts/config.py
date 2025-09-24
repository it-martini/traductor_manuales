"""
Configuración unificada para el traductor inteligente
Soporta HTML y DOCX con configuración centralizada
"""

import os
from pathlib import Path

# API Configuration
ANTHROPIC_API_KEY = "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"
MODEL = "claude-3-haiku-20240307"

# Rate limiting
RATE_LIMIT_DELAY = 0.5
MAX_RETRIES = 3

# Base directories
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

# Format configurations
FORMATS = {
    'html': {
        'name': 'HTML Manual',
        'source_dir': PROJECT_ROOT / 'html_v10',
        'target_dir': PROJECT_ROOT / 'outputs' / 'html_en',
        'cache_file': BASE_DIR / 'caches' / 'html_cache.json',
        'enabled': True,
        'file_pattern': '*.html',
        'description': '97 HTML files + navigation'
    },
    'docx': {
        'name': 'DOCX Manual',
        'source_dir': PROJECT_ROOT / 'docx_v10',
        'target_dir': PROJECT_ROOT / 'outputs' / 'docx_en',
        'cache_file': BASE_DIR / 'caches' / 'docx_cache.json',
        'enabled': True,
        'file_pattern': '*.docx',
        'description': '1 DOCX file with complete manual'
    }
}

# Shared terminology mapping for consistency
TERMINOLOGY_MAPPING = {
    "Aulas": "Classrooms",
    "Evaluaciones": "Assessments",
    "Portafolio": "Portfolio",
    "Catálogo": "Catalog",
    "Identificación Segura": "Secure Identification",
    "Redes sociales": "Social Networks",
    "Cursos para docentes": "Teacher Courses",
    "Introducción": "Introduction",
    "Perfiles": "Profiles",
    "Secciones": "Sections",
    "Categorías": "Categories",
    "Programa": "Program",
    "Presentación": "Presentation",
    "Encabezado": "Header",
    "Perfil": "Profile",
    "Preferencias": "Preferences",
    "Estadísticas": "Statistics",
    "Acceso a aulas": "Classroom Access",
    "Notificaciones": "Notifications",
    "Sucesos recientes": "Recent Events",
    "Carpetas": "Folders",
    "Archivos": "Files",
    "Documentos": "Documents",
    "Compartir": "Share",
    "Comentarios": "Comments",
    "Inicio del Aula": "Classroom Home"
}

# Translation prompt template
TRANSLATION_PROMPT = """Traduce el siguiente texto del español al inglés manteniendo:
1. El significado exacto y contexto profesional
2. Terminología técnica consistente para plataformas LMS
3. Tono formal apropiado para documentación educativa
4. NO traduzcas nombres propios, URLs, códigos o etiquetas técnicas

Usa esta terminología específica cuando aparezca:
{terminology}

Texto a traducir: "{text}"

Responde SOLO con la traducción en inglés, sin explicaciones."""

# UI Configuration
MENU_OPTIONS = {
    '1': {
        'label': '📄 HTML Manual',
        'format': 'html',
        'description': 'Translate web-based manual (97 files)'
    },
    '2': {
        'label': '📋 DOCX Manual',
        'format': 'docx',
        'description': 'Translate document file (1 DOCX)'
    },
    '3': {
        'label': '🔄 BOTH Formats',
        'format': 'both',
        'description': 'Translate HTML + DOCX'
    },
    '4': {
        'label': '📊 STATISTICS',
        'format': 'stats',
        'description': 'View translation status and cache info'
    },
    '5': {
        'label': '⚙️  CONFIGURATION',
        'format': 'config',
        'description': 'Adjust settings and preferences'
    },
    '0': {
        'label': '❌ EXIT',
        'format': 'exit',
        'description': 'Exit translator'
    }
}

def get_format_config(format_name: str) -> dict:
    """Get configuration for specific format"""
    return FORMATS.get(format_name, {})

def ensure_directories():
    """Ensure all required directories exist"""
    for format_config in FORMATS.values():
        format_config['target_dir'].mkdir(parents=True, exist_ok=True)

    # Ensure cache directory exists
    (BASE_DIR / 'caches').mkdir(exist_ok=True)