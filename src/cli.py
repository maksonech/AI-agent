#!/usr/bin/env python3
"""
Командный интерфейс для AI-агента анализа алертов.
Предоставляет различные режимы работы через аргументы командной строки.
"""
import argparse
import os
import sys
import time
from typing import List, Dict, Any
from datetime import datetime

# Импортируем необходимые библиотеки для работы с конфигурацией
try:
    from src.config import get_settings
    from src.config.logging_config import setup_tool_logger
    from src.config.exceptions import AIAgentError, FileOperationError, safe_execute
except ImportError as e:
    print(f"Ошибка импорта конфигурационных модулей: {str(e)}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Настройка логгера
cli_logger = setup_tool_logger("cli")


def setup_parser() -> argparse.ArgumentParser:
    """
    Настраивает парсер аргументов командной строки.
    
    Returns:
        argparse.ArgumentParser: Парсер аргументов командной строки
    """
    parser = argparse.ArgumentParser(
        description='AI-агент для анализа алертов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Запустить интерактивный режим
  python cli.py interactive
  
  # Проанализировать один файл алерта
  python cli.py analyze --file tests/fixtures/one_line_alert.txt
  
  # Проанализировать все файлы в директории в многопоточном режиме
  python cli.py batch --dir tests/fixtures --threads 4
  
  # Проверить статус токенов GigaChat
  python cli.py token-status
"""
    )
    
    # Создаем подпарсеры для различных команд
    subparsers = parser.add_subparsers(dest='command', help='Команда для выполнения')
    
    # Команда для интерактивного режима
    interactive_parser = subparsers.add_parser('interactive', help='Запустить интерактивный режим')
    
    # Команда для анализа одного файла
    analyze_parser = subparsers.add_parser('analyze', help='Анализировать один файл алерта')
    analyze_parser.add_argument('--file', '-f', required=True, help='Путь к файлу алерта')
    analyze_parser.add_argument('--output', '-o', help='Путь для сохранения результата (опционально)')
    
    # Команда для пакетного анализа файлов
    batch_parser = subparsers.add_parser('batch', help='Анализировать несколько файлов алертов')
    batch_parser.add_argument('--dir', '-d', required=True, help='Директория с файлами алертов')
    batch_parser.add_argument('--pattern', '-p', default='*.txt', help='Шаблон файлов для обработки (например, "*.txt")')
    batch_parser.add_argument('--threads', '-t', type=int, default=4, help='Количество потоков для обработки')
    batch_parser.add_argument('--output', '-o', help='Путь для сохранения результатов (опционально)')
    
    # Команда для проверки статуса токенов
    token_parser = subparsers.add_parser('token-status', help='Проверить статус токенов GigaChat')
    
    return parser


def run_interactive_mode() -> None:
    """Запускает интерактивный режим общения с агентом."""
    try:
        from src.main import chat
        print("Модуль основного чата успешно импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта модуля main: {str(e)}")
        print("Функция чата будет недоступна")
        return
    
    print("Запуск интерактивного режима AI-агента...")
    
    # Создаем уникальный идентификатор для сессии
    session_id = datetime.now().strftime('session_%Y%m%d_%H%M%S')
    
    try:
        chat(session_id)
    except Exception as e:
        cli_logger.critical(f"Критическая ошибка при запуске интерактивного режима: {str(e)}", exc_info=True)
        print(f"\n\n❌ Критическая ошибка: {str(e)}")
        print("Пожалуйста, проверьте лог-файлы для получения дополнительной информации.")
        sys.exit(1)


def run_single_analysis(file_path: str, output_path: str = None) -> None:
    """
    Выполняет анализ одного файла алерта и выводит результат.
    
    Args:
        file_path: Путь к файлу алерта
        output_path: Путь для сохранения результата (опционально)
    """
    try:
        from src.tools.alert_tools import analyze_file_alert
    except ImportError:
        try:
            from src.tools import analyze_file_alert
        except ImportError as e:
            print(f"❌ Ошибка импорта модуля analyze_file_alert: {str(e)}")
            print("Функция анализа алертов будет недоступна")
            return
    
    print(f"Анализ файла: {file_path}")
    
    if not os.path.exists(file_path):
        cli_logger.error(f"Файл не найден: {file_path}")
        print(f"\n❌ Ошибка: Файл не найден: {file_path}")
        sys.exit(1)
    
    try:
        start_time = time.time()
        result = analyze_file_alert.invoke(file_path)
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Анализ успешно завершен за {elapsed_time:.2f} секунд\n")
        print("Результат анализа:")
        print("=" * 80)
        print(result)
        print("=" * 80)
        
        # Сохраняем результат в файл, если указан путь
        if output_path:
            # Создаем директорию, если не существует
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"\nРезультат сохранен в файл: {output_path}")
        
    except Exception as e:
        cli_logger.error(f"Ошибка при анализе файла {file_path}: {str(e)}", exc_info=True)
        print(f"\n❌ Ошибка при анализе файла: {str(e)}")
        sys.exit(1)


def run_batch_analysis(directory: str, pattern: str = "*.txt", threads: int = 4, output_path: str = None) -> None:
    """
    Выполняет пакетный анализ файлов алертов в многопоточном режиме.
    
    Args:
        directory: Директория с файлами алертов
        pattern: Шаблон файлов для обработки
        threads: Количество потоков для обработки
        output_path: Путь для сохранения результатов (опционально)
    """
    try:
        from src.multithreaded import process_directory, save_results_to_json
        print("Модуль многопоточной обработки успешно импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта модуля multithreaded: {str(e)}")
        print("Функции пакетной обработки будут недоступны")
        return
    
    print(f"Пакетный анализ файлов в директории: {directory}")
    print(f"Шаблон файлов: {pattern}")
    print(f"Количество потоков: {threads}")
    
    try:
        # Функция обратного вызова для отображения прогресса
        def progress_callback(file_path, result, error):
            file_name = os.path.basename(file_path)
            if error:
                print(f"❌ Ошибка при обработке {file_name}: {error}")
            else:
                print(f"✅ Успешно обработан {file_name}")
        
        # Запускаем обработку директории
        start_time = time.time()
        results = process_directory(directory, pattern, threads, progress_callback)
        elapsed_time = time.time() - start_time
        
        # Выводим сводку
        success_count = sum(1 for res in results.values() if res["status"] == "success")
        error_count = sum(1 for res in results.values() if res["status"] == "error")
        
        print("\nСводка анализа:")
        print(f"Всего файлов: {len(results)}")
        print(f"Успешно: {success_count}")
        print(f"Ошибок: {error_count}")
        print(f"Общее время: {elapsed_time:.2f} секунд")
        
        # Сохраняем результаты в файл
        json_path = save_results_to_json(results, output_path)
        if json_path:
            print(f"\nРезультаты сохранены в: {json_path}")
        
    except Exception as e:
        cli_logger.error(f"Ошибка при пакетном анализе: {str(e)}", exc_info=True)
        print(f"\n❌ Ошибка при пакетном анализе: {str(e)}")
        sys.exit(1)


def check_token_status() -> None:
    """Проверяет и выводит статус токенов GigaChat."""
    try:
        from src.tools.gigachat_tools import check_token_status
    except ImportError:
        try:
            from src.tools import check_token_status
        except ImportError as e:
            print(f"❌ Ошибка импорта модуля check_token_status: {str(e)}")
            print("Функция проверки токенов будет недоступна")
            return
    
    print("Проверка статуса токенов GigaChat...")
    
    try:
        result = check_token_status.invoke("")
        print("\n" + result)
    except Exception as e:
        cli_logger.error(f"Ошибка при проверке статуса токенов: {str(e)}", exc_info=True)
        print(f"\n❌ Ошибка при проверке статуса токенов: {str(e)}")
        sys.exit(1)


def main() -> None:
    """Основная функция для обработки аргументов командной строки."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    if args.command == 'interactive':
        run_interactive_mode()
    elif args.command == 'analyze':
        run_single_analysis(args.file, args.output)
    elif args.command == 'batch':
        run_batch_analysis(args.dir, args.pattern, args.threads, args.output)
    elif args.command == 'token-status':
        check_token_status()
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОперация прервана пользователем.")
        sys.exit(0)
    except Exception as e:
        cli_logger.critical(f"Необработанная ошибка: {str(e)}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {str(e)}")
        print("Пожалуйста, проверьте лог-файлы для получения дополнительной информации.")
        sys.exit(1) 