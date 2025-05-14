"""
Модуль для многопоточного анализа алертов.
Позволяет параллельно обрабатывать несколько алертов для улучшения производительности.
"""
import os
import threading
import queue
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime

try:
    from src.tools import analyze_file_alert
except ImportError:
    from src.tools.alert_tools import analyze_file_alert

from src.config import get_settings
from src.config.logging_config import setup_tool_logger
from src.config.settings import get_alert_file_path, get_data_path
from src.config.exceptions import (
    FileOperationError, DataProcessingError, safe_execute, format_exception
)

# Настройка логгера
mt_logger = setup_tool_logger("multithreaded")

# Очередь для результатов анализа
results_queue = queue.Queue()

# Блокировка для безопасного доступа к общим ресурсам
results_lock = threading.Lock()


class AlertAnalyzeThread(threading.Thread):
    """
    Поток для анализа алерта из файла.
    """
    
    def __init__(
        self, 
        file_path: str, 
        thread_id: int, 
        callback: Optional[Callable[[str, str, Any], None]] = None
    ):
        """
        Инициализирует поток анализа алерта.
        
        Args:
            file_path: Путь к файлу с алертом
            thread_id: Идентификатор потока
            callback: Функция обратного вызова для обработки результатов
        """
        super().__init__(name=f"AlertThread-{thread_id}")
        self.file_path = file_path
        self.thread_id = thread_id
        self.result = None
        self.error = None
        self.callback = callback
        self.finished = False
        self.start_time = None
        self.end_time = None
    
    def run(self):
        """Выполняет анализ алерта в отдельном потоке."""
        mt_logger.info(f"Поток {self.name} начал обработку файла: {self.file_path}")
        self.start_time = time.time()
        
        try:
            # Проверка существования файла
            if not os.path.exists(self.file_path):
                raise FileOperationError(f"Файл алерта не найден: {self.file_path}")
            
            # Выполняем анализ алерта
            self.result = analyze_file_alert.invoke(self.file_path)
            
            # Сохраняем результат
            with results_lock:
                results_queue.put((self.thread_id, self.file_path, self.result, None))
                
            # Вызываем callback, если он предоставлен
            if self.callback:
                self.callback(self.file_path, self.result, None)
                
            mt_logger.info(f"Поток {self.name} успешно завершил обработку файла: {self.file_path}")
        except Exception as e:
            self.error = e
            error_msg = format_exception(e) if isinstance(e, (FileOperationError, DataProcessingError)) else str(e)
            mt_logger.error(f"Ошибка в потоке {self.name}: {error_msg}", exc_info=True)
            
            # Сохраняем ошибку
            with results_lock:
                results_queue.put((self.thread_id, self.file_path, None, error_msg))
                
            # Вызываем callback, если он предоставлен
            if self.callback:
                self.callback(self.file_path, None, error_msg)
        finally:
            self.end_time = time.time()
            self.finished = True


def analyze_multiple_alerts(
    file_paths: List[str], 
    max_threads: int = 4, 
    callback: Optional[Callable[[str, str, Any], None]] = None
) -> Dict[str, Any]:
    """
    Анализирует несколько файлов алертов параллельно.
    
    Args:
        file_paths: Список путей к файлам алертов
        max_threads: Максимальное количество одновременных потоков
        callback: Функция обратного вызова для обработки результатов
        
    Returns:
        Dict[str, Any]: Словарь с результатами анализа для каждого файла
    """
    if not file_paths:
        mt_logger.warning("Не предоставлены файлы для анализа")
        return {}
    
    # Очищаем очередь результатов
    while not results_queue.empty():
        results_queue.get()
    
    start_time = time.time()
    mt_logger.info(f"Начало многопоточного анализа {len(file_paths)} алертов")
    
    # Создаем и запускаем потоки
    threads = []
    active_threads = 0
    file_index = 0
    
    results = {}  # Словарь для хранения результатов
    
    while file_index < len(file_paths) or active_threads > 0:
        # Запускаем новые потоки, если есть свободные слоты и файлы для обработки
        while active_threads < max_threads and file_index < len(file_paths):
            file_path = file_paths[file_index]
            thread = AlertAnalyzeThread(file_path, file_index, callback)
            threads.append(thread)
            thread.start()
            
            file_index += 1
            active_threads += 1
            
            mt_logger.info(f"Запущен поток {thread.name} для файла {file_path}")
        
        # Проверяем завершенные потоки и обновляем счетчик активных потоков
        active_threads = sum(1 for t in threads if t.is_alive())
        
        # Собираем результаты из очереди
        while not results_queue.empty():
            thread_id, file_path, result, error = results_queue.get()
            if error:
                results[file_path] = {"status": "error", "error": error}
            else:
                results[file_path] = {"status": "success", "result": result}
        
        # Небольшая пауза для снижения загрузки CPU
        time.sleep(0.1)
    
    # Ждем завершения всех потоков (на всякий случай)
    for thread in threads:
        if thread.is_alive():
            thread.join(timeout=1.0)
    
    # Собираем оставшиеся результаты из очереди
    while not results_queue.empty():
        thread_id, file_path, result, error = results_queue.get()
        if error:
            results[file_path] = {"status": "error", "error": error}
        else:
            results[file_path] = {"status": "success", "result": result}
    
    # Собираем статистику выполнения
    total_time = time.time() - start_time
    success_count = sum(1 for res in results.values() if res["status"] == "success")
    error_count = sum(1 for res in results.values() if res["status"] == "error")
    
    mt_logger.info(f"Завершен многопоточный анализ алертов. "
                 f"Время: {total_time:.2f} сек, "
                 f"Успешно: {success_count}, "
                 f"Ошибок: {error_count}")
    
    return results


def process_directory(
    directory_path: str, 
    file_pattern: str = "*.txt", 
    max_threads: int = 4,
    callback: Optional[Callable[[str, str, Any], None]] = None
) -> Dict[str, Any]:
    """
    Обрабатывает все файлы в директории, соответствующие шаблону.
    
    Args:
        directory_path: Путь к директории с файлами алертов
        file_pattern: Шаблон имен файлов для обработки
        max_threads: Максимальное количество одновременных потоков
        callback: Функция обратного вызова для обработки результатов
        
    Returns:
        Dict[str, Any]: Словарь с результатами анализа для каждого файла
    """
    import glob
    
    # Получаем абсолютный путь к директории
    if not os.path.isabs(directory_path):
        if directory_path.startswith("tests/fixtures"):
            directory_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), directory_path)
        else:
            directory_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "fixtures", directory_path)
    
    # Проверяем существование директории
    if not os.path.exists(directory_path):
        error_msg = f"Директория не найдена: {directory_path}"
        mt_logger.error(error_msg)
        raise FileOperationError(error_msg)
    
    # Получаем список файлов по шаблону
    pattern = os.path.join(directory_path, file_pattern)
    file_paths = glob.glob(pattern)
    
    if not file_paths:
        warning_msg = f"Не найдено файлов по шаблону {pattern}"
        mt_logger.warning(warning_msg)
        return {}
    
    mt_logger.info(f"Найдено {len(file_paths)} файлов для обработки в {directory_path}")
    
    # Анализируем файлы многопоточно
    return analyze_multiple_alerts(file_paths, max_threads, callback)


def save_results_to_json(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Сохраняет результаты анализа в JSON-файл.
    
    Args:
        results: Словарь с результатами анализа
        output_path: Путь для сохранения файла (опционально)
        
    Returns:
        str: Путь к сохраненному файлу
    """
    import json
    
    if not results:
        mt_logger.warning("Нет результатов для сохранения")
        return ""
    
    if output_path is None:
        # Создаем имя файла с текущей датой/временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "Results", 
            f"alerts_analysis_{timestamp}.json"
        )
    
    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        mt_logger.info(f"Результаты успешно сохранены в {output_path}")
        return output_path
    except Exception as e:
        error_msg = f"Ошибка при сохранении результатов: {str(e)}"
        mt_logger.error(error_msg)
        raise FileOperationError(error_msg)


if __name__ == "__main__":
    # Пример использования
    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "fixtures")
    
    print(f"Анализ алертов в директории: {test_dir}")
    
    def print_callback(file_path, result, error):
        """Функция обратного вызова для вывода результатов."""
        if error:
            print(f"❌ Ошибка при обработке {os.path.basename(file_path)}: {error}")
        else:
            print(f"✅ Успешно обработан {os.path.basename(file_path)}")
    
    results = process_directory(test_dir, max_threads=2, callback=print_callback)
    
    # Выводим сводку
    print("\nСводка анализа:")
    success_count = sum(1 for res in results.values() if res["status"] == "success")
    error_count = sum(1 for res in results.values() if res["status"] == "error")
    
    print(f"Всего файлов: {len(results)}")
    print(f"Успешно: {success_count}")
    print(f"Ошибок: {error_count}")
    
    # Сохраняем результаты
    output_path = save_results_to_json(results)
    print(f"\nРезультаты сохранены в: {output_path}") 