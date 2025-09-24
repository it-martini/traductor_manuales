"""
Configuración de idiomas para el sistema de traducción de manuales
"""

LANGUAGES = {
    'es': {
        'name': 'Español',
        'native_name': 'Español',
        'is_original': True,
        'claude_code': 'Spanish',
        'emoji': '🇪🇸',
        'output_dir': None  # No output dir for original
    },
    'en': {
        'name': 'Inglés',
        'native_name': 'English',
        'is_original': False,
        'claude_code': 'English',
        'emoji': '🇺🇸',
        'output_dir': 'ingles'
    },
    'pt': {
        'name': 'Portugués',
        'native_name': 'Português',
        'is_original': False,
        'claude_code': 'Portuguese',
        'emoji': '🇵🇹',
        'output_dir': 'portugues'
    },
    'fr': {
        'name': 'Francés',
        'native_name': 'Français',
        'is_original': False,
        'claude_code': 'French',
        'emoji': '🇫🇷',
        'output_dir': 'frances'
    },
    'it': {
        'name': 'Italiano',
        'native_name': 'Italiano',
        'is_original': False,
        'claude_code': 'Italian',
        'emoji': '🇮🇹',
        'output_dir': 'italiano'
    },
    'de': {
        'name': 'Alemán',
        'native_name': 'Deutsch',
        'is_original': False,
        'claude_code': 'German',
        'emoji': '🇩🇪',
        'output_dir': 'aleman'
    },
    'nl': {
        'name': 'Neerlandés',
        'native_name': 'Nederlands',
        'is_original': False,
        'claude_code': 'Dutch',
        'emoji': '🇳🇱',
        'output_dir': 'neerlandes'
    },
    'ca': {
        'name': 'Catalán',
        'native_name': 'Català',
        'is_original': False,
        'claude_code': 'Catalan',
        'emoji': '🏴',
        'output_dir': 'catalan'
    },
    'eu': {
        'name': 'Euskera',
        'native_name': 'Euskera',
        'is_original': False,
        'claude_code': 'Basque',
        'emoji': '🏴',
        'output_dir': 'euskera'
    },
    'gl': {
        'name': 'Gallego',
        'native_name': 'Galego',
        'is_original': False,
        'claude_code': 'Galician',
        'emoji': '🏴',
        'output_dir': 'gallego'
    },
    'da': {
        'name': 'Danés',
        'native_name': 'Dansk',
        'is_original': False,
        'claude_code': 'Danish',
        'emoji': '🇩🇰',
        'output_dir': 'danes'
    },
    'sv': {
        'name': 'Sueco',
        'native_name': 'Svenska',
        'is_original': False,
        'claude_code': 'Swedish',
        'emoji': '🇸🇪',
        'output_dir': 'sueco'
    },
    'gn': {
        'name': 'Guaraní',
        'native_name': 'Avañe\'ẽ',
        'is_original': False,
        'claude_code': 'Guarani',
        'emoji': '🇵🇾',
        'output_dir': 'guarani'
    }
}

MANUALS = {
    'open_aula_front': {
        'name': 'Manual de Usuario (Front)',
        'name_en': 'User Manual (Front)',
        'description': 'Manual para usuarios del campus virtual',
        'source_dir': 'original/open_aula_front_es',
        'has_docx_original': True,  # Viene del HelpNDoc
        'priority': 1
    },
    'open_aula_back': {
        'name': 'Manual de Administración (Back)',
        'name_en': 'Administration Manual (Back)',
        'description': 'Manual para administradores del campus virtual',
        'source_dir': 'original/open_aula_back_es',
        'has_docx_original': False,  # Por implementar
        'priority': 2
    }
}

def get_language_display_name(lang_code):
    """Retorna el nombre para mostrar de un idioma"""
    lang = LANGUAGES.get(lang_code)
    if not lang:
        return lang_code
    return f"{lang['emoji']} {lang['name']}"

def get_available_languages():
    """Retorna todos los idiomas disponibles (excluyendo español)"""
    return {k: v for k, v in LANGUAGES.items() if not v['is_original']}

def get_translation_languages():
    """Retorna solo los idiomas que requieren traducción"""
    return [k for k, v in LANGUAGES.items() if not v['is_original']]

def get_output_path(lang_code, manual_type, format_type=None):
    """
    Construye rutas de salida con la nueva estructura

    Args:
        lang_code: Código de idioma (ej: 'en', 'pt')
        manual_type: Tipo de manual ('open_aula_front', 'open_aula_back')
        format_type: Tipo de formato ('html', 'docx')

    Returns:
        str: Ruta relativa desde el directorio base
    """
    if lang_code == 'es':
        return None  # Español está en original/

    lang_info = LANGUAGES.get(lang_code)
    if not lang_info or not lang_info.get('output_dir'):
        return None

    # Construir ruta: output/idioma_legible/open_aula_tipo_codigo/formato
    base_path = f"output/{lang_info['output_dir']}/{manual_type}_{lang_code}"

    if format_type:
        return f"{base_path}/{format_type}"
    else:
        return base_path

def get_language_code_from_output_dir(output_dir):
    """Obtiene el código de idioma desde el nombre del directorio de salida"""
    for code, lang_info in LANGUAGES.items():
        if lang_info.get('output_dir') == output_dir:
            return code
    return None

def format_language_status(lang_code, has_html=False, has_docx=False):
    """Formatea el estado de un idioma para mostrar en consola"""
    lang = LANGUAGES.get(lang_code)
    if not lang:
        return f"{lang_code}: ❓ ❓"

    html_status = "✓" if has_html else "✗"
    docx_status = "✓" if has_docx else "✗"

    if lang['is_original']:
        # Para español, el DOCX viene del HelpNDoc original
        return f"{lang['emoji']} {lang['name']:15} ✓ HTML | [Original HelpNDoc]"
    else:
        return f"{lang['emoji']} {lang['name']:15} {html_status} HTML | {docx_status} DOCX"


# =============================================================================
# PARTICULARIDADES IDIOMÁTICAS
# =============================================================================

def get_cultural_context(lang_code):
    """
    Obtiene el contexto cultural específico para cada idioma.
    Usado para personalizar traducciones según la cultura local.
    """
    cultural_contexts = {
        'en': {
            'region': 'International English',
            'audience': 'Global academic community',
            'formality': 'Professional but approachable',
            'education_terms': 'Standard international academic terminology',
            'platform_context': 'Learning Management System (LMS)',
            'key_adaptations': [
                'Use "course" instead of "class"',
                'Prefer "instructor" over "teacher"',
                'Use "assignment" rather than "task"',
                'American date format MM/DD/YYYY in examples'
            ]
        },
        'pt': {
            'region': 'Portuguese (Portugal focus)',
            'audience': 'Portuguese-speaking academic community',
            'formality': 'Formal but warm academic tone',
            'education_terms': 'European Portuguese academic terminology',
            'platform_context': 'Plataforma de Ensino à Distância',
            'key_adaptations': [
                'Use "disciplina" for course',
                'Prefer "docente" over "professor"',
                'Use "avaliação" for assessment',
                'European date format DD/MM/YYYY',
                'Use "utilizador" instead of "usuário"'
            ]
        },
        'fr': {
            'region': 'French (International Francophone)',
            'audience': 'French-speaking academic community',
            'formality': 'Formal academic French',
            'education_terms': 'Standard French educational terminology',
            'platform_context': 'Plateforme d\'Enseignement à Distance',
            'key_adaptations': [
                'Use "cours" for course',
                'Prefer "enseignant" for instructor',
                'Use "évaluation" for assessment',
                'French date format DD/MM/YYYY',
                'Formal "vous" throughout'
            ]
        },
        'it': {
            'region': 'Italian (Italy focus)',
            'audience': 'Italian academic community',
            'formality': 'Professional Italian academic style',
            'education_terms': 'Italian higher education terminology',
            'platform_context': 'Piattaforma di Apprendimento Digitale',
            'key_adaptations': [
                'Use "corso" for course',
                'Prefer "docente" for instructor',
                'Use "valutazione" for assessment',
                'Italian date format DD/MM/YYYY',
                'Use "Lei" form for politeness'
            ]
        },
        'de': {
            'region': 'German (DACH region)',
            'audience': 'German-speaking academic community',
            'formality': 'Formal German academic language',
            'education_terms': 'German educational system terminology',
            'platform_context': 'Lernmanagementsystem (LMS)',
            'key_adaptations': [
                'Use "Kurs" for course',
                'Prefer "Dozent/Lehrende" for instructor',
                'Use "Bewertung" for assessment',
                'German date format DD.MM.YYYY',
                'Formal "Sie" throughout'
            ]
        },
        'ca': {
            'region': 'Catalonia, Spain',
            'audience': 'Catalan academic community',
            'formality': 'Standard Catalan academic language',
            'education_terms': 'Catalan educational terminology',
            'platform_context': 'Campus Virtual / Plataforma d\'Aprenentatge',
            'key_adaptations': [
                'Use "curs" for course',
                'Prefer "professor/a" for instructor',
                'Use "avaluació" for assessment',
                'Spanish date format DD/MM/YYYY',
                'Catalan-specific academic terms'
            ]
        },
        'eu': {
            'region': 'Basque Country, Spain',
            'audience': 'Basque academic community',
            'formality': 'Standard Euskera academic language',
            'education_terms': 'Basque educational terminology',
            'platform_context': 'Campus Birtuala',
            'key_adaptations': [
                'Use "ikastaroa" for course',
                'Prefer "irakaslea" for instructor',
                'Use "ebaluazioa" for assessment',
                'Basque-specific academic terminology',
                'Cultural sensitivity to Basque identity'
            ]
        },
        'gl': {
            'region': 'Galicia, Spain',
            'audience': 'Galician academic community',
            'formality': 'Standard Galician academic language',
            'education_terms': 'Galician educational terminology',
            'platform_context': 'Campus Virtual',
            'key_adaptations': [
                'Use "curso" for course',
                'Prefer "profesor/a" for instructor',
                'Use "avaliación" for assessment',
                'Galician-specific academic terms',
                'Regional cultural context'
            ]
        },
        'nl': {
            'region': 'Netherlands/Belgium',
            'audience': 'Dutch-speaking academic community',
            'formality': 'Professional Dutch academic style',
            'education_terms': 'Dutch higher education terminology',
            'platform_context': 'Leerplatform / Virtuele Campus',
            'key_adaptations': [
                'Use "cursus" for course',
                'Prefer "docent" for instructor',
                'Use "beoordeling" for assessment',
                'Dutch date format DD-MM-YYYY',
                'Neutral/informal "je/jij" in instructions'
            ]
        },
        'da': {
            'region': 'Denmark',
            'audience': 'Danish academic community',
            'formality': 'Professional Danish academic style',
            'education_terms': 'Danish educational terminology',
            'platform_context': 'Læringsplatform',
            'key_adaptations': [
                'Use "kursus" for course',
                'Prefer "underviser" for instructor',
                'Use "bedømmelse" for assessment',
                'Danish date format DD/MM-YYYY',
                'Informal "du" in instructions'
            ]
        },
        'sv': {
            'region': 'Sweden',
            'audience': 'Swedish academic community',
            'formality': 'Professional Swedish academic style',
            'education_terms': 'Swedish educational terminology',
            'platform_context': 'Lärplattform',
            'key_adaptations': [
                'Use "kurs" for course',
                'Prefer "lärare/instruktör" for instructor',
                'Use "bedömning" for assessment',
                'Swedish date format YYYY-MM-DD',
                'Informal "du" in instructions'
            ]
        },
        'gn': {
            'region': 'Paraguay',
            'audience': 'Guaraní-speaking community in Paraguay',
            'formality': 'Respectful Guaraní with Spanish technical terms',
            'education_terms': 'Mixed Guaraní-Spanish educational terminology',
            'platform_context': 'Campus Virtual (technical terms in Spanish)',
            'key_adaptations': [
                'Mix of Guaraní and Spanish for technical terms',
                'Use Spanish for complex technical vocabulary',
                'Respectful Guaraní forms',
                'Cultural sensitivity to indigenous language',
                'Explain technical concepts clearly'
            ]
        }
    }

    return cultural_contexts.get(lang_code, {
        'region': 'Generic',
        'audience': 'General academic community',
        'formality': 'Professional academic style',
        'education_terms': 'Standard academic terminology',
        'platform_context': 'Learning Platform',
        'key_adaptations': ['Standard translation approach']
    })

def get_translation_instructions(lang_code, manual_type='open_aula_front'):
    """
    Genera instrucciones específicas de traducción para cada idioma.
    Combina el contexto cultural con el tipo de manual.
    """
    context = get_cultural_context(lang_code)

    # Tipo de audiencia según el manual
    if manual_type == 'open_aula_front':
        target_audience = "estudiantes y usuarios finales del campus virtual"
        content_focus = "interfaz de usuario, navegación, y funcionalidades de estudiante"
    else:  # open_aula_back
        target_audience = "administradores y gestores del campus virtual"
        content_focus = "configuración del sistema, gestión de usuarios, y herramientas administrativas"

    base_instructions = f"""
CONTEXTO DE TRADUCCIÓN:
- Región objetivo: {context['region']}
- Audiencia: {target_audience}
- Formalidad: {context['formality']}
- Plataforma: {context['platform_context']}
- Contenido: {content_focus}

DIRECTRICES ESPECÍFICAS:
"""

    for adaptation in context['key_adaptations']:
        base_instructions += f"- {adaptation}\n"

    base_instructions += f"""
TERMINOLOGÍA EDUCATIVA:
- Usar: {context['education_terms']}
- Mantener consistencia en términos técnicos del campus virtual
- Adaptar ejemplos a la región: {context['region']}

INSTRUCCIONES GENERALES:
- Mantener el formato HTML y todos los elementos técnicos
- No traducir nombres de archivos, URLs o código
- Adaptar ejemplos culturalmente cuando sea apropiado
- Mantener un tono {context['formality'].lower()}
- Priorizar claridad y usabilidad para {target_audience}
"""

    return base_instructions