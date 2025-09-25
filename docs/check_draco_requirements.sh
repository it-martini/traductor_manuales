#!/bin/bash
# Script para verificar requisitos en el servidor draco
# Ejecutar en draco para verificar si tiene todo lo necesario para el traductor

echo "================================================"
echo "    VERIFICACIÓN DE REQUISITOS PARA TRADUCTOR  "
echo "================================================"
echo ""

# Variables para tracking
REQUIREMENTS_MET=true
MISSING_ITEMS=""

# Función para verificar comando
check_command() {
    local CMD=$1
    local NAME=$2
    local REQUIRED=$3

    if command -v $CMD &> /dev/null; then
        VERSION=$($CMD --version 2>&1 | head -n1)
        echo "✅ $NAME: Instalado"
        echo "   Versión: $VERSION"
    else
        if [ "$REQUIRED" = "required" ]; then
            echo "❌ $NAME: NO ENCONTRADO (REQUERIDO)"
            REQUIREMENTS_MET=false
            MISSING_ITEMS="$MISSING_ITEMS\n  - $NAME ($CMD)"
        else
            echo "⚠️  $NAME: No encontrado (opcional)"
        fi
    fi
    echo ""
}

# Función para verificar módulo Python
check_python_module() {
    local MODULE=$1
    local NAME=$2

    if python3 -c "import $MODULE" &> /dev/null; then
        VERSION=$(python3 -c "import $MODULE; print(getattr($MODULE, '__version__', 'installed'))" 2>/dev/null)
        echo "✅ $NAME: Instalado (versión: $VERSION)"
    else
        echo "❌ $NAME: NO INSTALADO (REQUERIDO)"
        REQUIREMENTS_MET=false
        MISSING_ITEMS="$MISSING_ITEMS\n  - Python module: $MODULE"
    fi
}

echo "1. VERIFICANDO PYTHON Y PIP"
echo "----------------------------"
check_command "python3" "Python 3" "required"

# Verificar versión de Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$PYTHON_VERSION >= 3.7" | bc -l) )); then
        echo "   ✅ Versión Python adecuada: $PYTHON_VERSION (>= 3.7)"
    else
        echo "   ⚠️  Versión Python antigua: $PYTHON_VERSION (se recomienda >= 3.7)"
    fi
fi

check_command "pip3" "pip3" "required"

echo ""
echo "2. VERIFICANDO LIBRERÍAS PYTHON"
echo "--------------------------------"
check_python_module "requests" "requests"
check_python_module "bs4" "beautifulsoup4"
check_python_module "docx" "python-docx"
check_python_module "lxml" "lxml"
check_python_module "anthropic" "anthropic (Claude API)"

echo ""
echo "3. VERIFICANDO HERRAMIENTAS DE CONVERSIÓN"
echo "------------------------------------------"
check_command "pandoc" "Pandoc" "required"
check_command "wkhtmltopdf" "wkhtmltopdf" "optional"

# Verificar si existe el binario parcheado
echo "Verificando binario parcheado de wkhtmltopdf..."
if [ -f "./bin/wkhtmltopdf_patched" ]; then
    echo "✅ Binario parcheado encontrado en ./bin/"
    if [ -x "./bin/wkhtmltopdf_patched" ]; then
        echo "   ✅ Es ejecutable"
    else
        echo "   ⚠️  No tiene permisos de ejecución"
        echo "   Ejecutar: chmod +x ./bin/wkhtmltopdf_patched"
    fi
else
    echo "⚠️  Binario parcheado no encontrado en ./bin/"
    echo "   Se usará wkhtmltopdf del sistema si está disponible"
fi

echo ""
echo "4. VERIFICANDO HERRAMIENTAS GIT"
echo "--------------------------------"
check_command "git" "Git" "required"

# Verificar configuración git
if command -v git &> /dev/null; then
    echo "Configuración Git:"
    GIT_USER=$(git config --global user.name 2>/dev/null)
    GIT_EMAIL=$(git config --global user.email 2>/dev/null)

    if [ -n "$GIT_USER" ]; then
        echo "   ✅ Usuario: $GIT_USER"
    else
        echo "   ⚠️  Usuario no configurado"
    fi

    if [ -n "$GIT_EMAIL" ]; then
        echo "   ✅ Email: $GIT_EMAIL"
    else
        echo "   ⚠️  Email no configurado"
    fi
fi

echo ""
echo "5. VERIFICANDO ESTRUCTURA DE DIRECTORIOS"
echo "-----------------------------------------"
# Verificar directorios esperados
DIRS_TO_CHECK="original output cache scripts logs"

for DIR in $DIRS_TO_CHECK; do
    if [ -d "./$DIR" ]; then
        echo "✅ Directorio $DIR/ existe"
    else
        echo "⚠️  Directorio $DIR/ no encontrado"
    fi
done

echo ""
echo "6. VERIFICANDO ARCHIVOS DE CONFIGURACIÓN"
echo "-----------------------------------------"
if [ -f ".env" ]; then
    echo "✅ Archivo .env encontrado"
    if grep -q "CLAUDE_API_KEY" .env; then
        echo "   ✅ CLAUDE_API_KEY configurada"
    else
        echo "   ❌ CLAUDE_API_KEY no encontrada en .env"
        REQUIREMENTS_MET=false
    fi
else
    echo "❌ Archivo .env NO encontrado"
    echo "   Crear desde: cp .env.example .env"
    REQUIREMENTS_MET=false
fi

echo ""
echo "7. VERIFICANDO PERMISOS DE ESCRITURA"
echo "-------------------------------------"
# Verificar permisos de escritura en directorios clave
for DIR in output cache logs; do
    if [ -w "./$DIR" ] 2>/dev/null; then
        echo "✅ Permisos de escritura en $DIR/"
    else
        echo "❌ Sin permisos de escritura en $DIR/"
        REQUIREMENTS_MET=false
    fi
done

echo ""
echo "8. VERIFICANDO ESPACIO EN DISCO"
echo "--------------------------------"
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "Espacio disponible: $AVAILABLE_SPACE"

# Convertir a GB para comparación (aproximado)
SPACE_NUM=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$SPACE_NUM" -gt 5 ]; then
    echo "✅ Espacio suficiente (se recomiendan al menos 5GB)"
else
    echo "⚠️  Espacio limitado (se recomiendan al menos 5GB)"
fi

echo ""
echo "================================================"
echo "                   RESUMEN                      "
echo "================================================"
echo ""

if [ "$REQUIREMENTS_MET" = true ]; then
    echo "✅ TODOS LOS REQUISITOS CRÍTICOS ESTÁN CUMPLIDOS"
    echo ""
    echo "El servidor está listo para ejecutar el traductor."
else
    echo "❌ FALTAN REQUISITOS CRÍTICOS"
    echo ""
    echo "Elementos faltantes:$MISSING_ITEMS"
    echo ""
    echo "COMANDOS DE INSTALACIÓN SUGERIDOS:"
    echo "-----------------------------------"
    echo ""
    echo "# Para Ubuntu/Debian:"
    echo "sudo apt-get update"
    echo "sudo apt-get install python3 python3-pip pandoc wkhtmltopdf git"
    echo ""
    echo "# Instalar librerías Python:"
    echo "pip3 install requests beautifulsoup4 python-docx lxml anthropic"
    echo ""
    echo "# Configurar API key de Claude:"
    echo "cp .env.example .env"
    echo "# Editar .env y agregar CLAUDE_API_KEY=tu_clave_aqui"
fi

echo ""
echo "================================================"
echo "          INFORMACIÓN DEL SISTEMA               "
echo "================================================"
echo ""
echo "Sistema operativo:"
uname -a
echo ""
echo "Distribución:"
if [ -f /etc/os-release ]; then
    cat /etc/os-release | grep -E "^(NAME|VERSION)="
else
    echo "No se pudo determinar"
fi

echo ""
echo "Script finalizado."