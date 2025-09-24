#!/usr/bin/env python3
"""
Script principal del Sistema de Traducción de Manuales
Punto de entrada único para todas las operaciones
"""

import sys
from pathlib import Path

# Agregar directorio de scripts al path
scripts_dir = Path(__file__).parent / 'scripts'
sys.path.append(str(scripts_dir))

from menu_main import MainMenu

def main():
    """Función principal"""
    try:
        print("🚀 Iniciando Sistema de Traducción de Manuales...")
        print("   📁 Directorio base:", Path(__file__).parent)
        print()

        menu = MainMenu()
        menu.run()

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()