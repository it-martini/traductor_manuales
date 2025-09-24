# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Run the main application
python3 traductor.py

# Install Python dependencies
pip install requests beautifulsoup4 python-docx lxml

# Install system dependencies for PDF generation
sudo apt-get install pandoc wkhtmltopdf
# Note: wkhtmltopdf patched binary is included in bin/ for better link support

# Configure API key
cp .env.example .env
# Edit .env and add your Claude API key
```

## System Architecture

This is a **manual translation system** that converts Spanish technical documentation to multiple languages using Claude AI, with intelligent caching and HTML-to-DOCX conversion.

### Core Components

- **Entry Point**: `traductor.py` - Single point of entry that launches the interactive menu
- **Main Menu**: `scripts/menu_main.py` - Interactive CLI with visual status of all translations
- **Web Server**: `scripts/webserver.py` - HTTP server with HTML table interface for browsing manuals
- **HTML Translator**: `scripts/html_translator.py` - Core translation engine with smart caching
- **DOCX Converter**: `scripts/docx_converter.py` - Converts translated HTML to formatted Word documents
- **Configuration**: `scripts/config.py`, `scripts/languages_config.py` and `scripts/system_config.py`

### Directory Structure

```
traductor_manuales/
├── traductor.py              # Main entry point
├── bin/                      # System binaries
│   └── wkhtmltopdf_patched   # Patched wkhtmltopdf for PDFs
├── original/                 # Source Spanish manuals
│   ├── open_aula_front_es/   # User manual (students)
│   └── open_aula_back_es/    # Admin manual (administrators)
├── output/                   # Generated translations by language
├── scripts/                  # Core system modules
├── cache/                    # Translation cache (translations.json)
└── logs/                     # Operation logs
```

### Key Architecture Patterns

**Smart Caching System**: The translator uses a sophisticated cache in `cache/translations.json` that stores:
- Original text and translation pairs
- Element type metadata
- Usage counts and timestamps
- Significantly reduces API costs on updates

**Dual Manual System**:
- `open_aula_front` - Student/user-facing manual
- `open_aula_back` - Administrator manual
Both are treated as separate translation projects.

**Language Configuration**: Languages are defined in `scripts/config.py` (and legacy `scripts/languages_config.py`) with:
- Native names and emoji flags
- Claude API language codes
- Output directory mappings
- Regional variations (Spanish regions: Catalan, Euskera, Galician)

## CLI Commands

### Interactive Menu (Recommended)
```bash
python3 traductor.py
```

### Direct Translation
```bash
# Translate user manual to English
python3 scripts/html_translator.py --lang en --manual open_aula_front

# Translate admin manual to Portuguese
python3 scripts/html_translator.py --lang pt --manual open_aula_back

# Force retranslation (ignores cache)
python3 scripts/html_translator.py --lang fr --manual open_aula_front --force
```

### DOCX and PDF Generation
```bash
# Generate Word document and PDF from translated HTML (automatic)
python3 scripts/docx_converter.py --lang en --manual open_aula_front

# Force regeneration
python3 scripts/docx_converter.py --lang en --manual open_aula_front --force
```

### Web Server for Manual Navigation
```bash
# Start integrated web server (from main menu option [6])
python3 traductor.py
# Then select [6] Encender/Apagar webserver → [1] Iniciar webserver

# Start standalone web server
python3 scripts/webserver.py

# Access web interface
http://localhost:8080
```

## Configuration Files

- **`.env`**: Contains `CLAUDE_API_KEY=your_key_here`
- **`scripts/config.py`**: Main configuration including languages and system settings
- **`scripts/languages_config.py`**: Legacy language configuration (still supported)
- **`scripts/system_config.py`**: System-specific settings (paths, timeouts, etc.)

## Translation Cost Management

The system includes built-in cost estimation and warnings:
- Estimates API costs before translation
- Auto-confirms translations under $1 USD
- Warns for translations over $5 USD
- Cache dramatically reduces costs for updates

## Cache System

The cache in `cache/translations.json` uses a two-format system:
- **New format**: `{"original": text, "translated": text, "element_type": type, "timestamp": time, "usage_count": count}`
- **Legacy format**: Direct string translations (maintained for compatibility)

Cache is automatically managed - no manual intervention needed.

## Development

### Adding New Languages
1. Edit `scripts/config.py` (or `scripts/languages_config.py` for legacy support)
2. Add new entry to `LANGUAGES` dict with proper `claude_code` and `output_dir`
3. System auto-creates directories as needed

### Adding New Manual Types
1. Place source files in `original/manual_name_es/`
2. Update `MANUALS` dict in `scripts/config.py`
3. System auto-detects new manuals in menu

### Translation Prompt Customization
The translation prompt is in Spanish (lines 112-123 in `html_translator.py`) for cleaner Claude responses. Modify the prompt in `HTMLTranslator.translate_text()` method.

## Common Operations

### Check Translation Status
The interactive menu shows visual status of all languages with HTML/DOCX completion indicators.

### Batch Operations
Use the interactive menu's mass operations for translating multiple languages efficiently.

## Recent Updates

### Enhanced PDF Generation
- **Multi-language support**: Automatic translation of titles, index, and footer text for all 13 supported languages
- **Professional styling**: Corporate colors (#17365D, #4F81BD), proper font sizes (32pt/24pt titles)
- **wkhtmltopdf integration**: Using patched binary in `bin/wkhtmltopdf_patched` for better internal link support
- **Automatic generation**: PDFs are generated automatically after DOCX creation
- **Improved layout**: Conservative page width similar to Word documents, proper margins (15mm-20mm)

### Supported Languages for DOCX/PDF
The system now supports complete title/index/footer translation for:
- Spanish, English, Portuguese, French, Italian, German
- Dutch, Catalan, Euskera, Galician, Danish, Swedish, Guaraní

### Output Structure (Updated)
```
output/{language}/open_aula_{type}_{code}/
├── html/                    # Translated HTML manual
├── docx/                   # Word and PDF documents
│   ├── manual_aula_{type}_{code}.docx  # ~24MB with images
│   └── media/              # Images and resources
└── pdf/                    # Generated PDFs
    └── manual_aula_{type}_{code}.pdf   # ~17MB with images and links
```

### Troubleshooting
- **API Key issues**: Verify `.env` file contains valid Claude API key
- **Missing Python dependencies**: Run `pip install requests beautifulsoup4 python-docx lxml`
- **Missing system dependencies**: Run `sudo apt-get install pandoc wkhtmltopdf`
- **PDF generation fails**: Check if `bin/wkhtmltopdf_patched` exists and is executable
- **Manual not found**: Ensure source files exist in `original/` directory