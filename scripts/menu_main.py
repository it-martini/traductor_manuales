#!/usr/bin/env python3
"""
Menú principal interactivo para el sistema de traducción de manuales
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Agregar el directorio actual al path para imports
sys.path.append(str(Path(__file__).parent))

from languages_config import LANGUAGES, MANUALS, get_language_display_name, format_language_status
from system_config import *

class ManualStatus:
    """Analiza y mantiene el estado de los manuales"""

    def __init__(self):
        self.status = {}
        self.scan_all_manuals()

    def scan_all_manuals(self):
        """Escanea el estado de todos los manuales en todos los idiomas"""
        for manual_key, manual_info in MANUALS.items():
            self.status[manual_key] = {}

            for lang_code in LANGUAGES.keys():
                html_exists = self.check_html_exists(manual_key, lang_code)
                docx_exists = self.check_docx_exists(manual_key, lang_code)

                self.status[manual_key][lang_code] = {
                    'html': html_exists,
                    'docx': docx_exists,
                    'html_count': self.count_html_files(manual_key, lang_code) if html_exists else 0
                }

    def check_html_exists(self, manual_key, lang_code):
        """Verifica si existen archivos HTML para un manual/idioma"""
        if lang_code == 'es':
            path = get_manual_path(manual_key)
        else:
            path = get_manual_path(manual_key, lang_code, 'html')

        return path.exists() and any(path.glob('*.html'))

    def check_docx_exists(self, manual_key, lang_code):
        """Verifica si existe DOCX para un manual/idioma"""
        if lang_code == 'es':
            # Para español, asumimos que existe el DOCX original del HelpNDoc
            return MANUALS[manual_key].get('has_docx_original', False)
        else:
            path = get_manual_path(manual_key, lang_code, 'docx')
            return path.exists() and any(path.glob('*.docx'))

    def count_html_files(self, manual_key, lang_code):
        """Cuenta archivos HTML para un manual/idioma"""
        if lang_code == 'es':
            path = get_manual_path(manual_key)
        else:
            path = get_manual_path(manual_key, lang_code, 'html')

        if not path.exists():
            return 0

        return len(list(path.glob('*.html')))

    def get_manual_summary(self, manual_key):
        """Genera resumen del estado de un manual"""
        manual_status = self.status.get(manual_key, {})
        total_langs = len(LANGUAGES)
        # Contar traducciones + el español original (que siempre tiene HTML)
        langs_with_html = sum(1 for lang_status in manual_status.values() if lang_status.get('html', False)) + 1  # +1 por español
        langs_with_docx = sum(1 for lang_status in manual_status.values() if lang_status.get('docx', False))

        return {
            'total_languages': total_langs,
            'html_complete': langs_with_html,
            'docx_complete': langs_with_docx,
            'completion_percent': (langs_with_html / total_langs) * 100
        }

class MainMenu:
    """Menú principal del sistema"""

    def __init__(self):
        self.status = ManualStatus()
        ensure_directories()

    def print_header(self):
        """Imprime header principal"""
        print("═" * 70)
        print("       TRADUCTOR DE MANUALES - Campus Virtual")
        print("═" * 70)
        print()

    def print_manual_status(self, manual_key):
        """Imprime el estado detallado de un manual"""
        manual_info = MANUALS[manual_key]
        print(f"📚 {manual_info['name']} - Estado por idioma:")
        print("┌" + "─" * 60 + "┐")

        for lang_code, lang_info in LANGUAGES.items():
            status = self.status.status[manual_key].get(lang_code, {})
            status_line = format_language_status(
                lang_code,
                status.get('html', False),
                status.get('docx', False)
            )
            print(f"│ {status_line:<58} │")

        print("└" + "─" * 60 + "┘")
        print()

        # Resumen
        summary = self.status.get_manual_summary(manual_key)
        print(f"📊 Resumen: {summary['html_complete']}/{summary['total_languages']} idiomas con HTML "
              f"({summary['completion_percent']:.1f}% completo)")
        print()

    def show_main_menu(self):
        """Muestra el menú principal"""
        self.print_header()

        # Mostrar estado de todos los manuales
        for manual_key in MANUALS.keys():
            self.print_manual_status(manual_key)

        print("🌍 OPCIONES PRINCIPALES:")
        print("┌" + "─" * 50 + "┐")
        print("│ [1] Seleccionar manual para trabajar         │")
        print("│ [2] Ver estado detallado                     │")
        print("│ [3] Configuración del sistema                │")
        print("│ [4] Limpiar caché de traducciones            │")
        print("│ [5] Ver logs de operaciones                  │")
        print("│ [6] Encender/Apagar webserver                │")
        print("│                                              │")
        print("│ [0] Salir                                    │")
        print("└" + "─" * 50 + "┘")
        print()

    def show_manual_menu(self, manual_key):
        """Muestra menú para un manual específico"""
        manual_info = MANUALS[manual_key]

        print(f"📚 TRABAJANDO CON: {manual_info['name']}")
        print("═" * 50)
        print()

        self.print_manual_status(manual_key)

        print("🔧 OPERACIONES DISPONIBLES:")
        print("┌" + "─" * 48 + "┐")
        print("│ [1] Traducir HTML a un idioma específico    │")
        print("│ [2] Generar DOCX desde HTML existente       │")
        print("│ [3] Proceso completo (traducir + DOCX)      │")
        print("│ [4] Traducir múltiples idiomas               │")
        print("│ [5] Generar todos los DOCX                  │")
        print("│ [6] Proceso masivo (todo)                   │")
        print("│                                             │")
        print("│ [0] Volver al menú principal                │")
        print("└" + "─" * 48 + "┘")
        print()

    def show_language_selection(self, only_missing=False):
        """Muestra selección de idiomas"""
        available_langs = [k for k in LANGUAGES.keys() if k != 'es']

        print("🌍 SELECCIONAR IDIOMA:")
        print("┌" + "─" * 40 + "┐")

        for i, lang_code in enumerate(available_langs, 1):
            lang_name = get_language_display_name(lang_code)
            print(f"│ [{i:2d}] {lang_name:<30} │")

        print("│                                        │")
        print("│ [0] Cancelar                           │")
        print("└" + "─" * 40 + "┘")
        print()

        return available_langs

    def get_user_choice(self, prompt="Selección", valid_range=None):
        """Obtiene selección del usuario con validación"""
        while True:
            try:
                choice = input(f"{prompt}: ").strip()
                if not choice:
                    continue

                choice_num = int(choice)

                if valid_range and choice_num not in valid_range:
                    print(f"❌ Opción inválida. Selecciona entre {min(valid_range)}-{max(valid_range)}")
                    continue

                return choice_num

            except ValueError:
                print("❌ Por favor ingresa un número válido")
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                sys.exit(0)

    def run(self):
        """Ejecuta el menú principal"""
        while True:
            self.show_main_menu()
            choice = self.get_user_choice("Selección", range(0, 7))

            if choice == 0:
                print("\n👋 ¡Hasta luego!")
                break
            elif choice == 1:
                self.select_manual_menu()
            elif choice == 2:
                self.show_detailed_status()
            elif choice == 3:
                self.show_configuration()
            elif choice == 4:
                self.clear_cache()
            elif choice == 5:
                self.show_logs()
            elif choice == 6:
                self.webserver_menu()

    def select_manual_menu(self):
        """Menú de selección de manual"""
        print("\n📚 SELECCIONAR MANUAL:")
        print("┌" + "─" * 40 + "┐")

        manual_keys = list(MANUALS.keys())
        for i, manual_key in enumerate(manual_keys, 1):
            manual_info = MANUALS[manual_key]
            print(f"│ [{i}] {manual_info['name']:<30} │")

        print("│                                        │")
        print("│ [0] Volver                             │")
        print("└" + "─" * 40 + "┘")
        print()

        choice = self.get_user_choice("Selección", range(0, len(manual_keys) + 1))

        if choice == 0:
            return

        manual_key = manual_keys[choice - 1]
        self.manual_operations_menu(manual_key)

    def manual_operations_menu(self, manual_key):
        """Menú de operaciones para un manual específico"""
        while True:
            self.show_manual_menu(manual_key)
            choice = self.get_user_choice("Selección", range(0, 7))

            if choice == 0:
                break
            elif choice == 1:
                self.translate_single_language(manual_key)
            elif choice == 2:
                self.generate_docx_from_html(manual_key)
            elif choice == 3:
                self.complete_process_single(manual_key)
            elif choice == 4:
                self.translate_multiple_languages(manual_key)
            elif choice == 5:
                self.generate_all_docx(manual_key)
            elif choice == 6:
                self.complete_process_all(manual_key)

    def translate_single_language(self, manual_key):
        """Traduce a un solo idioma"""
        available_langs = self.show_language_selection()
        choice = self.get_user_choice("Idioma", range(0, len(available_langs) + 1))

        if choice == 0:
            return

        target_lang = available_langs[choice - 1]
        print(f"\n🔄 Traduciendo {MANUALS[manual_key]['name']} a {get_language_display_name(target_lang)}")

        try:
            # Importar y usar el traductor HTML
            from html_translator import MultiLanguageHTMLTranslator

            translator = MultiLanguageHTMLTranslator(manual_key)

            print("⏳ Iniciando traducción...")
            result = translator.translate_manual(target_lang)

            if result['success']:
                print(f"✅ Traducción completada!")
                print(f"📁 HTML generado")
                if 'files_processed' in result:
                    print(f"📊 Archivos procesados: {result['files_processed']}")
                if 'time_elapsed' in result:
                    print(f"⏱️ Tiempo: {result['time_elapsed']/60:.1f} minutos")

                # Actualizar estado
                self.status.scan_all_manuals()

                # Preguntar si generar DOCX
                response = input("\n¿Generar DOCX también? (s/N): ").lower()
                if response in ['s', 'si', 'y', 'yes']:
                    self._generate_docx_for_language(manual_key, target_lang)
            else:
                print(f"❌ Error en traducción: {result['message']}")

        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        input("\nPresiona Enter para continuar...")

    def generate_docx_from_html(self, manual_key):
        """Genera DOCX desde HTML existente"""
        # Mostrar idiomas que tienen HTML pero no DOCX
        available_langs = []
        for lang_code in LANGUAGES.keys():
            if lang_code == 'es':
                continue  # El español no genera DOCX
            status = self.status.status[manual_key].get(lang_code, {})
            if status.get('html', False):
                available_langs.append(lang_code)

        if not available_langs:
            print("\n❌ No hay idiomas con HTML traducido para generar DOCX")
            input("Presiona Enter para continuar...")
            return

        print("\n🌍 IDIOMAS CON HTML DISPONIBLE:")
        print("┌" + "─" * 40 + "┐")

        for i, lang_code in enumerate(available_langs, 1):
            lang_name = get_language_display_name(lang_code)
            print(f"│ [{i:2d}] {lang_name:<30} │")

        print("│                                        │")
        print("│ [0] Cancelar                           │")
        print("└" + "─" * 40 + "┘")
        print()

        choice = self.get_user_choice("Idioma", range(0, len(available_langs) + 1))

        if choice == 0:
            return

        target_lang = available_langs[choice - 1]
        print(f"\n📄 Generando DOCX para {get_language_display_name(target_lang)}")

        self._generate_docx_for_language(manual_key, target_lang)
        input("\nPresiona Enter para continuar...")

    def complete_process_single(self, manual_key):
        """Proceso completo para un idioma"""
        available_langs = self.show_language_selection()
        choice = self.get_user_choice("Idioma", range(0, len(available_langs) + 1))

        if choice == 0:
            return

        target_lang = available_langs[choice - 1]
        print(f"\n🔄 Proceso completo para {get_language_display_name(target_lang)}")

        # Traducir HTML
        try:
            from html_translator import MultiLanguageHTMLTranslator
            translator = MultiLanguageHTMLTranslator(manual_key)
            print("⏳ Iniciando traducción...")
            success, html_output, message = translator.translate_manual(target_lang)

            if success:
                print(f"✅ Traducción HTML completada!")
                print(f"📁 HTML generado en: {html_output}")
            else:
                print(f"❌ Error en traducción: {message}")
                input("\nPresiona Enter para continuar...")
                return
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            input("\nPresiona Enter para continuar...")
            return

        # Generar DOCX automáticamente
        print("\n📄 Generando DOCX automáticamente...")
        self._generate_docx_for_language(manual_key, target_lang)

        input("\nPresiona Enter para continuar...")

    def translate_multiple_languages(self, manual_key):
        """Traduce múltiples idiomas"""
        print("\n🌍 TRADUCCIÓN MÚLTIPLE")

        # Mostrar idiomas disponibles
        available_langs = [lang for lang in LANGUAGES.keys() if lang != 'es']
        print("📝 Idiomas disponibles:")
        for i, lang in enumerate(available_langs, 1):
            print(f"   {i:2}. {get_language_display_name(lang)}")

        print("\n💡 Ejemplo: 1,3,5 o 1-6 o all")
        selection = input("Selecciona idiomas (separados por comas): ").strip()

        if not selection:
            print("❌ Selección cancelada")
            input("Presiona Enter para continuar...")
            return

        # Procesar selección
        selected_langs = []
        if selection.lower() == 'all':
            selected_langs = available_langs
        else:
            try:
                for part in selection.split(','):
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected_langs.extend(available_langs[start-1:end])
                    else:
                        idx = int(part) - 1
                        if 0 <= idx < len(available_langs):
                            selected_langs.append(available_langs[idx])
            except (ValueError, IndexError):
                print("❌ Selección inválida")
                input("Presiona Enter para continuar...")
                return

        if not selected_langs:
            print("❌ No se seleccionaron idiomas válidos")
            input("Presiona Enter para continuar...")
            return

        # Confirmar selección
        print(f"\n📊 Idiomas seleccionados ({len(selected_langs)}):")
        for lang in selected_langs:
            print(f"   • {get_language_display_name(lang)}")

        confirm = input(f"\n¿Proceder con {len(selected_langs)} idiomas? (s/N): ").lower()
        if confirm not in ['s', 'si', 'y', 'yes']:
            print("❌ Operación cancelada")
            input("Presiona Enter para continuar...")
            return

        # Procesar idiomas
        try:
            from html_translator import MultiLanguageHTMLTranslator
            translator = MultiLanguageHTMLTranslator(manual_key)

            successful = 0
            failed = 0

            for i, lang in enumerate(selected_langs, 1):
                print(f"\n🔄 [{i}/{len(selected_langs)}] Traduciendo a {get_language_display_name(lang)}")

                try:
                    result = translator.translate_manual(lang)
                    if result['success']:
                        print(f"✅ {get_language_display_name(lang)} completado")
                        successful += 1
                    else:
                        print(f"❌ {get_language_display_name(lang)} falló: {result.get('message', 'Error desconocido')}")
                        failed += 1
                except Exception as e:
                    print(f"❌ {get_language_display_name(lang)} falló: {e}")
                    failed += 1

            # Resumen final
            print(f"\n📊 RESUMEN:")
            print(f"✅ Exitosos: {successful}")
            print(f"❌ Fallidos: {failed}")

            # Actualizar estado
            self.status.scan_all_manuals()

        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        input("\nPresiona Enter para continuar...")

    def generate_all_docx(self, manual_key):
        """Genera todos los DOCX"""
        print("\n📄 GENERACIÓN MASIVA DE DOCX")

        # Buscar idiomas con HTML disponible
        available_langs = []
        for lang_code in LANGUAGES.keys():
            if lang_code == 'es':
                continue
            status = self.status.status[manual_key].get(lang_code, {})
            if status.get('html', False):
                available_langs.append(lang_code)

        if not available_langs:
            print("❌ No hay idiomas con HTML para generar DOCX")
            input("Presiona Enter para continuar...")
            return

        print(f"📊 Idiomas disponibles: {len(available_langs)}")
        for lang in available_langs:
            print(f"   • {get_language_display_name(lang)}")

        confirm = input(f"\n¿Generar DOCX para los {len(available_langs)} idiomas? (s/N): ").lower()
        if confirm in ['s', 'si']:
            for lang in available_langs:
                print(f"\n📄 Procesando {get_language_display_name(lang)}...")
                self._generate_docx_for_language(manual_key, lang)

        input("\nPresiona Enter para continuar...")

    def complete_process_all(self, manual_key):
        """Proceso completo para todos los idiomas"""
        print("\n🌍 PROCESO COMPLETO PARA TODOS LOS IDIOMAS")

        available_langs = [lang for lang in LANGUAGES.keys() if lang != 'es']
        print(f"⚠️ Esta función traduciría y generaría DOCX para {len(available_langs)} idiomas")
        print("💰 Esto generaría costos muy significativos ($30-50 USD)")

        print(f"\n📊 Idiomas que se procesarían:")
        for lang in available_langs:
            print(f"   • {get_language_display_name(lang)}")

        print("\n⚠️ ADVERTENCIA:")
        print("   • Este proceso puede tardar varias horas")
        print("   • Consumirá muchos tokens de API")
        print("   • Generará archivos HTML y DOCX para todos los idiomas")

        confirm1 = input("\n¿Estás seguro de proceder? (escribe 'CONFIRMAR' para continuar): ")
        if confirm1 != 'CONFIRMAR':
            print("❌ Operación cancelada")
            input("Presiona Enter para continuar...")
            return

        confirm2 = input("¿Realmente deseas procesar TODOS los idiomas? (s/N): ").lower()
        if confirm2 not in ['s', 'si', 'y', 'yes']:
            print("❌ Operación cancelada")
            input("Presiona Enter para continuar...")
            return

        # Procesar todos los idiomas
        try:
            from html_translator import MultiLanguageHTMLTranslator
            from docx_converter import MultiLanguageDocxConverter

            translator = MultiLanguageHTMLTranslator(manual_key)
            converter = MultiLanguageDocxConverter(manual_key)

            successful_translations = 0
            failed_translations = 0
            successful_docx = 0
            failed_docx = 0

            total_langs = len(available_langs)

            for i, lang in enumerate(available_langs, 1):
                print(f"\n{'='*50}")
                print(f"🔄 [{i}/{total_langs}] Procesando {get_language_display_name(lang)}")
                print(f"{'='*50}")

                # Paso 1: Traducir HTML
                print(f"📝 Traduciendo HTML...")
                try:
                    result = translator.translate_manual(lang)
                    if result['success']:
                        print(f"✅ Traducción HTML completada")
                        successful_translations += 1

                        # Paso 2: Generar DOCX
                        print(f"📄 Generando DOCX...")
                        try:
                            success, output_file, message = converter.convert_html_to_docx(lang, force_regenerate=True)
                            if success:
                                print(f"✅ DOCX generado: {output_file}")
                                successful_docx += 1
                            else:
                                print(f"❌ DOCX falló: {message}")
                                failed_docx += 1
                        except Exception as e:
                            print(f"❌ DOCX falló: {e}")
                            failed_docx += 1

                    else:
                        print(f"❌ Traducción falló: {result.get('message', 'Error desconocido')}")
                        failed_translations += 1
                        failed_docx += 1  # No se puede generar DOCX sin HTML

                except Exception as e:
                    print(f"❌ Traducción falló: {e}")
                    failed_translations += 1
                    failed_docx += 1  # No se puede generar DOCX sin HTML

            # Resumen final
            print(f"\n{'='*50}")
            print(f"📊 RESUMEN FINAL")
            print(f"{'='*50}")
            print(f"📝 Traducciones HTML:")
            print(f"   ✅ Exitosas: {successful_translations}")
            print(f"   ❌ Fallidas: {failed_translations}")
            print(f"📄 Generación DOCX:")
            print(f"   ✅ Exitosas: {successful_docx}")
            print(f"   ❌ Fallidas: {failed_docx}")

            if successful_translations == total_langs and successful_docx == total_langs:
                print(f"\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
            elif successful_translations > 0 or successful_docx > 0:
                print(f"\n⚠️ Proceso completado con algunos errores")
            else:
                print(f"\n❌ El proceso falló completamente")

            # Actualizar estado
            self.status.scan_all_manuals()

        except Exception as e:
            print(f"❌ Error inesperado en el proceso: {e}")

        input("\nPresiona Enter para continuar...")

    def show_detailed_status(self):
        """Muestra estado detallado del sistema"""
        print("\n📊 ESTADO DETALLADO DEL SISTEMA")
        print("═" * 50)
        for manual_key in MANUALS.keys():
            self.print_manual_status(manual_key)
        input("Presiona Enter para continuar...")

    def show_configuration(self):
        """Muestra configuración del sistema"""
        print("\n⚙️ CONFIGURACIÓN DEL SISTEMA")
        print("═" * 40)
        print(f"📁 Directorio base: {BASE_DIR}")
        print(f"🗃️ Caché: {'✓ Habilitado' if TRANSLATION_CONFIG['cache_enabled'] else '✗ Deshabilitado'}")
        print(f"💰 Límite de costo: ${TRANSLATION_CONFIG['cost_warning_threshold']}")
        print(f"🔄 Reintentos máximos: {TRANSLATION_CONFIG['max_retries']}")
        input("\nPresiona Enter para continuar...")

    def clear_cache(self):
        """Limpia caché de traducciones"""
        print("\n🧹 LIMPIAR CACHÉ")
        print("┌─────────────────────────────────────────┐")
        print("│ [1] Limpiar solo traducciones corruptas │")
        print("│ [2] ⚠️  ELIMINAR TODO EL CACHÉ ⚠️        │")
        print("│ [0] Cancelar                            │")
        print("└─────────────────────────────────────────┘")

        try:
            choice = int(input("Opción: ").strip())
        except ValueError:
            print("❌ Opción inválida")
            input("\nPresiona Enter para continuar...")
            return

        if choice == 1:
            # Limpiar solo traducciones corruptas
            if CACHE_FILE.exists():
                from html_translator import HTMLTranslator
                translator = HTMLTranslator()
                old_cache = translator.cache.copy()
                translator.cache = translator.load_cache()  # Esto auto-limpia
                cleaned = len(old_cache) - len(translator.cache)
                if cleaned > 0:
                    print(f"✅ Limpiadas {cleaned} traducciones corruptas")
                else:
                    print("ℹ️ No se encontraron traducciones corruptas")
            else:
                print("ℹ️ No hay caché para limpiar")

        elif choice == 2:
            # ELIMINAR TODO EL CACHÉ - SUPER CONFIRMACIÓN
            self._delete_entire_cache_with_super_confirmation()

        elif choice == 0:
            print("❌ Operación cancelada")

        else:
            print("❌ Opción inválida")

        input("\nPresiona Enter para continuar...")

    def show_logs(self):
        """Muestra logs del sistema"""
        print("\n📜 LOGS DEL SISTEMA")
        print("═" * 50)

        if LOGS_DIR.exists():
            # Buscar archivos de log
            log_files = list(LOGS_DIR.glob("*.log"))
            json_files = list(LOGS_DIR.glob("*.json"))

            if log_files or json_files:
                # Mostrar archivos de log más recientes
                all_files = sorted(log_files + json_files, key=lambda x: x.stat().st_mtime, reverse=True)

                print(f"📊 Archivos de log encontrados: {len(all_files)}")
                print("\n🕐 Logs más recientes:")

                for i, log_file in enumerate(all_files[:10], 1):
                    size_kb = log_file.stat().st_size / 1024
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    file_type = "JSON" if log_file.suffix == ".json" else "LOG"
                    print(f"  {i:2d}. [{file_type}] {log_file.name} ({size_kb:.1f}KB) - {mtime.strftime('%Y-%m-%d %H:%M')}")

                # Opciones
                print("\n📋 OPCIONES:")
                print("  [1-10] Ver contenido de un archivo")
                print("  [s] Mostrar estadísticas de resumen")
                print("  [c] Limpiar logs antiguos")
                print("  [Enter] Volver al menú")

                choice = input("\nSelección: ").strip()

                if choice.isdigit():
                    file_num = int(choice)
                    if 1 <= file_num <= len(all_files[:10]):
                        self._show_log_content(all_files[file_num - 1])
                elif choice.lower() == 's':
                    self._show_log_statistics()
                elif choice.lower() == 'c':
                    self._cleanup_old_logs()
            else:
                print("ℹ️ No hay archivos de log disponibles")
                print("   Los logs se generan automáticamente durante las traducciones")
        else:
            print("ℹ️ Directorio de logs no existe")

        input("\nPresiona Enter para continuar...")

    def _show_log_content(self, log_file):
        """Muestra el contenido de un archivo de log"""
        print(f"\n📄 CONTENIDO: {log_file.name}")
        print("─" * 70)

        try:
            if log_file.suffix == ".json":
                # Mostrar resumen JSON
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                print(f"Manual: {data.get('manual', 'N/A')}")
                print(f"Idioma: {data.get('language', 'N/A')}")
                print(f"Inicio: {data.get('start_time', 'N/A')}")
                print(f"Fin: {data.get('end_time', 'N/A')}")
                print(f"Archivos procesados: {data.get('files_processed', 0)}")
                print(f"Cache hits: {data.get('cache_hits', 0)}")
                print(f"API calls: {data.get('api_calls', 0)}")
                print(f"Total elementos: {data.get('total_elements', 0)}")

                if data.get('errors'):
                    print(f"Errores: {len(data['errors'])}")
                    for error in data['errors'][:5]:
                        print(f"  - {error.get('message', 'Sin mensaje')}")
            else:
                # Mostrar últimas líneas del log
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                print(f"Total líneas: {len(lines)}")
                print("\n📝 Últimas 20 líneas:")
                for line in lines[-20:]:
                    print("  " + line.rstrip())

        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")

        input("\nPresiona Enter para continuar...")

    def _show_log_statistics(self):
        """Muestra estadísticas de todos los logs"""
        print("\n📊 ESTADÍSTICAS DE LOGS")
        print("─" * 40)

        json_files = list(LOGS_DIR.glob("summary_*.json"))

        if not json_files:
            print("ℹ️ No hay archivos de estadísticas disponibles")
            return

        total_sessions = len(json_files)
        total_files = 0
        total_cache_hits = 0
        total_api_calls = 0
        languages = set()

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_files += data.get('files_processed', 0)
                    total_cache_hits += data.get('cache_hits', 0)
                    total_api_calls += data.get('api_calls', 0)
                    languages.add(data.get('language', 'unknown'))
            except:
                continue

        total_elements = total_cache_hits + total_api_calls
        cache_ratio = (total_cache_hits / total_elements * 100) if total_elements > 0 else 0

        print(f"Sesiones de traducción: {total_sessions}")
        print(f"Archivos procesados: {total_files}")
        print(f"Elementos traducidos: {total_elements:,}")
        print(f"Cache hits: {total_cache_hits:,} ({cache_ratio:.1f}%)")
        print(f"API calls: {total_api_calls:,} ({100-cache_ratio:.1f}%)")
        print(f"Idiomas procesados: {len(languages)}")
        if languages:
            print(f"  - {', '.join(sorted(languages))}")

    def _cleanup_old_logs(self):
        """Limpia logs antiguos"""
        print("\n🧹 LIMPIAR LOGS ANTIGUOS")
        print("─" * 30)

        all_files = list(LOGS_DIR.glob("*.log")) + list(LOGS_DIR.glob("*.json"))

        if not all_files:
            print("ℹ️ No hay archivos para limpiar")
            return

        # Agrupar por antigüedad
        now = time.time()
        old_files = [f for f in all_files if now - f.stat().st_mtime > 7 * 24 * 3600]  # > 7 días

        print(f"Total archivos: {len(all_files)}")
        print(f"Archivos antiguos (>7 días): {len(old_files)}")

        if old_files:
            total_size = sum(f.stat().st_size for f in old_files) / 1024 / 1024  # MB
            print(f"Espacio a liberar: {total_size:.1f} MB")

            confirm = input(f"\n¿Eliminar {len(old_files)} archivos antiguos? (s/N): ")
            if confirm.lower() == 's':
                deleted = 0
                for f in old_files:
                    try:
                        f.unlink()
                        deleted += 1
                    except:
                        pass

                print(f"✅ Eliminados {deleted} archivos")
            else:
                print("❌ Limpieza cancelada")
        else:
            print("✨ No hay archivos antiguos para eliminar")

    def _generate_docx_for_language(self, manual_key, lang_code):
        """Función auxiliar para generar DOCX de un idioma específico"""
        try:
            from docx_converter import MultiLanguageDocxConverter

            converter = MultiLanguageDocxConverter(manual_key)

            print("⏳ Generando DOCX...")
            # Siempre forzar regeneración cuando se llama desde el menú tras traducir
            success, output_file, message = converter.convert_html_to_docx(lang_code, force_regenerate=True)

            if success:
                print(f"✅ DOCX generado exitosamente!")
                print(f"📁 Archivo: {output_file}")

                # Actualizar estado
                self.status.scan_all_manuals()
            else:
                print(f"❌ Error generando DOCX: {message}")

        except Exception as e:
            print(f"❌ Error inesperado: {e}")

    def _delete_entire_cache_with_super_confirmation(self):
        """Elimina todo el caché con múltiples confirmaciones y avisos de costo"""

        # Verificar si existe el caché
        if not CACHE_FILE.exists():
            print("ℹ️ No hay caché para limpiar")
            return

        # Analizar el caché actual
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            cache_count = len(cache_data)
            cache_size_mb = CACHE_FILE.stat().st_size / (1024 * 1024)

            # Estimar costo (aproximado: $0.01 por traducción)
            estimated_cost = cache_count * 0.01

        except Exception as e:
            print(f"⚠️ Error analizando caché: {e}")
            cache_count = "desconocido"
            cache_size_mb = 0
            estimated_cost = "desconocido"

        # PRIMERA ADVERTENCIA - IMPACTO ECONÓMICO
        print("\n" + "🚨" * 20)
        print("   ⚠️  ADVERTENCIA CRÍTICA - IMPACTO ECONÓMICO ⚠️")
        print("🚨" * 20)
        print(f"📊 Traducciones en caché: {cache_count}")
        print(f"📏 Tamaño del archivo: {cache_size_mb:.1f} MB")
        print(f"💰 Valor estimado del caché: ~${estimated_cost:.2f} USD" if isinstance(estimated_cost, float) else f"💰 Valor estimado: {estimated_cost}")
        print("\n🔥 ELIMINAR EL CACHÉ SIGNIFICA:")
        print("   • Perder TODAS las traducciones guardadas")
        print("   • Tener que re-traducir todo desde cero")
        print("   • Pagar nuevamente los costos de API")
        print("   • Tiempo adicional para regenerar traducciones")

        confirm1 = input(f"\n¿Estás SEGURO de eliminar {cache_count} traducciones? (escribir 'SI' para continuar): ").strip()
        if confirm1 != 'SI':
            print("✅ Operación cancelada - Caché preservado")
            return

        # SEGUNDA CONFIRMACIÓN - MÁS ESPECÍFICA
        print("\n" + "⚠️" * 15)
        print("   SEGUNDA CONFIRMACIÓN REQUERIDA")
        print("⚠️" * 15)
        print("🔍 Esta acción es IRREVERSIBLE")
        print("💸 Necesitarás pagar nuevamente por re-traducir todo")
        print("⏱️ Tomará horas regenerar todas las traducciones")

        confirm2 = input(f"\n¿REALMENTE quieres eliminar el caché de {cache_size_mb:.1f}MB? (escribir 'ELIMINAR' para confirmar): ").strip()
        if confirm2 != 'ELIMINAR':
            print("✅ Operación cancelada - Caché preservado")
            return

        # TERCERA CONFIRMACIÓN - ÚLTIMA OPORTUNIDAD
        print("\n" + "🛑" * 10)
        print("   ÚLTIMA OPORTUNIDAD PARA CANCELAR")
        print("🛑" * 10)
        print("⚡ En 3 segundos se eliminará PERMANENTEMENTE el caché")
        print("⚡ Presiona Ctrl+C AHORA para cancelar")

        try:
            for i in range(3, 0, -1):
                print(f"   Eliminando en {i}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n✅ Operación cancelada por el usuario - Caché preservado")
            return

        # ELIMINACIÓN FINAL
        try:
            CACHE_FILE.unlink()
            print("\n💥 CACHÉ COMPLETAMENTE ELIMINADO")
            print(f"📊 {cache_count} traducciones eliminadas")
            print(f"💰 ~${estimated_cost:.2f} USD en traducciones perdidas" if isinstance(estimated_cost, float) else f"💰 Valor perdido: {estimated_cost}")
            print("⚠️ Necesitarás re-traducir todo desde cero")

        except Exception as e:
            print(f"❌ Error eliminando caché: {e}")

    def webserver_menu(self):
        """Menú simplificado para el webserver"""
        while True:
            print("\n🌐 GESTIÓN DEL WEBSERVER")
            print("═" * 40)

            # Verificar si hay procesos python en puerto 8080
            import subprocess
            try:
                result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
                is_running = ':8080' in result.stdout and 'python' in result.stdout
            except:
                is_running = False

            if is_running:
                print("✅ Estado: ACTIVO")
                print("🌍 URL: http://localhost:8080")
            else:
                print("🔴 Estado: INACTIVO")

            print(f"📁 Directorio: {OUTPUT_DIR}")

            print("\n🔧 OPCIONES:")
            print("┌" + "─" * 38 + "┐")

            if is_running:
                print("│ [1] Abrir en navegador              │")
                print("│ [2] 🔴 Detener webserver            │")
            else:
                print("│ [1] 🟢 Iniciar webserver            │")

            print("│                                     │")
            print("│ [0] Volver al menú principal        │")
            print("└" + "─" * 38 + "┘")
            print()

            max_choice = 3 if is_running else 2
            choice = self.get_user_choice("Selección", range(0, max_choice))

            if choice == 0:
                break
            elif choice == 1:
                if is_running:
                    self._open_webserver_in_browser("http://localhost:8080")
                else:
                    self._start_webserver_simple()
            elif choice == 2 and is_running:
                self._stop_webserver_simple()

    def _start_webserver_simple(self):
        """Inicia el webserver simple"""
        print("\n🚀 INICIAR WEBSERVER")
        print("─" * 20)

        try:
            # Verificar que existe el directorio de salida
            if not OUTPUT_DIR.exists():
                print(f"⚠️ El directorio de salida no existe: {OUTPUT_DIR}")
                print("💡 Traduce al menos un manual antes de usar el webserver")
                input("\nPresiona Enter para continuar...")
                return

            # Ejecutar el servidor simple en background
            import subprocess
            import os

            print("⏳ Iniciando servidor web...")

            # Cambiar al directorio del proyecto
            script_path = os.path.join(os.path.dirname(__file__), 'webserver.py')

            # Ejecutar en background
            process = subprocess.Popen([
                'python3', script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Esperar un momento para que inicie
            import time
            time.sleep(2)

            # Verificar si está corriendo
            if process.poll() is None:
                print("\n🎉 ¡Webserver iniciado exitosamente!")
                print("🌍 URL: http://localhost:8080")
                print("📁 Navegador de archivos disponible")
            else:
                stdout, stderr = process.communicate()
                print("❌ No se pudo iniciar el webserver")
                print(f"Error: {stderr.decode()}")

        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        input("\nPresiona Enter para continuar...")

    def _stop_webserver_simple(self):
        """Detiene el webserver simple"""
        print("\n🛑 DETENER WEBSERVER")
        print("─" * 20)

        confirm = input("¿Estás seguro de detener el servidor web? (s/N): ").lower()
        if confirm not in ['s', 'si', 'y', 'yes']:
            print("❌ Operación cancelada")
            input("\nPresiona Enter para continuar...")
            return

        try:
            import subprocess

            print("⏳ Deteniendo servidor web...")

            # Buscar y matar procesos python que usen puerto 8080
            try:
                result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
                lines = result.stdout.split('\n')

                for line in lines:
                    if ':8080' in line and 'python' in line:
                        # Extraer PID
                        parts = line.split()
                        if len(parts) > 6:
                            pid_info = parts[6]  # formato: PID/process_name
                            if '/' in pid_info:
                                pid = pid_info.split('/')[0]
                                subprocess.run(['kill', pid])
                                print(f"✅ Proceso {pid} terminado")

                print("✅ Webserver detenido exitosamente")

            except Exception as e:
                print(f"⚠️ Error buscando procesos: {e}")
                # Método alternativo
                subprocess.run(['pkill', '-f', 'webserver.py'], stderr=subprocess.DEVNULL)
                print("✅ Intentó detener webserver con pkill")

        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        input("\nPresiona Enter para continuar...")

    def _show_webserver_details(self):
        """Muestra información detallada del webserver"""
        print("\n📊 INFORMACIÓN DETALLADA DEL WEBSERVER")
        print("─" * 45)

        try:
            from webserver import get_webserver_status
            import os

            status = get_webserver_status()

            print(f"🌍 URL: {status['url']}")
            print(f"🖥️ Host: {status['host']}")
            print(f"🔌 Puerto: {status['port']}")
            print(f"📁 Directorio: {status['directory']}")
            print(f"✅ Estado: {'ACTIVO' if status['running'] else 'INACTIVO'}")

            if status['running']:
                print(f"🔗 Enlaces directos:")
                print(f"   • Página principal: {status['url']}/")
                print(f"   • Navegador de archivos: {status['url']}")

            # Información del directorio
            if OUTPUT_DIR.exists():
                total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file()) / (1024*1024)
                file_count = len(list(OUTPUT_DIR.rglob('*.*')))
                lang_dirs = len([d for d in OUTPUT_DIR.iterdir() if d.is_dir()])

                print(f"\n📊 Estadísticas del directorio:")
                print(f"   • Archivos totales: {file_count}")
                print(f"   • Directorios de idiomas: {lang_dirs}")
                print(f"   • Tamaño total: {total_size:.1f} MB")

        except Exception as e:
            print(f"❌ Error obteniendo información: {e}")

        input("\nPresiona Enter para continuar...")

    def _configure_webserver_port(self):
        """Configura el puerto del webserver"""
        print("\n⚙️ CONFIGURAR PUERTO")
        print("─" * 20)

        try:
            current_port = 8080
            print(f"Puerto actual: {current_port}")
            print("Puertos comunes: 8080, 8000, 3000, 5000")

            while True:
                try:
                    new_port = input(f"\nNuevo puerto (Enter para {current_port}): ").strip()

                    if not new_port:
                        new_port = current_port
                        break

                    new_port = int(new_port)

                    if new_port < 1024:
                        print("⚠️ Puertos menores a 1024 requieren permisos de administrador")
                    elif new_port > 65535:
                        print("❌ Puerto inválido (máximo 65535)")
                        continue

                    break

                except ValueError:
                    print("❌ Por favor ingresa un número válido")

            print(f"✅ Puerto configurado: {new_port}")
            print("💡 El puerto se aplicará cuando inicies el webserver")

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPresiona Enter para continuar...")

    def _open_webserver_in_browser(self, url):
        """Abre el webserver en el navegador"""
        try:
            import webbrowser
            print(f"🌍 Abriendo {url} en el navegador...")
            webbrowser.open(url)
            print("✅ Navegador abierto (si está disponible)")
        except Exception as e:
            print(f"⚠️ No se pudo abrir automáticamente el navegador: {e}")
            print(f"🔗 Puedes abrir manualmente: {url}")

        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    try:
        menu = MainMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)