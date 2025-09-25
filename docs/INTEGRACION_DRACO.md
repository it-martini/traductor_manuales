# Plan de Integración: Traductor Multiidioma en Flujo de Sincronización Draco

## 📋 Resumen Ejecutivo

Este documento detalla el plan para integrar el sistema de traducción automática multiidioma en el flujo actual de sincronización de manuales con el servidor Draco.

## 🔄 Flujo Actual vs Propuesto

### Flujo Actual
```
1. Edición manual español (original/)
2. git add . && git commit
3. git push (repositorio interno)
4. git push externo (draco)
5. SSH draco → git pull
6. Deploy manual español
```

### Flujo Propuesto con Traducción
```
1. Edición manual español (original/)
2. git add . && git commit
3. 🆕 python3 scripts/sync_translator.py (traducción automática)
4. git push (incluye traducciones)
5. git push externo
6. SSH draco → git pull
7. Deploy multiidioma
```

## 🏗️ Arquitectura de Integración

### Opciones de Implementación

#### Opción A: Pre-commit Hook (Automático)
- **Ventajas**: Totalmente automático, nunca se olvida
- **Desventajas**: Commits más lentos, puede bloquear desarrollo
- **Implementación**: Hook en `.git/hooks/pre-commit`

#### Opción B: Script Manual con Automatización (Semi-automático) ⭐ RECOMENDADO
- **Ventajas**: Control sobre cuándo traducir, flexible
- **Desventajas**: Requiere recordar ejecutarlo
- **Implementación**: `scripts/sync_translator.py`

#### Opción C: CI/CD Pipeline (Ideal para producción)
- **Ventajas**: No bloquea desarrollo local, escalable
- **Desventajas**: Requiere infraestructura CI
- **Implementación**: GitHub Actions o GitLab CI

## 📁 Estructura de Directorios Propuesta

```
manuales.git/
├── es/                          # Fuente original (actual)
│   ├── open_aula_front/
│   └── open_aula_back/
├── translations/                # 🆕 Traducciones automáticas
│   ├── en/
│   │   ├── open_aula_front/
│   │   │   ├── html/
│   │   │   ├── docx/
│   │   │   └── pdf/
│   │   └── open_aula_back/
│   ├── pt/                     # Portugués
│   ├── fr/                     # Francés
│   ├── it/                     # Italiano
│   ├── de/                     # Alemán
│   ├── nl/                     # Neerlandés
│   ├── ca/                     # Catalán
│   ├── eu/                     # Euskera
│   ├── gl/                     # Gallego
│   ├── da/                     # Danés
│   ├── sv/                     # Sueco
│   └── gn/                     # Guaraní
├── scripts/                     # 🆕 Scripts de automatización
│   ├── sync_translator.py
│   ├── html_translator.py
│   ├── docx_converter.py
│   └── config.py
├── cache/                       # 🆕 Cache de traducciones
│   └── translations.json
└── bin/                         # 🆕 Binarios necesarios
    └── wkhtmltopdf_patched
```

## 🚀 Proceso de Sincronización Modificado

### 1. Desarrollo Local
```bash
# Editar manuales en español
cd /path/to/manuales.git
vim es/open_aula_front/index.html

# Verificar cambios
git status
git diff

# Agregar cambios
git add es/
```

### 2. Traducción Automática
```bash
# Detectar cambios y traducir automáticamente
python3 scripts/sync_translator.py

# O forzar traducción completa
python3 scripts/sync_translator.py --force

# O traducir manual específico
python3 scripts/sync_translator.py --manual open_aula_front
```

### 3. Commit con Traducciones
```bash
# El script hace commit automático, o manual:
git add translations/ cache/
git commit -m "#12345 - Actualización manual + traducciones multiidioma"
```

### 4. Sincronización a Repositorios
```bash
# Push a repositorio interno
git push

# Push a repositorio externo (draco)
git push externo
```

### 5. Deploy en Draco
```bash
# SSH a draco
ssh devops
ssh educativa_manuales

# Actualizar repositorio
cd /var/www/educativa/manuales.educativa.com.git
git pull

# Crear links simbólicos para cada idioma (una vez)
cd /var/www/educativa/manuales.educativa.com
ln -s manuales.educativa.com.git/translations/en en
ln -s manuales.educativa.com.git/translations/pt pt
ln -s manuales.educativa.com.git/translations/fr fr
# ... para cada idioma
```

## 🔧 Script sync_translator.py

### Funcionalidades Principales

1. **Detección Inteligente de Cambios**
   - Usa `git diff HEAD~1` para detectar archivos modificados
   - Identifica qué manual fue modificado (front/back)
   - Solo traduce manuales afectados

2. **Traducción Incremental**
   - Cache inteligente reduce costos API
   - Solo traduce elementos modificados
   - Mantiene consistencia terminológica

3. **Generación Múltiple**
   - HTML: Manual navegable web
   - DOCX: Documento Word descargable
   - PDF: Documento PDF con enlaces internos

4. **Commit Automático**
   - Mensaje descriptivo con manuales traducidos
   - Incluye timestamp
   - Formato: "🌍 Auto-traducción: open_aula_front - 2025-01-25 14:30"

### Uso del Script

```bash
# Uso básico (detecta cambios automáticamente)
python3 scripts/sync_translator.py

# Forzar traducción completa
python3 scripts/sync_translator.py --force

# Traducir manual específico
python3 scripts/sync_translator.py --manual open_aula_front

# Solo detectar cambios sin traducir
python3 scripts/sync_translator.py --detect-only

# Ver ayuda
python3 scripts/sync_translator.py --help
```

## 📦 Requisitos del Sistema

### En Servidor Draco

Para verificar requisitos, ejecutar el script `check_draco_requirements.sh`:

```bash
# Copiar script a draco
scp check_draco_requirements.sh devops:~/

# Ejecutar verificación
ssh devops
ssh educativa_manuales
cd /var/www/educativa/manuales.educativa.com.git
bash ~/check_draco_requirements.sh
```

### Requisitos Mínimos

#### Sistema
- Python 3.7+
- Git
- 5GB espacio en disco

#### Librerías Python
```bash
pip3 install requests beautifulsoup4 python-docx lxml anthropic
```

#### Herramientas de Conversión
```bash
sudo apt-get install pandoc wkhtmltopdf
```

#### Configuración
- Archivo `.env` con `CLAUDE_API_KEY`
- Permisos de escritura en `output/` y `cache/`

## 🌐 URLs Finales

Tras la implementación, los manuales estarán disponibles en:

- Español: `https://manuales.educativa.com/` (actual)
- Inglés: `https://manuales.educativa.com/en/`
- Portugués: `https://manuales.educativa.com/pt/`
- Francés: `https://manuales.educativa.com/fr/`
- Italiano: `https://manuales.educativa.com/it/`
- Alemán: `https://manuales.educativa.com/de/`
- Neerlandés: `https://manuales.educativa.com/nl/`
- Catalán: `https://manuales.educativa.com/ca/`
- Euskera: `https://manuales.educativa.com/eu/`
- Gallego: `https://manuales.educativa.com/gl/`
- Danés: `https://manuales.educativa.com/da/`
- Sueco: `https://manuales.educativa.com/sv/`
- Guaraní: `https://manuales.educativa.com/gn/`

## 💰 Consideraciones de Costos

### Estimaciones por Manual
- Manual completo (97 archivos HTML): ~$3-5 USD primera vez
- Actualizaciones incrementales: ~$0.10-0.50 USD
- Cache reduce costos en 80-90% para actualizaciones

### Optimizaciones
- Cache inteligente con `translations.json`
- Traducción solo de elementos modificados
- Batch processing para reducir llamadas API

## 🔐 Seguridad

- API key de Claude en `.env` (nunca en git)
- Archivo `.env` con permisos 600
- No traducir contenido sensible (passwords, tokens)

## 📝 Checklist de Implementación

- [ ] Verificar requisitos en draco con `check_draco_requirements.sh`
- [ ] Instalar dependencias faltantes
- [ ] Copiar traductor_manuales al servidor
- [ ] Configurar `.env` con API key
- [ ] Probar traducción de un manual
- [ ] Configurar estructura de directorios
- [ ] Crear links simbólicos en Apache/Nginx
- [ ] Modificar proceso de documentación
- [ ] Capacitar equipo en nuevo flujo
- [ ] Monitorear primeras ejecuciones

## 🚨 Troubleshooting

### Problema: API key no válida
```bash
# Verificar .env
cat .env | grep CLAUDE_API_KEY
# Actualizar si es necesario
```

### Problema: Sin permisos de escritura
```bash
# Dar permisos al usuario
chmod -R 755 output/ cache/ logs/
chown -R educativa_manuales:educativa_manuales output/ cache/
```

### Problema: Falta librería Python
```bash
# Instalar con pip3
pip3 install [librería]
```

### Problema: PDF no se genera
```bash
# Verificar wkhtmltopdf
which wkhtmltopdf
# O usar binario parcheado
./bin/wkhtmltopdf_patched --version
```

## 📅 Timeline Sugerido

1. **Semana 1**: Preparación entorno draco
2. **Semana 2**: Pruebas con un manual
3. **Semana 3**: Traducción completa inicial
4. **Semana 4**: Configuración web server
5. **Semana 5**: Go-live y monitoreo

## 📞 Contacto y Soporte

Para dudas sobre la implementación, revisar:
- Documentación: `CLAUDE.md`
- Logs: `logs/translator.log`
- Cache: `cache/translations.json`

---

*Documento generado: 2025-01-25*
*Versión: 1.0*