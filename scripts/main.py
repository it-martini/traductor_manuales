"""
Traductor Inteligente Unificado
Combina traductores HTML y DOCX con selector inteligente
"""

import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import FORMATS, MENU_OPTIONS, ensure_directories
from shared.cache_manager import CacheManager


class UnifiedTranslator:
    """Main unified translator with interactive menu"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.project_root = self.base_dir.parent
        self.cache_manager = CacheManager(self.base_dir / 'caches')
        ensure_directories()

    def print_header(self):
        """Print main header"""
        print("🚀 TRADUCTOR INTELIGENTE UNIFICADO")
        print("=" * 50)
        print("Combina HTML + DOCX con caché inteligente")
        print()

    def analyze_all_formats(self) -> dict:
        """Analyze translation status for all formats"""
        print("📊 ANALIZANDO ESTADO DEL PROYECTO...")
        print()

        analysis = {}

        # Analyze HTML
        html_config = FORMATS['html']
        html_files = list(html_config['source_dir'].glob(html_config['file_pattern']))
        html_target_files = list(html_config['target_dir'].glob(html_config['file_pattern']))

        analysis['html'] = {
            'source_files': len(html_files),
            'target_files': len(html_target_files),
            'needs_translation': len(html_files) > len(html_target_files),
            'estimated_elements': len(html_files) * 30,  # Rough estimate
            'estimated_cost': 0.50 if len(html_files) > len(html_target_files) else 0.0
        }

        # Analyze DOCX
        docx_config = FORMATS['docx']
        docx_files = list(docx_config['source_dir'].glob(docx_config['file_pattern']))
        docx_target_files = list(docx_config['target_dir'].glob(docx_config['file_pattern']))

        analysis['docx'] = {
            'source_files': len(docx_files),
            'target_files': len(docx_target_files),
            'needs_translation': len(docx_files) > len(docx_target_files),
            'estimated_elements': 1579 if len(docx_files) > 0 else 0,
            'estimated_cost': 0.40 if len(docx_files) > len(docx_target_files) else 0.0
        }

        return analysis

    def print_status_overview(self, analysis: dict):
        """Print detailed status overview"""
        # HTML Status
        html_status = "🔄 Pendiente" if analysis['html']['needs_translation'] else "✅ Actualizado"
        print(f"📄 HTML: {analysis['html']['source_files']} archivos")
        print(f"   {html_status}")
        if analysis['html']['needs_translation']:
            print(f"   📝 ~{analysis['html']['estimated_elements']} elementos")
            print(f"   💰 Costo estimado: ${analysis['html']['estimated_cost']:.2f}")
        else:
            print(f"   💾 {analysis['html']['target_files']} archivos traducidos")

        print()

        # DOCX Status
        docx_status = "🔄 Pendiente" if analysis['docx']['needs_translation'] else "✅ Actualizado"
        print(f"📋 DOCX: {analysis['docx']['source_files']} archivo")
        print(f"   {docx_status}")
        if analysis['docx']['needs_translation']:
            print(f"   📝 ~{analysis['docx']['estimated_elements']} elementos")
            print(f"   💰 Costo estimado: ${analysis['docx']['estimated_cost']:.2f}")
        else:
            print(f"   💾 {analysis['docx']['target_files']} archivos traducidos")

        print()

        # Total
        total_cost = analysis['html']['estimated_cost'] + analysis['docx']['estimated_cost']
        total_elements = analysis['html']['estimated_elements'] + analysis['docx']['estimated_elements']

        print("🎯 RESUMEN TOTAL:")
        print(f"   💰 Costo total estimado: ${total_cost:.2f}")
        if total_elements > 0:
            print(f"   📝 Elementos por traducir: {total_elements}")
            print(f"   ⏱️  Tiempo estimado: {total_elements / 60:.1f} minutos")
        else:
            print("   🎉 ¡Todo está actualizado!")

        print()

    def show_menu(self):
        """Display interactive menu"""
        print("Selecciona una opción:")
        print()

        for key, option in MENU_OPTIONS.items():
            print(f"[{key}] {option['label']}")
            print(f"    {option['description']}")

        print()

    def handle_format_translation(self, format_type: str):
        """Handle translation for specific format"""
        if format_type == 'html':
            self.translate_html()
        elif format_type == 'docx':
            self.translate_docx()
        elif format_type == 'both':
            self.translate_html()
            self.translate_docx()

    def translate_html(self):
        """Translate HTML format"""
        print("🔄 INICIANDO TRADUCCIÓN HTML")
        print("=" * 40)
        print("⚠️  Ejecutando traductor HTML existente...")
        print("💡 Usar: cd ../translator && python main.py")
        print()

    def translate_docx(self):
        """Translate DOCX format"""
        print("🔄 INICIANDO TRADUCCIÓN DOCX")
        print("=" * 40)
        print("⚠️  Ejecutando traductor DOCX existente...")
        print("💡 Usar: cd ../docx_translator && python main.py")
        print()

    def show_statistics(self):
        """Show detailed statistics"""
        print("📊 ESTADÍSTICAS DETALLADAS")
        print("=" * 40)

        # Cache statistics
        cache_stats = self.cache_manager.get_unified_stats()

        print(f"💾 CACHÉS:")
        print(f"   Total traducciones: {cache_stats['total_translations']}")
        print(f"   Tamaño total: {cache_stats['total_cache_size_mb']:.2f} MB")
        print(f"   Formatos: {cache_stats['formats']}")
        print()

        for format_name, details in cache_stats['cache_details'].items():
            status = "❌ Error" if 'error' in details else "✅ OK"
            print(f"   📄 {format_name.upper()}: {status}")
            print(f"      Traducciones: {details['total_translations']}")
            print(f"      Última actualización: {details['last_updated']}")
            if 'error' in details:
                print(f"      Error: {details['error']}")
        print()

    def show_configuration(self):
        """Show configuration options"""
        print("⚙️  CONFIGURACIÓN")
        print("=" * 40)

        print("📁 DIRECTORIOS:")
        for format_name, config in FORMATS.items():
            print(f"   {format_name.upper()}:")
            print(f"      Origen: {config['source_dir']}")
            print(f"      Destino: {config['target_dir']}")
            print(f"      Caché: {config['cache_file']}")
            print(f"      Habilitado: {'✅' if config['enabled'] else '❌'}")
        print()

        print("🔧 OPCIONES DISPONIBLES:")
        print("   [1] Migrar cachés existentes")
        print("   [2] Limpiar cachés vacíos")
        print("   [0] Volver al menú principal")
        print()

        choice = input("Selecciona opción: ").strip()

        if choice == '1':
            self.migrate_caches()
        elif choice == '2':
            self.cleanup_caches()

    def migrate_caches(self):
        """Migrate existing caches"""
        print("🔄 MIGRANDO CACHÉS EXISTENTES...")

        translator_dir = self.project_root / 'translator'
        docx_translator_dir = self.project_root / 'docx_translator'

        migrated = self.cache_manager.migrate_existing_caches(translator_dir, docx_translator_dir)

        if migrated:
            print("✅ Cachés migrados:")
            for migration in migrated:
                print(f"   📄 {migration['format'].upper()}: {migration['translations']} traducciones")
                print(f"      De: {migration['source']}")
                print(f"      A: {migration['target']}")
        else:
            print("💾 No hay cachés para migrar o ya están migrados")

        print()

    def cleanup_caches(self):
        """Clean up empty caches"""
        print("🧹 LIMPIANDO CACHÉS VACÍOS...")

        cleaned = self.cache_manager.cleanup_empty_caches()

        if cleaned:
            print("✅ Cachés eliminados:")
            for cache_file in cleaned:
                print(f"   🗑️  {cache_file}")
        else:
            print("💾 No hay cachés vacíos para limpiar")

        print()

    def run(self):
        """Main execution loop"""
        try:
            self.print_header()

            # Migrate existing caches if available
            translator_dir = self.project_root / 'translator'
            docx_translator_dir = self.project_root / 'docx_translator'

            if (translator_dir / 'translation_cache.json').exists() or (docx_translator_dir / 'docx_translation_cache.json').exists():
                print("🔄 Migrando cachés existentes...")
                migrated = self.cache_manager.migrate_existing_caches(translator_dir, docx_translator_dir)
                if migrated:
                    print(f"✅ {len(migrated)} cachés migrados exitosamente")
                print()

            # Initial analysis
            analysis = self.analyze_all_formats()
            self.print_status_overview(analysis)

            # Interactive menu loop
            while True:
                self.show_menu()
                choice = input("Opción: ").strip()

                if choice == '0':
                    print("👋 ¡Hasta luego!")
                    break

                elif choice in ['1', '2', '3']:
                    format_type = MENU_OPTIONS[choice]['format']
                    self.handle_format_translation(format_type)

                elif choice == '4':
                    self.show_statistics()

                elif choice == '5':
                    self.show_configuration()

                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
                    print()

        except KeyboardInterrupt:
            print("\n⚠️  Proceso interrumpido por el usuario")
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Entry point"""
    translator = UnifiedTranslator()
    translator.run()


if __name__ == "__main__":
    main()