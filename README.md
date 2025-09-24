# Sistema de Traducción de Manuales - Campus Virtual

Sistema completo para traducir manuales del campus virtual a múltiples idiomas, con conversión automática de HTML a DOCX.

## Estructura del Proyecto

```
traductor_manuales/
├── traductor.py           # Script principal de entrada
├── .env                   # Configuración API (no versionado)
├── README.md              # Documentación principal
├── CLAUDE.md              # Instrucciones para Claude Code
│
├── scripts/               # Sistema de traducción
│   ├── main.py            # Lógica principal
│   ├── menu_main.py       # Menú interactivo
│   ├── html_translator.py # Traductor HTML
│   ├── docx_converter.py  # Conversor DOCX
│   ├── html_to_docx.py    # Procesamiento HTML→DOCX
│   ├── toc_handler.py     # Manejo de TOC e índices
│   ├── languages_config.py# Configuración de idiomas
│   └── system_config.py   # Configuración del sistema
│
├── original/              # Manuales originales
│   ├── open_aula_front_es/ # Manual de usuario (97 páginas)
│   └── open_aula_back_es/  # Manual de administración
│
├── output/                # Traducciones generadas
│   └── ingles/            # Inglés completado
│       └── open_aula_front_en/ # Manual de usuario en inglés
│
└── cache/                 # Caché de traducciones (500KB)
    └── translations.json  # Caché persistente
```

## Tipos de Manuales

### 📘 Manual de Usuario (Front-end)
- **Nombre**: `open_aula_front`
- **Audiencia**: Estudiantes y usuarios finales
- **DOCX generado**: `manual_aula_front_{codigo}.docx`

### 📕 Manual de Administración (Back-end)
- **Nombre**: `open_aula_back`
- **Audiencia**: Administradores del sistema
- **DOCX generado**: `manual_aula_back_{codigo}.docx`

## Idiomas Soportados

### Principales (prioridad alta):
- 🇺🇸 **Inglés** (English) - `en`
- 🇵🇹 **Portugués** (Português) - `pt`
- 🇫🇷 **Francés** (Français) - `fr`
- 🇮🇹 **Italiano** (Italiano) - `it`

### Regionales España (prioridad media):
- 🏴 **Catalán** (Català) - `ca`
- 🏴 **Euskera** (Euskera) - `eu`
- 🏴 **Gallego** (Galego) - `gl`

### Adicionales (prioridad baja):
- 🇩🇪 **Alemán** (Deutsch) - `de`
- 🇳🇱 **Neerlandés** (Nederlands) - `nl`
- 🇩🇰 **Danés** (Dansk) - `da`
- 🇸🇪 **Sueco** (Svenska) - `sv`
- 🇵🇾 **Guaraní** (Avañe'ẽ) - `gn`

## Configuración

### 1. API Key de Claude

Crear archivo `.env` en el directorio raíz:

```bash
cp .env.example .env
# Editar .env y agregar tu API key de Claude
```

### 2. Dependencias

#### Dependencias Python
```bash
pip install requests beautifulsoup4 python-docx lxml
```

#### Dependencias del sistema (para generación de PDF)
```bash
# Ubuntu/Debian
sudo apt-get install pandoc wkhtmltopdf

# macOS
brew install pandoc wkhtmltopdf

# El proyecto incluye un binario parcheado en bin/wkhtmltopdf_patched
# para mejor soporte de enlaces internos
```

## Uso

### Iniciar el sistema

```bash
cd ~/tmp/traductor_manuales
python3 traductor.py
```

### Menú principal

El sistema presenta un menú interactivo con:

- **Estado visual** de todos los idiomas
- **Opciones inteligentes** según lo que existe
- **Estimaciones de costo** para traducciones
- **Progreso en tiempo real**

### Operaciones disponibles

1. **Traducir HTML**: Convierte el manual español a otro idioma
2. **Generar DOCX + PDF**: Crea DOCX y PDF desde HTML traducido
3. **Proceso completo**: Traduce + genera DOCX + PDF automáticamente
4. **Operaciones masivas**: Para múltiples idiomas

### Uso desde línea de comandos

```bash
# Traducir manual de usuario a inglés
python3 scripts/html_translator.py --lang en --manual open_aula_front

# Generar DOCX + PDF del manual de administración en francés
python3 scripts/docx_converter.py --lang fr --manual open_aula_back

# Forzar regeneración
python3 scripts/html_translator.py --lang pt --manual open_aula_front --force
```

## Características

### Sistema de Caché Inteligente
- **Reutiliza traducciones** previas automáticamente
- **Reduce costos** significativamente en actualizaciones
- **Mejora velocidad** en retraducciones

### Conversión HTML → DOCX → PDF Optimizada
- **Enlaces internos REALES** funcionando con bookmarks en ambos formatos
- **Enlaces externos** preservados y funcionales
- **Imágenes inteligentes**: detección automática inline/standalone
- **Página de título** traducida automáticamente para 13 idiomas
- **Índice jerárquico** con numeración automática traducido por idioma
- **Pie de página profesional** con copyright y paginación traducida
- **PDF con estilo corporativo**: colores (#17365D, #4F81BD), títulos grandes (32pt/24pt)
- **Generación automática PDF** después de cada DOCX
- **Filtrado automático** de páginas irrelevantes (Home, descarga PDF)

### Particularidades Idiomáticas
- **Adaptaciones culturales** por región
- **Terminología específica** por país
- **Formatos locales** (fechas, números)
- **Variantes regionales** del mismo idioma

### Interfaz Intuitiva
- **Estado visual** de todos los idiomas
- **Confirmaciones inteligentes** para operaciones costosas
- **Progreso en tiempo real** con estimaciones
- **Detección automática** de lo que falta

## Flujo de Trabajo Típico

### Para un idioma nuevo:

1. **Seleccionar manual** en el menú (Usuario o Administración)
2. **Elegir "Proceso completo"**
3. **Seleccionar idioma** destino
4. **Confirmar costo** estimado
5. **Esperar traducción** (15-30 min para manual completo)
6. **DOCX y PDF generados** automáticamente

### Para actualización:

1. El sistema **detecta automáticamente** qué existe
2. Ofrece opciones para **regenerar solo DOCX** si HTML ya existe
3. **Caché inteligente** reduce dramáticamente el tiempo

## Costos Estimados

- **Manual completo nuevo**: ~$2-4 USD
- **Actualizaciones menores**: ~$0.20-0.50 USD (gracias al caché)
- **Solo regenerar DOCX**: $0 USD

## Archivos de Salida

### Para cada idioma se genera:

```
output/{idioma_legible}/open_aula_{tipo}_{codigo}/
├── html/                           # Manual navegable web
│   ├── *.html                      # Páginas traducidas (94 páginas)
│   ├── lib/                        # Imágenes y recursos
│   ├── css/                        # Estilos
│   ├── js/                         # JavaScript
│   ├── vendors/                    # Librerías
│   ├── _toc.json                   # Estructura de navegación
│   └── index.html                  # Página principal
├── docx/                           # Documentos para descarga
│   ├── manual_aula_{tipo}_{codigo}.docx  # ~24MB con imágenes
│   └── media/                      # Imágenes y recursos
└── pdf/                            # PDF optimizado
    └── manual_aula_{tipo}_{codigo}.pdf   # ~17MB con enlaces funcionales
```

**Ejemplos actuales:**
- `output/ingles/open_aula_front_en/docx/manual_aula_front_en.docx` (24MB)
- `output/ingles/open_aula_front_en/pdf/manual_aula_front_en.pdf` (17MB)
- `output/italiano/open_aula_front_it/docx/manual_aula_front_it.docx` (24MB)
- `output/italiano/open_aula_front_it/pdf/manual_aula_front_it.pdf` (17MB)

## Estado Actual

### ✅ Completado:
- 🇪🇸 **Español**: Manual de usuario original (`open_aula_front_es`)
- 🇺🇸 **Inglés**: Manual de usuario completo (HTML + DOCX optimizado)

### 📁 Disponible para traducir:
- 🇪🇸 **Español**: Manual de administración (`open_aula_back_es`)

### 🌍 Idiomas configurados:
- 🇵🇹 Portugués, 🇫🇷 Francés, 🇮🇹 Italiano, 🇩🇪 Alemán
- 🇳🇱 Neerlandés, 🏴 Catalán, 🏴 Euskera, 🏴 Gallego
- 🇩🇰 Danés, 🇸🇪 Sueco, 🇵🇾 Guaraní

## Monitoreo y Caché

- **Caché persistente** en `cache/translations.json`
- **Estado en tiempo real** en la interfaz
- **Output directo** en pantalla durante operaciones

## Troubleshooting

### Error de API Key
```bash
# Verificar .env
cat .env
# Debe contener: CLAUDE_API_KEY=tu_key_aqui
```

### Error de dependencias
```bash
pip install --upgrade requests beautifulsoup4 python-docx lxml
```

### Manual no encontrado
- Verificar que existe `original/open_aula_front_es/` con archivos HTML
- Verificar que existe `original/open_aula_back_es/` para manual de administración

## Desarrollo

### Agregar nuevo idioma
1. Editar `scripts/languages_config.py`
2. Agregar entrada en diccionario `LANGUAGES`
3. Incluir `output_dir` y códigos apropiados
4. Los directorios se crean automáticamente

### Personalizar traducciones
- Modificar prompts en `scripts/html_translator.py`
- Ajustar configuración en `scripts/system_config.py`
- Agregar particularidades en `scripts/languages_config.py`

### Agregar nuevo tipo de manual
1. Colocar archivos fuente en `original/nombre_manual_es/`
2. Actualizar `MANUALS` en `scripts/languages_config.py`
3. El sistema detectará automáticamente el nuevo manual

---

**Desarrollado para e-ducativa Educación Virtual S.A.**
Sistema de traducción inteligente con caché para optimización de costos y adaptaciones idiomáticas.