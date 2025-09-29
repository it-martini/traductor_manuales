#!/usr/bin/env python3
"""
Traductor HTML Multi-idioma
Adaptado del sistema traductor_en para la nueva estructura
"""

import sys
import json
import os
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from collections import deque

# Agregar directorios al path
sys.path.append(str(Path(__file__).parent))

from languages_config import LANGUAGES, get_language_display_name
from system_config import CACHE_FILE, get_manual_path, estimate_translation_cost, load_api_key, get_log_file

class TranslationLogger:
    """Logger para registrar traducciones y progreso en archivos de log"""

    def __init__(self, manual_name, target_lang, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.manual_name = manual_name
        self.target_lang = target_lang
        self.timestamp = timestamp
        self.log_file = get_log_file(f"translation_{manual_name}_{target_lang}", timestamp)
        self.summary_data = {
            'start_time': datetime.now().isoformat(),
            'manual': manual_name,
            'language': target_lang,
            'files_processed': 0,
            'total_elements': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': []
        }

        # Crear archivo de log e inicializar
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_session_start()

    def log_session_start(self):
        """Registrar inicio de sesión de traducción"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SESSION_START: Manual={self.manual_name}, Lang={self.target_lang}\n")

    def log_translation(self, original, translated, source="API", cost=0.0):
        """Registrar una traducción individual"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Truncar textos largos para el log
        orig_short = original[:50] + "..." if len(original) > 50 else original
        trans_short = translated[:50] + "..." if len(translated) > 50 else translated

        # Agregar costo al log si es API call
        cost_str = f" (${cost:.4f})" if source == "API" and cost > 0 else ""

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] TRANSLATE: \"{orig_short}\" -> \"{trans_short}\" [{source}]{cost_str}\n")

        # Actualizar estadísticas
        if source == "CACHE":
            self.summary_data['cache_hits'] += 1
        else:
            self.summary_data['api_calls'] += 1
            # Agregar costo total al resumen
            if 'total_cost' not in self.summary_data:
                self.summary_data['total_cost'] = 0.0
            self.summary_data['total_cost'] += cost

    def log_file_start(self, filename, element_count):
        """Registrar inicio de procesamiento de archivo"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] FILE_START: {filename} ({element_count} elements)\n")

    def log_file_complete(self, filename, cache_hits, api_calls, duration=None, cost=None):
        """Registrar completación de archivo"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duration_str = f", Time:{duration}" if duration else ""
        cost_str = f", Cost:${cost:.4f}" if cost else ""

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] FILE_COMPLETE: {filename} (Cache:{cache_hits}, API:{api_calls}{duration_str}{cost_str})\n")

        self.summary_data['files_processed'] += 1

    def log_progress(self, current_file, total_files, current_elem, total_elems):
        """Registrar progreso general"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_pct = (current_file / total_files) * 100 if total_files > 0 else 0
        elem_pct = (current_elem / total_elems) * 100 if total_elems > 0 else 0

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] PROGRESS: Files:{current_file}/{total_files} ({file_pct:.1f}%), Elements:{current_elem}/{total_elems} ({elem_pct:.1f}%)\n")

    def log_error(self, error_msg, context=""):
        """Registrar error"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] ERROR: {error_msg} | Context: {context}\n")

        self.summary_data['errors'].append({
            'timestamp': timestamp,
            'message': error_msg,
            'context': context
        })

    def finalize_session(self):
        """Finalizar sesión y crear resumen"""
        self.summary_data['end_time'] = datetime.now().isoformat()
        self.summary_data['total_elements'] = self.summary_data['cache_hits'] + self.summary_data['api_calls']

        # Log final
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] SESSION_END: Files:{self.summary_data['files_processed']}, ")
            f.write(f"Cache:{self.summary_data['cache_hits']}, API:{self.summary_data['api_calls']}, ")
            f.write(f"Cost:${self.summary_data.get('total_cost', 0.0):.4f}, ")
            f.write(f"Errors:{len(self.summary_data['errors'])}\n")

        # Crear archivo de resumen JSON
        summary_file = get_log_file(f"summary_{self.manual_name}_{self.target_lang}", self.timestamp)
        summary_file = summary_file.with_suffix('.json')

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.summary_data, f, indent=2, ensure_ascii=False)


class ProgressDisplay:
    """Mostrar progreso avanzado en pantalla durante traducción"""

    def __init__(self, total_files=0, total_elements=0):
        self.total_files = total_files
        self.total_elements = total_elements
        self.current_file = 0
        self.current_element = 0
        self.start_time = time.time()
        self.total_cost = 0.0

    def update_totals(self, total_files, total_elements):
        """Actualizar totales cuando se conocen"""
        self.total_files = total_files
        self.total_elements = total_elements

    def show_file_start(self, filename, file_num, element_count):
        """Mostrar inicio de archivo"""
        self.current_file = file_num
        print(f"\n📄 [{file_num}/{self.total_files}] {filename}")
        print(f"   🔢 {element_count} elementos a procesar")

    def show_element_progress(self, elem_num, total_elems, cache_hits, api_calls, current_text="", translation=""):
        """Mostrar progreso con barra dinámica y traducción ocasional"""
        if total_elems == 0:
            return

        progress = elem_num / total_elems
        bar_length = 20
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        # Calcular velocidad
        elapsed = time.time() - self.start_time
        if elapsed > 0 and elem_num > 0:
            speed = elem_num / elapsed
            eta_seconds = (total_elems - elem_num) / speed if speed > 0 else 0
            eta_str = f"ETA: {int(eta_seconds//60)}:{int(eta_seconds%60):02d}"
        else:
            eta_str = "ETA: --:--"

        # Crear una sola línea que siempre se sobreescribe
        progress_line = f"\r   [{bar}] {elem_num}/{total_elems} | {progress*100:.1f}% | Cache: {cache_hits} | API: {api_calls} | {eta_str}"

        # Si hay traducción nueva, mostrarla primero
        if translation and len(translation.strip()) > 0 and current_text:
            orig_text = (current_text[:40] + "...") if len(current_text) > 40 else current_text
            trans_text = (translation[:40] + "...") if len(translation) > 40 else translation

            # Limpiar línea anterior y mostrar traducción
            print(f"\r{' ' * 100}", end="\r")
            print(f"   🔄 {orig_text} → 🌍 {trans_text}")

        # Siempre mostrar la barra de progreso al final
        print(progress_line, end="", flush=True)

    def show_file_complete(self, cache_hits, api_calls, duration=None, cost=None):
        """Mostrar completación de archivo"""
        duration_str = f" en {duration}" if duration else ""
        cost_str = f", ${cost:.4f}" if cost else ""
        # Acumular costo total
        if cost:
            self.total_cost += cost
        # Nueva línea y mostrar completación
        print(f"\n   ✅ Completado: {cache_hits} cache + {api_calls} API{duration_str}{cost_str}")
        # Actualizar progreso general después de completar archivo
        self.current_file += 1

    def show_overall_progress(self, files_completed=None, total_files=None):
        """Mostrar progreso general con ETA total en línea fija"""
        if files_completed is None:
            files_completed = self.current_file
        if total_files is None:
            total_files = self.total_files

        if total_files > 0:
            overall_progress = (files_completed / total_files)
            bar_length = 30
            filled_length = int(bar_length * overall_progress)
            overall_bar = '█' * filled_length + '░' * (bar_length - filled_length)

            elapsed = time.time() - self.start_time
            elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"

            # Calcular ETA total
            if files_completed > 0 and elapsed > 0:
                avg_time_per_file = elapsed / files_completed
                remaining_files = total_files - files_completed
                eta_seconds = remaining_files * avg_time_per_file
                eta_str = f"ETA: {int(eta_seconds//60)}:{int(eta_seconds%60):02d}"
            else:
                eta_str = "ETA: --:--"

            # Línea fija que se sobreescribe (sin \n para que sea fija)
            cost_str = f" | ${self.total_cost:.4f}" if self.total_cost > 0 else ""
            overall_line = f"\r🌍 Total: [{overall_bar}] {files_completed}/{total_files} archivos ({overall_progress*100:.1f}%) | Tiempo: {elapsed_str} | {eta_str}{cost_str}"
            print(overall_line, end="", flush=True)


class AdaptiveRateLimiter:
    """Rate limiter dinámico que se adapta a la respuesta de la API"""

    def __init__(self, base_delay=1.0, max_delay=30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.request_times = deque(maxlen=100)  # Últimas 100 requests
        self.consecutive_429s = 0
        self.last_request_time = 0

    def should_wait(self):
        """Determina si debe esperar antes del próximo request"""
        now = time.time()

        # Siempre respetar el delay mínimo entre requests
        time_since_last = now - self.last_request_time
        if time_since_last < self.current_delay:
            return self.current_delay - time_since_last

        return 0

    def wait_if_needed(self):
        """Espera el tiempo necesario antes del próximo request"""
        wait_time = self.should_wait()
        if wait_time > 0:
            # Solo mostrar mensaje si es una espera significativa (>2 segundos)
            if wait_time > 2.0:
                print(f"      ⏸️ Rate limiting: esperando {wait_time:.1f}s...")
            time.sleep(wait_time)

    def record_request(self, status_code=200):
        """Registra un request y ajusta el rate limiting según la respuesta"""
        now = time.time()
        self.request_times.append(now)
        self.last_request_time = now

        if status_code == 429:
            # Rate limit hit - incrementar delay agresivamente
            self.consecutive_429s += 1
            self.current_delay = min(
                self.current_delay * (2 ** self.consecutive_429s),
                self.max_delay
            )
            print(f"      ⚠️ Rate limit (429) - delay aumentado a {self.current_delay:.1f}s")

        elif status_code == 200:
            # Request exitoso - reducir delay gradualmente si estaba elevado
            if self.consecutive_429s > 0:
                self.consecutive_429s = max(0, self.consecutive_429s - 1)
                self.current_delay = max(
                    self.base_delay,
                    self.current_delay * 0.8
                )
                if self.current_delay == self.base_delay:
                    print(f"      ✅ Rate limit normalizado a {self.current_delay:.1f}s")

    def get_stats(self):
        """Retorna estadísticas del rate limiting"""
        now = time.time()
        recent_requests = [t for t in self.request_times if now - t < 60]  # Último minuto

        return {
            'current_delay': self.current_delay,
            'consecutive_429s': self.consecutive_429s,
            'requests_last_minute': len(recent_requests),
            'avg_requests_per_minute': len(recent_requests) if recent_requests else 0
        }

def estimate_tokens(text):
    """Estima el número de tokens en un texto (aproximación simple)"""
    if not text:
        return 0
    # Aproximación: ~4 caracteres por token para texto en español/idiomas latinos
    return max(1, len(text) // 4)

def calculate_cost(input_tokens, output_tokens):
    """Calcula el costo usando precios actuales de Claude 3 Haiku (2025)"""
    # Precios por millón de tokens
    INPUT_PRICE = 0.25   # $0.25 per 1M input tokens
    OUTPUT_PRICE = 1.25  # $1.25 per 1M output tokens

    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE

    return input_cost + output_cost

class HTMLTranslator:
    """Traductor de archivos HTML con caché inteligente"""

    def __init__(self, manual_name='open_aula_front'):
        self.manual_name = manual_name
        self.api_key = load_api_key()
        self.cache = self.load_cache()
        self.logger = None
        self.progress = None
        self.session = requests.Session()
        self.rate_limiter = AdaptiveRateLimiter(base_delay=0.5, max_delay=30.0)

        # Validar y limpiar caché automáticamente al inicializar
        self.validate_and_clean_cache()

    def load_cache(self):
        """Carga el caché de traducciones y limpia entradas corruptas"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)

                # Limpiar entradas del caché que contengan texto sucio
                cleaned_cache = {}
                cleaned_count = 0

                for key, value in cache.items():
                    if self._is_dirty_translation(value):
                        cleaned_count += 1
                        # Limpiar la traducción sucia
                        if isinstance(value, dict):
                            # Formato nuevo con metadata
                            cleaned_translation = self._clean_translation_response(value.get('translated', ''))
                            value['translated'] = cleaned_translation
                            cleaned_cache[key] = value
                        else:
                            # Formato antiguo (string)
                            cleaned_value = self._clean_translation_response(value)
                            cleaned_cache[key] = cleaned_value
                    else:
                        cleaned_cache[key] = value

                if cleaned_count > 0:
                    print(f"🧹 Limpiadas {cleaned_count} entradas del caché con texto corrupto")
                    # Guardar caché limpio
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_cache, f, ensure_ascii=False, indent=2)

                return cleaned_cache

            except Exception as e:
                print(f"⚠️ Error cargando caché: {e}")
        return {}

    def save_cache(self):
        """Guarda el caché de traducciones"""
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando caché: {e}")

    def get_cache_key(self, text, target_lang):
        """Genera clave única para el caché"""
        content = f"{text}:{target_lang}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get_file_checksum(self, file_path):
        """Calcula checksum MD5 de un archivo"""
        import hashlib
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️ Error calculando checksum de {file_path}: {e}")
            return None

    def should_retranslate_file(self, source_file, target_file, target_lang):
        """Determina si un archivo necesita retraducirse"""
        if not target_file.exists():
            return True, "Archivo destino no existe"

        # Calcular checksum del archivo fuente
        source_checksum = self.get_file_checksum(source_file)
        if not source_checksum:
            return True, "No se pudo calcular checksum del origen"

        # Buscar metadata del archivo en caché
        file_metadata_key = f"FILE_METADATA:{source_file.name}:{target_lang}"

        if file_metadata_key in self.cache:
            metadata = self.cache[file_metadata_key]
            if isinstance(metadata, dict):
                last_checksum = metadata.get('source_checksum')
                if last_checksum == source_checksum:
                    return False, "Archivo no ha cambiado desde última traducción"
                else:
                    return True, f"Archivo modificado (checksum cambió: {last_checksum[:8]} → {source_checksum[:8]})"

        return True, "Primera traducción del archivo"

    def save_file_metadata(self, source_file, target_file, target_lang):
        """Guarda metadata del archivo traducido"""
        source_checksum = self.get_file_checksum(source_file)
        if source_checksum:
            file_metadata_key = f"FILE_METADATA:{source_file.name}:{target_lang}"
            self.cache[file_metadata_key] = {
                'source_checksum': source_checksum,
                'target_file': str(target_file),
                'translated_at': time.time(),
                'source_size': source_file.stat().st_size,
                'target_size': target_file.stat().st_size if target_file.exists() else 0
            }

    def validate_cache(self):
        """Valida la integridad del caché y retorna estadísticas"""
        stats = {
            'total_entries': len(self.cache),
            'translation_entries': 0,
            'file_metadata_entries': 0,
            'languages': set(),
            'corrupted_entries': [],
            'oldest_entry': None,
            'newest_entry': None,
            'total_usage': 0
        }

        current_time = time.time()

        for key, value in self.cache.items():
            try:
                if key.startswith('FILE_METADATA:'):
                    stats['file_metadata_entries'] += 1
                    if isinstance(value, dict) and 'translated_at' in value:
                        timestamp = value['translated_at']
                        if stats['oldest_entry'] is None or timestamp < stats['oldest_entry']:
                            stats['oldest_entry'] = timestamp
                        if stats['newest_entry'] is None or timestamp > stats['newest_entry']:
                            stats['newest_entry'] = timestamp
                else:
                    stats['translation_entries'] += 1
                    # Extraer idioma de la clave MD5 buscando en todas las traducciones
                    if isinstance(value, dict):
                        if 'timestamp' in value:
                            timestamp = value['timestamp']
                            if stats['oldest_entry'] is None or timestamp < stats['oldest_entry']:
                                stats['oldest_entry'] = timestamp
                            if stats['newest_entry'] is None or timestamp > stats['newest_entry']:
                                stats['newest_entry'] = timestamp

                        usage_count = value.get('usage_count', 1)
                        stats['total_usage'] += usage_count

                        # Intentar detectar idioma por patrones comunes
                        translated_text = value.get('translated', '')
                        if any(word in translated_text.lower() for word in ['the', 'and', 'or', 'to', 'of']):
                            stats['languages'].add('en')
                        elif any(word in translated_text.lower() for word in ['di', 'della', 'con', 'per', 'una']):
                            stats['languages'].add('it')
                        elif any(word in translated_text.lower() for word in ['et', 'de', 'le', 'pour', 'avec']):
                            stats['languages'].add('fr')

            except Exception as e:
                stats['corrupted_entries'].append(f"{key}: {str(e)}")

        return stats

    def print_cache_report(self):
        """Imprime un reporte completo del estado del caché"""
        stats = self.validate_cache()

        print("📊 REPORTE DEL CACHÉ")
        print("=" * 50)
        print(f"📝 Total entradas: {stats['total_entries']}")
        print(f"🔤 Traducciones: {stats['translation_entries']}")
        print(f"📄 Metadata archivos: {stats['file_metadata_entries']}")
        print(f"🌍 Idiomas detectados: {', '.join(stats['languages']) or 'Ninguno detectado'}")
        print(f"🔄 Uso total: {stats['total_usage']} reutilizaciones")

        if stats['oldest_entry']:
            oldest_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(stats['oldest_entry']))
            print(f"📅 Entrada más antigua: {oldest_date}")

        if stats['newest_entry']:
            newest_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(stats['newest_entry']))
            print(f"📅 Entrada más reciente: {newest_date}")

        if stats['corrupted_entries']:
            print(f"\n⚠️ Entradas corruptas encontradas: {len(stats['corrupted_entries'])}")
            for corrupt in stats['corrupted_entries'][:3]:  # Mostrar solo las primeras 3
                print(f"   - {corrupt}")
            if len(stats['corrupted_entries']) > 3:
                print(f"   ... y {len(stats['corrupted_entries']) - 3} más")
        else:
            print("✅ No se encontraron entradas corruptas")

        # Análisis de eficiencia
        if stats['translation_entries'] > 0:
            avg_usage = stats['total_usage'] / stats['translation_entries']
            print(f"\n📈 Eficiencia promedio: {avg_usage:.1f} reutilizaciones por traducción")

            if avg_usage < 1.5:
                print("⚠️ Baja reutilización del caché (< 1.5x)")
            elif avg_usage > 3.0:
                print("🎯 Excelente reutilización del caché (> 3.0x)")
            else:
                print("✅ Reutilización normal del caché")

    def cleanup_cache(self, max_age_days=30, min_usage=1):
        """Limpia entradas antiguas o poco usadas del caché"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        keys_to_remove = []

        for key, value in self.cache.items():
            should_remove = False

            if isinstance(value, dict):
                # Verificar edad
                timestamp = value.get('timestamp', current_time)
                age = current_time - timestamp

                if age > max_age_seconds:
                    should_remove = True
                    reason = f"Antiguo ({age/86400:.1f} días)"

                # Verificar uso mínimo
                usage_count = value.get('usage_count', 1)
                if usage_count < min_usage and age > 86400:  # Al menos 1 día de antigüedad
                    should_remove = True
                    reason = f"Poco usado ({usage_count}x)"

                if should_remove:
                    keys_to_remove.append((key, reason))

        # Remover entradas
        removed_count = len(keys_to_remove)
        for key, reason in keys_to_remove:
            del self.cache[key]

        if removed_count > 0:
            self.save_cache()
            print(f"🧹 Cache limpiado: {removed_count} entradas removidas")
            for key, reason in keys_to_remove[:5]:  # Mostrar solo las primeras 5
                print(f"   - {key[:20]}...: {reason}")
            if removed_count > 5:
                print(f"   ... y {removed_count - 5} más")
        else:
            print("✨ Cache ya está limpio")

        return removed_count

    def fix_html_attributes(self, soup, target_lang):
        """Corrige atributos HTML específicos del idioma"""
        # Usar los idiomas configurados en languages_config.py
        # Los códigos coinciden exactamente con LANGUAGES
        supported_langs = {
            'es': 'es',      # Español (original)
            'en': 'en',      # Inglés
            'pt': 'pt',      # Portugués
            'fr': 'fr',      # Francés
            'it': 'it',      # Italiano
            'de': 'de',      # Alemán
            'nl': 'nl',      # Neerlandés (Holandés)
            'ca': 'ca',      # Catalán
            'eu': 'eu',      # Euskera (Vasco)
            'gl': 'gl',      # Gallego
            'da': 'da',      # Danés
            'sv': 'sv',      # Sueco
            'gn': 'gn',      # Guaraní
        }

        # Corregir atributo lang en tag html
        html_tag = soup.find('html')
        if html_tag and 'lang' in html_tag.attrs:
            target_lang_code = supported_langs.get(target_lang, target_lang)
            html_tag['lang'] = target_lang_code

        # Remover texto "html" suelto al inicio si existe
        for element in soup.contents:
            if isinstance(element, str) and element.strip() == '"html"':
                element.extract()

        # Corregir enlaces PDF para que apunten al idioma correcto
        self.fix_pdf_links(soup, target_lang)

    def fix_pdf_links(self, soup, target_lang):
        """Corrige enlaces PDF para que apunten al archivo del idioma correcto"""
        import re

        # Determinar el tipo de manual basado en el directorio
        # Esto se puede determinar desde el self.manual_name si está disponible
        manual_type = getattr(self, 'manual_name', 'front')

        if 'front' in manual_type:
            manual_suffix = 'front'
        elif 'back' in manual_type:
            manual_suffix = 'back'
        else:
            manual_suffix = 'front'  # default

        # Patrón para identificar enlaces PDF españoles
        spanish_pdf_pattern = f'manual_aula_{manual_suffix}_es\\.pdf'
        replacement_pdf = f'manual_aula_{manual_suffix}_{target_lang}.pdf'

        # Corregir meta refresh
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh and 'content' in meta_refresh.attrs:
            content = meta_refresh['content']
            if re.search(spanish_pdf_pattern, content):
                new_content = re.sub(spanish_pdf_pattern, replacement_pdf, content)
                meta_refresh['content'] = new_content
                print(f"   🔗 Corregido meta refresh: {replacement_pdf}")

        # Corregir enlaces directos <a href="...">
        pdf_links = soup.find_all('a', href=re.compile(spanish_pdf_pattern))
        for link in pdf_links:
            old_href = link['href']
            new_href = re.sub(spanish_pdf_pattern, replacement_pdf, old_href)
            link['href'] = new_href
            print(f"   🔗 Corregido enlace PDF: {new_href}")

        # También corregir cualquier referencia en JavaScript o texto inline si existe
        for script in soup.find_all('script'):
            if script.string and re.search(spanish_pdf_pattern, script.string):
                script.string = re.sub(spanish_pdf_pattern, replacement_pdf, script.string)

    def fix_pdf_links_in_json(self, json_data, target_lang):
        """Corrige enlaces PDF en datos JSON como _toc.json"""
        import re

        # Determinar el tipo de manual basado en self.manual_name
        manual_type = getattr(self, 'manual_name', 'front')

        if 'front' in manual_type:
            manual_suffix = 'front'
        elif 'back' in manual_type:
            manual_suffix = 'back'
        else:
            manual_suffix = 'front'  # default

        # Patrón para identificar enlaces PDF españoles
        spanish_pdf_pattern = f'manual_aula_{manual_suffix}_es\\.pdf'
        replacement_pdf = f'manual_aula_{manual_suffix}_{target_lang}.pdf'

        pdf_links_fixed = 0

        # Procesar cada elemento del array JSON
        for item in json_data:
            if isinstance(item, dict) and 'a_attr' in item:
                if isinstance(item['a_attr'], dict) and 'href' in item['a_attr']:
                    href = item['a_attr']['href']
                    if re.search(spanish_pdf_pattern, href):
                        new_href = re.sub(spanish_pdf_pattern, replacement_pdf, href)
                        item['a_attr']['href'] = new_href
                        pdf_links_fixed += 1
                        print(f"      🔗 JSON PDF corregido: {new_href}")

        if pdf_links_fixed > 0:
            print(f"      ✅ {pdf_links_fixed} enlaces PDF corregidos en JSON")

    def protect_email_addresses(self, text):
        """Protege direcciones de email reemplazándolas con marcadores únicos"""
        import re

        # Patrón para detectar emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        emails_found = []
        def replace_email(match):
            email = match.group(0)
            placeholder = f"__EMAIL_PLACEHOLDER_{len(emails_found)}__"
            emails_found.append(email)
            return placeholder

        protected_text = re.sub(email_pattern, replace_email, text)
        return protected_text, emails_found

    def restore_email_addresses(self, text, emails_list):
        """Restaura las direcciones de email protegidas"""
        for i, email in enumerate(emails_list):
            placeholder = f"__EMAIL_PLACEHOLDER_{i}__"
            text = text.replace(placeholder, email)
        return text

    def translate_with_claude(self, text, target_lang, context="", element_type="text", max_retries=3):
        """Traduce texto usando Claude API con reintentos robustos"""

        # Proteger direcciones de email antes de cualquier procesamiento
        protected_text, emails_found = self.protect_email_addresses(text)

        # Usar texto protegido para caché y traducción
        cache_key = self.get_cache_key(protected_text, target_lang)

        # Verificar caché (puede tener formato antiguo o nuevo)
        if cache_key in self.cache:
            cached_value = self.cache[cache_key]
            # Si es formato nuevo con metadata, extraer la traducción
            if isinstance(cached_value, dict) and 'translated' in cached_value:
                # Actualizar contador de uso
                cached_value['usage_count'] = cached_value.get('usage_count', 0) + 1
                translated = cached_value['translated']
            else:
                translated = cached_value  # Formato antiguo

            # Restaurar emails en traducción del caché
            translated = self.restore_email_addresses(translated, emails_found)

            # Log cache hit
            if self.logger:
                self.logger.log_translation(text, translated, "CACHE")

            return translated, 0.0  # Cost 0 para traducciones desde caché

        if not self.api_key:
            raise ValueError("No se encontró API key de Claude")

        # Preparar prompt en español (funciona mejor con Claude)
        lang_info = LANGUAGES.get(target_lang, {})
        target_lang_name = lang_info.get('claude_code', target_lang)

        # Importar funciones de particularidades idiomáticas
        from languages_config import get_translation_instructions
        cultural_instructions = get_translation_instructions(target_lang, self.manual_name)

        prompt = f"""IMPORTANTE: Responde ÚNICAMENTE con el texto traducido directo. NO incluyas explicaciones, traducciones adicionales, o formato instructivo.

Traduce este texto del español al {target_lang_name}:
"{protected_text}"

Reglas críticas:
1. Respuesta DIRECTA: solo el texto traducido
2. NO escribas "Traducción al...", "Translation to...", "Tradução em..." ni similares
3. NO incluyas el texto original
4. NO agregues explicaciones o ejemplos
5. Mantén significado exacto y tono profesional
6. Preserva tags HTML tal como están
7. NO traduzcas nombres propios, URLs o códigos técnicos
8. PRESERVA EXACTAMENTE cualquier __EMAIL_PLACEHOLDER_X__ tal como aparece

{cultural_instructions}

Traducción directa:"""

        # Implementar reintentos con backoff exponencial
        for attempt in range(max_retries + 1):
            try:
                # Aplicar rate limiting adaptivo antes de cada request
                if attempt == 0:
                    # Primer intento - usar rate limiting normal
                    self.rate_limiter.wait_if_needed()
                else:
                    # Reintentos - usar backoff exponencial del reintento
                    wait_time = 2 ** attempt  # Backoff exponencial: 2s, 4s, 8s
                    print(f"🔄 Reintento {attempt}/{max_retries} en {wait_time}s...")
                    time.sleep(wait_time)

                # Llamada a Claude API
                response = self.session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",  # Modelo más económico
                        "max_tokens": 4000,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    # Registrar request exitoso en rate limiter
                    self.rate_limiter.record_request(200)

                    result = response.json()
                    translated_text = result['content'][0]['text'].strip()

                    # Calcular costo real de la traducción
                    usage = result.get('usage', {})
                    input_tokens = usage.get('input_tokens', estimate_tokens(prompt))
                    output_tokens = usage.get('output_tokens', estimate_tokens(translated_text))
                    cost = calculate_cost(input_tokens, output_tokens)

                    # Limpiar la respuesta - remover instrucciones técnicas
                    translated_text = self._clean_translation_response(translated_text)

                    # Restaurar direcciones de email en la traducción
                    translated_text = self.restore_email_addresses(translated_text, emails_found)

                    # Validar que la traducción no esté corrupta
                    self._validate_translation(text, translated_text, target_lang)

                    # Guardar en caché con metadata incluyendo costo
                    self.cache[cache_key] = {
                        'original': text,
                        'translated': translated_text,
                        'element_type': element_type,
                        'timestamp': time.time(),
                        'usage_count': 1,
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens,
                        'cost': cost
                    }

                    # Log API call con costo
                    if self.logger:
                        self.logger.log_translation(text, translated_text, "API", cost)

                    # Mostrar ejemplo de traducción (verbose)
                    self._show_translation_example(text, translated_text, target_lang)

                    return translated_text, cost

                # Errores que justifican reintentos
                elif response.status_code in [429, 500, 502, 503, 504]:
                    # Registrar error en rate limiter
                    self.rate_limiter.record_request(response.status_code)

                    error_msg = f"Error API Claude {response.status_code}: {response.text[:200]}"

                    if attempt < max_retries:
                        print(f"⚠️ {error_msg} - Reintentando...")
                        continue
                    else:
                        print(f"❌ {error_msg} - Máximo de reintentos alcanzado")
                        raise Exception(error_msg)

                # Errores que NO justifican reintentos (401, 403, 400, etc.)
                else:
                    error_msg = f"Error API Claude {response.status_code}: {response.text[:200]}"
                    print(f"❌ {error_msg} - Error no recoverable")
                    raise Exception(error_msg)

            except requests.exceptions.HTTPError as e:
                # Manejar errores HTTP específicos
                status_code = e.response.status_code if e.response else 0

                if status_code == 401:
                    error_msg = "🔐 API Key inválida o expirada. Verifica tu configuración en .env"
                    print(f"❌ {error_msg}")
                    if self.logger:
                        self.logger.log_error(f"AUTH_ERROR: {error_msg}")
                    raise Exception(error_msg)

                elif status_code == 429:
                    error_msg = "⏳ Rate limit excedido. Claude está limitando las requests"
                    if attempt < max_retries:
                        wait_time = min(60 * attempt, 300)  # Max 5 minutos
                        print(f"⚠️ {error_msg} - Esperando {wait_time}s antes de reintentar...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ {error_msg} - Máximo de reintentos alcanzado")
                        if self.logger:
                            self.logger.log_error(f"RATE_LIMIT: {error_msg}")
                        raise Exception(error_msg)

                elif status_code in [402, 403]:
                    error_msg = "💳 Crédito API agotado o acceso denegado. Verifica tu cuenta de Claude"
                    print(f"❌ {error_msg}")
                    if self.logger:
                        self.logger.log_error(f"CREDIT_ERROR: Status {status_code} - {error_msg}")
                    raise Exception(error_msg)

                else:
                    error_msg = f"Error HTTP {status_code}: {str(e)}"
                    if attempt < max_retries:
                        print(f"⚠️ {error_msg} - Reintentando...")
                        continue
                    else:
                        print(f"❌ {error_msg} - Máximo de reintentos alcanzado")
                        raise Exception(error_msg)

            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                error_msg = f"Error de conexión: {str(e)}"

                if attempt < max_retries:
                    print(f"⚠️ {error_msg} - Reintentando...")
                    continue
                else:
                    print(f"❌ {error_msg} - Máximo de reintentos alcanzado")
                    raise Exception(error_msg)

            except Exception as e:
                # Para otros errores (JSON parsing, etc.) no reintentar
                print(f"❌ Error no recoverable: {e}")
                raise

    def _validate_translation(self, original, translated, target_lang):
        """Valida que la traducción no esté corrupta con explicaciones o instrucciones"""
        import re

        # Patrones de traducciones corruptas detectados
        corruption_patterns = [
            r'Tradução em \w+:',           # "Tradução em galego:"
            r'Traducción al \w+:',         # "Traducción al Catalan:"
            r'Translation to \w+:',        # "Translation to English:"
            r'Traduction en \w+:',         # "Traduction en français:"
            r'Traduzione in \w+:',         # "Traduzione in italiano:"
            r'Übersetzung ins \w+:',       # "Übersetzung ins Deutsche:"
            r'"[^"]*"\s*\n\s*\n\s*\w+.*:', # Patrón general: "texto"\n\nIdioma:
            r'^".*"\s*\n.*:.*".*"$',       # Formato explicativo con comillas
        ]

        for pattern in corruption_patterns:
            if re.search(pattern, translated, re.MULTILINE | re.IGNORECASE):
                error_msg = f"❌ TRADUCCIÓN CORRUPTA detectada para '{target_lang}': contiene explicaciones en lugar de traducción pura"
                print(f"{error_msg}")
                print(f"Original: {original[:100]}...")
                print(f"Corrupta: {translated[:200]}...")
                # Rechazar traducción corrupta - forzar reintento
                raise Exception(f"Traducción corrupta detectada - patrón: {pattern}")

        return True

    def validate_and_clean_cache(self):
        """Valida el caché y limpia traducciones corruptas automáticamente"""
        import re

        if not self.cache:
            return

        corruption_patterns = [
            r'Tradução em \w+:',
            r'Traducción al \w+:',
            r'Translation to \w+:',
            r'Traduction en \w+:',
            r'Traduzione in \w+:',
            r'Übersetzung ins \w+:',
            r'"[^"]*"\s*\n\s*\n\s*\w+.*:',
            r'^".*"\s*\n.*:.*".*"$',
        ]

        keys_to_remove = []
        for key, translation in self.cache.items():
            if isinstance(translation, dict):
                translated_text = translation.get('translated', '')
            else:
                translated_text = str(translation)

            for pattern in corruption_patterns:
                if re.search(pattern, translated_text, re.MULTILINE | re.IGNORECASE):
                    keys_to_remove.append(key)
                    break

        if keys_to_remove:
            print(f"🧹 Limpiando {len(keys_to_remove)} traducciones corruptas del caché...")
            for key in keys_to_remove:
                del self.cache[key]
            self.save_cache()
            print("✅ Caché limpiado automáticamente")

    def _clean_translation_response(self, response):
        """Limpia la respuesta de Claude removiendo instrucciones técnicas y HTML extra"""
        import re

        cleaned = response.strip()

        # 1. Detectar y extraer solo la parte traducida si Claude devuelve HTML completo
        if cleaned.startswith(('<!DOCTYPE', '<html', '&lt;html')):
            print("⚠️ Claude devolvió HTML completo, extrayendo solo texto traducido...")
            # Si empieza con HTML, Claude se confundió - rechazar completamente
            print(f"❌ Respuesta inválida: {cleaned[:100]}...")
            raise Exception("Claude devolvió HTML completo en lugar de texto traducido")

        # 2. Remover tags HTML sueltos que no deberían estar
        html_patterns = [
            r'</?html[^>]*>',
            r'</?head[^>]*>',
            r'</?body[^>]*>',
            r'</?title[^>]*>',
            r'<!DOCTYPE[^>]*>',
        ]

        for pattern in html_patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                print(f"⚠️ Removiendo HTML extra: {pattern}")
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 3. Remover prefijos explicativos
        prefixes_to_remove = [
            r"^(?:Here's the|This is the|The) translation.*?:\s*",
            r"^(?:Aquí está la|Esta es la) traducción.*?:\s*",
            r"^Traducción:\s*",
            r"^Translation:\s*",
            r"^Ecco la traduzione.*?:\s*",
            r"^La traduzione.*?:\s*",
        ]

        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

        # 4. Limpiar espacios múltiples y saltos de línea extra
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)

        result = cleaned.strip()

        # 5. Remover comillas dobles innecesarias (problema común de Claude)
        # Claude a veces agrega comillas dobles cuando no debería
        if result.startswith('"') and result.endswith('"') and result.count('"') == 2:
            # Solo mostrar este mensaje ocasionalmente para debug, no siempre
            result = result[1:-1]

        # 6. Validación final - asegurar que no quedó HTML estructural
        if any(tag in result.lower() for tag in ['<html', '<head', '<body', '<!doctype']):
            print(f"❌ CRÍTICO: HTML estructural detectado en resultado final")
            print(f"Respuesta problemática: {result[:200]}...")
            raise Exception("Respuesta contiene HTML estructural después de limpieza")

        return result

    def translate_json_file(self, source_file, target_file, target_lang, force_retranslate=False):
        """Traduce archivos JSON como _toc.json y _keywords.json"""
        try:
            # Verificar si necesita retraducirse (a menos que sea forzado)
            if not force_retranslate:
                should_retranslate, reason = self.should_retranslate_file(source_file, target_file, target_lang)
                if not should_retranslate:
                    print(f"      ⏭️ Omitiendo JSON {source_file.name}: {reason}")
                    return True
                else:
                    print(f"      🔄 Traduciendo JSON {source_file.name}: {reason}")
            else:
                print(f"      📄 Traduciendo JSON: {source_file.name}")

            # Leer archivo JSON
            with open(source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"      ⚠️ Formato JSON no esperado en {source_file.name}")
                return False

            translated_count = 0
            cache_hits = 0

            # Traducir cada entrada del array
            for item in data:
                if isinstance(item, dict) and 'text' in item:
                    original_text = item['text']

                    # Solo traducir si no está vacío y no es técnico
                    if original_text and not self._is_technical_text(original_text):
                        cache_key = self.get_cache_key(original_text, target_lang)

                        if cache_key in self.cache:
                            # Usar cache
                            cached_value = self.cache[cache_key]
                            if isinstance(cached_value, dict) and 'translated' in cached_value:
                                translated_text = cached_value['translated']
                                cached_value['usage_count'] = cached_value.get('usage_count', 0) + 1
                            else:
                                translated_text = cached_value
                            cache_hits += 1
                            print(f"      ⚡ JSON Cache: '{original_text}' → '{translated_text}'")
                        else:
                            # Traducir con API
                            translated_text = self.translate_with_claude(
                                original_text, target_lang, element_type="json_text"
                            )
                            translated_count += 1
                            print(f"      🔄 JSON: '{original_text}' → '{translated_text}'")

                        # Aplicar traducción
                        item['text'] = translated_text

            # Corregir enlaces PDF en el JSON después de traducir
            self.fix_pdf_links_in_json(data, target_lang)

            # Guardar archivo JSON traducido
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

            print(f"      ✅ JSON traducido: {translated_count} nuevos, {cache_hits} del cache")

            # Guardar metadata del archivo JSON traducido
            self.save_file_metadata(source_file, target_file, target_lang)

            # Guardar caché después de traducir JSON
            if translated_count > 0:
                self.save_cache()
                print(f"      💾 Caché guardado con {len(self.cache)} entradas")

            return True

        except Exception as e:
            print(f"      ❌ Error traduciendo JSON {source_file.name}: {e}")
            return False

    def _is_technical_text(self, text):
        """Detecta si un texto es técnico y no debe traducirse"""
        technical_indicators = [
            '#',  # IDs técnicos
            'href=',  # URLs
            '.html',  # Enlaces
            '.pdf',   # Archivos
            '/',      # Rutas
            'icon-',  # Clases CSS
        ]

        # Si es muy corto o contiene indicadores técnicos, no traducir
        if len(text.strip()) < 2:
            return True

        for indicator in technical_indicators:
            if indicator in text:
                return True

        return False

    def _is_dirty_translation(self, text):
        """Detecta si una traducción contiene texto corrupto"""
        # Con el nuevo prompt en español, deberíamos tener menos texto corrupto
        # Pero mantenemos la detección básica

        # Si es dict con metadata, revisar el campo translated
        if isinstance(text, dict):
            text = text.get('translated', '')

        dirty_indicators = [
            'Here\'s the translation',
            'Aquí está la traducción',
            'RULES: Preserve',
            'Traduce el siguiente',
            'Responde SOLO con',
        ]

        for indicator in dirty_indicators:
            if indicator in text:
                return True
        return False

    def _show_translation_example(self, original, translated, target_lang, show_always=False):
        """Muestra un ejemplo de la traducción en tiempo real"""
        from bs4 import BeautifulSoup

        # Solo mostrar ocasionalmente para reducir spam (excepto si show_always=True)
        if not show_always and hasattr(self, '_translation_count'):
            self._translation_count += 1
            if self._translation_count % 10 != 0:  # Solo cada 10 traducciones
                return
        else:
            if not hasattr(self, '_translation_count'):
                self._translation_count = 1

        # Extraer texto plano para mostrar ejemplos
        try:
            # Si es HTML, extraer texto
            if '<' in original and '>' in original:
                soup_orig = BeautifulSoup(original, 'html.parser')
                text_orig = soup_orig.get_text().strip()

                soup_trans = BeautifulSoup(translated, 'html.parser')
                text_trans = soup_trans.get_text().strip()
            else:
                text_orig = original.strip()
                text_trans = translated.strip()

            # Mostrar solo si hay texto significativo
            if len(text_orig) > 10 and len(text_trans) > 10:
                # Truncar si es muy largo
                max_len = 60
                if len(text_orig) > max_len:
                    text_orig = text_orig[:max_len] + "..."
                if len(text_trans) > max_len:
                    text_trans = text_trans[:max_len] + "..."

                # Deshabilitar por ahora para limpiar salida - se registra en logs
                # lang_flag = LANGUAGES.get(target_lang, {}).get('emoji', '🌍')
                # print(f"      🔄 ES: {text_orig}")
                # print(f"      {lang_flag} {target_lang.upper()}: {text_trans}")

        except Exception:
            # Si hay error, no mostrar nada para no interrumpir el proceso
            pass

    def extract_translatable_elements(self, soup):
        """Extrae elementos traducibles del HTML"""
        from bs4 import Comment
        elements = []

        # Elementos de texto directo
        for tag in soup.find_all(text=True):
            # Excluir scripts, styles y comentarios HTML
            if tag.parent.name in ['script', 'style']:
                continue
            # Excluir comentarios HTML (esto es lo que causaba el problema)
            if isinstance(tag, Comment):
                continue
            text = tag.strip()
            if text and len(text) > 2:
                elements.append({
                    'type': 'text',
                    'element': tag,
                    'text': text
                })

        # Atributos traducibles (alt, title)
        for tag in soup.find_all():
            if tag.get('alt'):
                elements.append({
                    'type': 'alt',
                    'element': tag,
                    'text': tag['alt']
                })
            if tag.get('title'):
                elements.append({
                    'type': 'title',
                    'element': tag,
                    'text': tag['title']
                })

        return elements

    def analyze_html_structure(self, file_path):
        """Analiza la estructura de un archivo HTML y retorna estadísticas"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # Contar elementos traducibles
            translatable_elements = self.extract_translatable_elements(soup)

            # Calcular estadísticas
            total_chars = sum(len(elem['text']) for elem in translatable_elements)

            # Contar diferentes tipos de elementos
            text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'li', 'td', 'th', 'label', 'title'])
            text_elements_with_content = [elem for elem in text_elements if elem.get_text(strip=True)]

            # Contar links e imágenes
            links = soup.find_all('a', href=True)
            images = soup.find_all('img')

            # Estimar complejidad
            complexity_score = len(translatable_elements) + (total_chars / 100)

            analysis = {
                'file_path': file_path,
                'file_size_bytes': len(content),
                'translatable_elements_count': len(translatable_elements),
                'text_elements_count': len(text_elements_with_content),
                'total_chars': total_chars,
                'links_count': len(links),
                'images_count': len(images),
                'complexity_score': complexity_score,
                'estimated_requests': max(1, total_chars // 3000),  # ~3K chars por request
                'estimated_time_minutes': max(1, len(translatable_elements) * 1.5 / 60)  # 1.5s por elemento
            }

            return analysis

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'file_size_bytes': 0,
                'translatable_elements_count': 0,
                'text_elements_count': 0,
                'total_chars': 0,
                'links_count': 0,
                'images_count': 0,
                'complexity_score': 0,
                'estimated_requests': 0,
                'estimated_time_minutes': 0
            }

    def translate_html_file(self, source_file, target_file, target_lang, force_retranslate=False, file_num=0):
        """Traduce un archivo HTML específico"""
        start_time = time.time()
        cache_hits = 0
        api_calls = 0

        try:
            # Verificar si necesita retraducirse (a menos que sea forzado)
            if not force_retranslate:
                should_retranslate, reason = self.should_retranslate_file(source_file, target_file, target_lang)
                if not should_retranslate:
                    if self.progress:
                        print(f"\n📄 [{file_num}/{self.progress.total_files}] {source_file.name}")
                        print(f"   ⏭️ Omitiendo: {reason}")
                    else:
                        print(f"      ⏭️ Omitiendo {source_file.name}: {reason}")
                    return True

            # Leer archivo original
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # Extraer elementos traducibles
            elements = self.extract_translatable_elements(soup)

            # Log y progreso de inicio de archivo
            if self.logger:
                self.logger.log_file_start(source_file.name, len(elements))

            if self.progress:
                self.progress.show_file_start(source_file.name, file_num, len(elements))
            else:
                print(f"      📝 {len(elements)} elementos a traducir", end="", flush=True)

            # Traducir elementos
            translated_count = 0
            cache_hits = 0
            total_cost = 0.0

            for i, element in enumerate(elements, 1):
                cache_key = self.get_cache_key(element['text'], target_lang)

                if cache_key in self.cache:
                    cached_value = self.cache[cache_key]
                    # Manejar formato antiguo y nuevo del caché
                    if isinstance(cached_value, dict) and 'translated' in cached_value:
                        translated_text = cached_value['translated']
                        # Actualizar contador de uso
                        cached_value['usage_count'] = cached_value.get('usage_count', 0) + 1
                    else:
                        translated_text = cached_value  # Formato antiguo
                    cache_hits += 1

                    # Log traducción desde caché
                    if self.logger:
                        self.logger.log_translation(element['text'], translated_text, "CACHE", 0.0)

                    # Mostrar progreso con traducción desde caché
                    if self.progress:
                        self.progress.show_element_progress(i, len(elements), cache_hits, api_calls, element['text'], translated_text)
                    else:
                        # Mostrar progreso simple con punto
                        print(".", end="", flush=True)
                else:
                    # Mostrar progreso antes de traducir
                    if self.progress:
                        self.progress.show_element_progress(i, len(elements), cache_hits, api_calls, element['text'])
                    else:
                        # Mostrar progreso con asterisco para API calls
                        print("*", end="", flush=True)

                    translated_text, cost = self.translate_with_claude(
                        element['text'],
                        target_lang,
                        element_type=element['type']
                    )
                    api_calls += 1
                    translated_count += 1
                    total_cost += cost

                    # Log traducción individual
                    if self.logger:
                        self.logger.log_translation(element['text'], translated_text, "API", cost)

                    # Mostrar progreso con traducción recién hecha
                    if self.progress:
                        self.progress.show_element_progress(i, len(elements), cache_hits, api_calls, element['text'], translated_text)

                # Aplicar traducción
                if element['type'] == 'text':
                    element['element'].replace_with(translated_text)
                elif element['type'] == 'alt':
                    element['element']['alt'] = translated_text
                elif element['type'] == 'title':
                    element['element']['title'] = translated_text

                # Rate limiting ahora se maneja automáticamente en translate_with_claude

            # Corregir atributos HTML específicos del idioma
            self.fix_html_attributes(soup, target_lang)

            # Guardar archivo traducido preservando formato
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                # Usar prettify() para mantener estructura del HTML árbol
                f.write(soup.prettify())

            # Calcular duración
            duration = time.time() - start_time
            duration_str = f"{int(duration//60)}m {int(duration%60)}s"

            # Log de finalización de archivo
            if self.logger:
                self.logger.log_file_complete(source_file.name, cache_hits, api_calls, duration_str, total_cost)

            # Mostrar completación
            if self.progress:
                self.progress.show_file_complete(cache_hits, api_calls, duration_str, total_cost)
            else:
                cost_str = f", ${total_cost:.4f}" if total_cost > 0 else ""
                print(f"\n      ✅ {api_calls} nuevos, {cache_hits} caché{cost_str}")

            # Guardar metadata del archivo traducido
            self.save_file_metadata(source_file, target_file, target_lang)

            # Guardar caché después de traducir HTML
            if translated_count > 0:
                self.save_cache()
                print(f"      💾 Caché guardado con {len(self.cache)} entradas")

            # Mostrar estadísticas del rate limiting si hubo traducciones
            if translated_count > 0:
                stats = self.rate_limiter.get_stats()
                print(f"      📊 Rate limiting: {stats['requests_last_minute']} req/min, delay actual: {stats['current_delay']:.1f}s")

            return True

        except Exception as e:
            # Manejar error gracefully y guardar progreso
            error_msg = str(e)

            # Registrar error con contexto
            if self.logger:
                self.logger.log_error(error_msg, f"File: {source_file.name}, Elements processed: {translated_count}")

            # Si es error de crédito, guardar progreso y mostrar mensaje útil
            if "crédito" in error_msg.lower() or "credit" in error_msg.lower():
                print(f"      💳 ¡Error de crédito! Progreso guardado:")
                print(f"          📄 Archivo: {source_file.name}")
                print(f"          ✅ Elementos traducidos antes del error: {translated_count}")
                print(f"          💾 Progreso guardado en caché para continuar después")

                # Guardar caché con el progreso actual
                if translated_count > 0:
                    self.save_cache()
                    print(f"          🔄 Caché actualizado: {len(self.cache)} entradas")

                print(f"\n      🔧 Para continuar:")
                print(f"          1. Recarga crédito en tu cuenta de Claude")
                print(f"          2. Ejecuta el mismo comando - continuará desde donde quedó")
                print(f"          3. El caché evitará repetir traducciones ya hechas")

            elif "rate limit" in error_msg.lower():
                print(f"      ⏳ Rate limit excedido. Progreso guardado hasta este punto.")
                if translated_count > 0:
                    self.save_cache()
                    print(f"          💾 {translated_count} traducciones guardadas en caché")
                print(f"          🕐 Reintenta en unos minutos")

            else:
                print(f"      ❌ Error: {e}")

            return False

    def translate_manual(self, target_lang, force_retranslate=False):
        """
        Traduce un manual completo a un idioma específico

        Args:
            target_lang: Código del idioma destino
            force_retranslate: Si True, retraduce aunque ya exista

        Returns:
            dict: Resultado de la traducción
        """
        if target_lang == 'es':
            return {
                'success': False,
                'message': 'El español es el idioma original, no requiere traducción'
            }

        if target_lang not in LANGUAGES:
            return {
                'success': False,
                'message': f'Idioma no soportado: {target_lang}'
            }

        # Rutas
        source_path = get_manual_path(self.manual_name)
        target_path = get_manual_path(self.manual_name, target_lang, 'html')

        if not source_path.exists():
            return {
                'success': False,
                'message': f'No se encuentra el manual original en {source_path}'
            }

        # Obtener archivos HTML y JSON (buscar en directorio html/ si existe)
        html_dir = source_path / 'html'
        if html_dir.exists():
            html_files = list(html_dir.glob('*.html'))
            json_files = list(html_dir.glob('*.json'))
        else:
            html_files = list(source_path.glob('*.html'))
            json_files = list(source_path.glob('*.json'))

        if not html_files and not json_files:
            return {
                'success': False,
                'message': f'No se encontraron archivos HTML o JSON en {source_path} ni en {html_dir}'
            }

        # Verificar progreso previo de traducción
        existing_html = list(target_path.glob('*.html')) if target_path.exists() else []
        existing_json = list(target_path.glob('*.json')) if target_path.exists() else []

        # Análisis de reanudación inteligente
        if existing_html or existing_json:
            total_expected = len(html_files) + len(json_files)
            total_existing = len(existing_html) + len(existing_json)

            if total_existing == total_expected and not force_retranslate:
                print(f"✅ Traducción completa detectada: {total_existing}/{total_expected} archivos")
                return {
                    'success': True,
                    'message': f'Ya existe traducción completa a {get_language_display_name(target_lang)} ({total_existing} archivos)',
                    'files_processed': total_existing,
                    'from_cache': True
                }
            elif total_existing > 0:
                percentage = (total_existing / total_expected) * 100
                print(f"🔄 Traducción parcial detectada: {total_existing}/{total_expected} archivos ({percentage:.1f}%)")
                if not force_retranslate:
                    print(f"   ℹ️ Se continuará desde donde se interrumpió (detección inteligente activa)")
                else:
                    print(f"   ⚠️ Force_retranslate=True: se retraducirán TODOS los archivos")

        lang_name = LANGUAGES[target_lang]['name']
        print(f"🔄 Traduciendo {self.manual_name} a {lang_name}")
        print(f"   📁 Origen: {source_path}")
        print(f"   📁 Destino: {target_path}")
        total_files = len(html_files) + len(json_files)
        print(f"   📊 Archivos: {len(html_files)} HTML + {len(json_files)} JSON = {total_files}")

        # Inicializar logger y progreso
        self.logger = TranslationLogger(self.manual_name, target_lang)
        self.progress = ProgressDisplay(total_files)

        # Estimación de costo
        estimated_cost = estimate_translation_cost(len(html_files) * 30 + len(json_files) * 10)  # ~30 HTML, ~10 JSON

        # Confirmar si el costo es alto
        estimated_elements = len(html_files) * 30 + len(json_files) * 10
        if estimated_cost > 2.0:
            confirm = input(f"\n⚠️ Se van a traducir ~{estimated_elements} elementos. ¿Continuar? (s/N): ")
            if confirm.lower() != 's':
                if self.logger:
                    self.logger.log_error("Usuario canceló por costo alto", f"Estimado: ${estimated_cost:.2f}")
                    self.logger.finalize_session()
                return {
                    'success': False,
                    'message': 'Traducción cancelada por el usuario'
                }

        # Procesar archivos
        start_time = time.time()
        processed_files = 0
        errors = 0

        # 1. Procesar archivos HTML
        try:
            # Estimar tiempo total al inicio
            remaining_files = sum(1 for f in html_files if force_retranslate or not (target_path / f.name).exists())
            if remaining_files > 0:
                avg_time_per_file = 1.5  # minutos promedio por archivo
                total_eta_minutes = remaining_files * avg_time_per_file
                print(f"   ⏱️ ETA total estimado: ~{int(total_eta_minutes)} minutos para {remaining_files} archivos restantes")
                print()

            for i, html_file in enumerate(html_files, 1):
                target_file = target_path / html_file.name
                success = self.translate_html_file(html_file, target_file, target_lang, force_retranslate, file_num=i)

                if success:
                    processed_files += 1
                else:
                    errors += 1
                    if self.logger:
                        self.logger.log_error(f"Error procesando archivo HTML: {html_file.name}")

                # Mostrar progreso general con datos actualizados
                if self.progress:
                    self.progress.show_overall_progress(processed_files, len(html_files))

        except Exception as e:
            error_msg = str(e)
            if "crédito" in error_msg.lower() or "credit" in error_msg.lower():
                print(f"\n💳 ¡Se agotó el crédito de la API!")
                print(f"   📊 Progreso hasta ahora:")
                print(f"       ✅ Archivos completados: {processed_files}/{len(html_files)} HTML")
                print(f"       ❌ Errores: {errors}")
                print(f"       💾 Todo el progreso ha sido guardado en caché")
                print(f"\n   🔧 Para continuar cuando tengas crédito:")
                print(f"       • Ejecuta el mismo comando")
                print(f"       • La traducción continuará desde donde se interrumpió")
                print(f"       • No se repetirán archivos ya procesados")

                # Finalizar logs
                if self.logger:
                    self.logger.log_error(f"CREDIT_EXHAUSTED: {error_msg}", f"Completed: {processed_files}/{len(html_files)}")
                    self.logger.finalize_session()

                return {
                    'success': False,
                    'message': f'Crédito agotado después de {processed_files}/{len(html_files)} archivos',
                    'files_processed': processed_files,
                    'partial_completion': True
                }
            else:
                # Re-lanzar otros errores
                raise

        # 2. Procesar archivos JSON
        json_start_num = len(html_files)
        for i, json_file in enumerate(json_files, 1):
            file_num = json_start_num + i
            if self.progress:
                print(f"\n📄 [{file_num}/{total_files}] {json_file.name} (JSON)")
            else:
                print(f"   📄 JSON ({i}/{len(json_files)}) {json_file.name}")

            target_file = target_path / json_file.name
            success = self.translate_json_file(json_file, target_file, target_lang, force_retranslate)

            if success:
                processed_files += 1
            else:
                errors += 1

            # Guardar caché periódicamente
            if i % 5 == 0:
                self.save_cache()

        # Guardar caché final
        self.save_cache()

        elapsed_time = time.time() - start_time
        print(f"\n✅ Traducción completada en {elapsed_time/60:.1f} minutos")
        print(f"   📊 Procesados: {processed_files}/{len(html_files)}")
        if hasattr(self, 'progress') and self.progress and self.progress.total_cost > 0:
            print(f"   💰 Costo total: ${self.progress.total_cost:.4f}")
        if errors > 0:
            print(f"   ⚠️ Errores: {errors}")

        # Finalizar logging
        if self.logger:
            self.logger.finalize_session()
            print(f"   📜 Log guardado: {self.logger.log_file.name}")

        # Copiar recursos adicionales (imágenes, CSS, etc.)
        # Usar la misma lógica que para archivos HTML
        resource_source = html_dir if html_dir.exists() else source_path
        self.copy_resources(resource_source, target_path)

        return {
            'success': True,
            'message': f'Traducción a {lang_name} completada exitosamente',
            'files_processed': processed_files,
            'errors': errors,
            'time_elapsed': elapsed_time,
            'from_cache': False
        }

    def copy_resources(self, source_path, target_path):
        """Copia recursos adicionales (imágenes, CSS, archivos JS, etc.)"""
        import shutil
        import glob

        # Copiar directorios de recursos
        resources_dirs = ['lib', 'css', 'js', 'images', 'vendors', 'context']

        for resource_dir in resources_dirs:
            source_resource = source_path / resource_dir
            target_resource = target_path / resource_dir

            if source_resource.exists():
                if target_resource.exists():
                    shutil.rmtree(target_resource)
                shutil.copytree(source_resource, target_resource)
                print(f"      📁 Recursos copiados: {resource_dir}")

        # Copiar archivos JavaScript críticos (_*.js)
        js_files = list(source_path.glob('_*.js'))
        for js_file in js_files:
            target_js = target_path / js_file.name
            shutil.copy2(js_file, target_js)
            print(f"      📄 Script copiado: {js_file.name}")

# Alias para compatibilidad con el menú
MultiLanguageHTMLTranslator = HTMLTranslator

def main():
    """Función principal para usar desde línea de comandos"""
    import argparse

    parser = argparse.ArgumentParser(description='Traducir manual HTML a otro idioma')
    parser.add_argument('--lang', required=True, help='Código de idioma destino (ej: en, pt, fr)')
    parser.add_argument('--manual', default='open_aula_front', help='Nombre del manual')
    parser.add_argument('--force', action='store_true', help='Forzar retraducción')

    args = parser.parse_args()

    translator = HTMLTranslator(args.manual)
    result = translator.translate_manual(args.lang, args.force)

    if result['success']:
        print(f"✅ {result['message']}")
        if not result.get('from_cache', False):
            print(f"📊 Archivos procesados: {result.get('files_processed', 0)}")
            if 'time_elapsed' in result:
                print(f"⏱️ Tiempo: {result['time_elapsed']/60:.1f} minutos")
        sys.exit(0)
    else:
        print(f"❌ {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    main()