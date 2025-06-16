"""Главный модуль для взаимодействия с агентами."""

# Импорты
import os
import logging
import sys
from datetime import datetime

# Проверяем доступность модели GigaChat перед импортом агентов
try:
    from src.agents.alert_agent import get_alert_agent
    from src.agents.assistant_agent import get_assistant_agent
    
    # Получаем экземпляры агентов для проверки инициализации
    alert_agent = get_alert_agent()
    assistant_agent = get_assistant_agent()
    
    if alert_agent.model is None or assistant_agent.model is None:
        print("⚠️ ОШИБКА: Модель GigaChat не инициализирована")
        logging.error("Модель GigaChat не инициализирована")
        sys.exit(1)
except ImportError as e:
    print(f"⚠️ ОШИБКА: Не удалось импортировать агентов: {str(e)}")
    logging.error(f"Не удалось импортировать агентов: {str(e)}")
    sys.exit(1)

# Пытаемся импортировать инструменты
try:
    from src.tools.alert_tools import analyze_file_alert
    from src.tools.gigachat_tools import check_token_status
except ImportError:
    # Резервный вариант для обратной совместимости
    from src.tools.tools import analyze_file_alert
    from src.tools.tools import check_token_status

# Импортируем модули централизованной конфигурации
from config import get_settings
from config.logging_config import setup_chat_logger
from config.settings import get_alert_file_path

# Импортируем систему обработки исключений
from config.exceptions import (
    AIAgentError, FileOperationError, GigaChatAPIError, DataProcessingError,
    format_exception, safe_execute
)

# Основной цикл общения с агентами
def chat(thread_id: str):
    """
    Основная функция для общения с агентами.
    """
    # Настройка логирования с помощью централизованной конфигурации
    logger = setup_chat_logger()
    logger.info(f"Сессия чата начата с thread_id: {thread_id}")
    
    # Получение настроек приложения
    settings = get_settings()
    
    # Флаг для отслеживания, был ли проанализирован алерт в этой сессии
    alert_analyzed = False
    last_alert_file = ""
    
    # Команды для выхода из программы
    exit_commands = ["exit", "выход", "пока", "до свидания", "бб", "bye", "quit", "q", "досвидания", "закрыть"]
    
    welcome_message = "Добро пожаловать в терминал общения с AI-агентами!"
    instructions = """Напишите Ваш запрос или введите 'exit' для выхода.
    
📄 Для анализа файлов с алертами введите 'файл' или 'анализ файла алерта'
📋 После анализа алерта можно запросить информацию о нем через 'последний алерт'
🔄 Для повторного анализа последнего алерта введите 'повторный анализ'
🔑 Для проверки статуса токенов GigaChat введите 'токены' или 'проверить токены'"""
    
    # Выводим приветственное сообщение один раз и записываем в лог
    print(welcome_message)
    print(instructions)
    logger.info(f"Бот: {welcome_message}")
    logger.info(f"Бот: {instructions}")
    
    while True:
        try:
            user_input = input("\n>>: ")
            logger.info(f"Пользователь: {user_input}")
            
            if user_input.lower() in exit_commands:
                farewell_message = "До свидания!"
                print(farewell_message)
                logger.info(f"Бот: {farewell_message}")
                logger.info("Сессия чата завершена")
                break
            
            # Проверяем, если пользователь хочет узнать статус токенов GigaChat
            if user_input.lower() in ["токены", "проверить токены", "статус токенов", "токен", "проверить токен"]:
                logger.info("Прямой вызов функции check_token_status")
                
                def check_token_handler():
                    print("\n🔑 Проверка статуса токенов GigaChat:")
                    logger.info("Запрос информации о статусе токенов GigaChat")
                    
                    # Используем интерактивного ассистента для проверки токенов
                    result = assistant_agent.check_api_endpoint("token status")
                    print("🤖 :", result)
                    logger.info(f"Бот (проверка токенов): результат получен")
                
                # Используем safe_execute для безопасного выполнения функции
                result = safe_execute(
                    check_token_handler,
                    error_message="Ошибка при проверке токенов GigaChat",
                    logger=logger,
                    expected_exceptions=[GigaChatAPIError]
                )
                
                if isinstance(result, str) and result.startswith("❌"):
                    print("🤖 :", result)
                    
                continue
            
            # Проверяем, если пользователь хочет проанализировать файл алерта
            if user_input.lower() in ["проанализировать алерт из файла", "анализ файла алерта",
                                      "анализ алерта", "алерт", "файл"]:
                logger.info("Запрос на анализ файла алерта")
                
                def analyze_alert_handler():
                    # Предлагаем пользователю выбрать файл алерта
                    selected_file = select_alert_file()
                    
                    print(f"\n📄 Анализ файла: {os.path.basename(selected_file)}")
                    logger.info(f"Выбран файл для анализа: {selected_file}")
                    
                    # Используем агент анализа алертов
                    result = alert_agent.analyze_alert_file(selected_file)
                    
                    # Читаем оригинальный текст алерта для сохранения
                    original_alert_text = ""
                    try:
                        with open(selected_file, 'r', encoding='utf-8') as alert_file:
                            original_alert_text = alert_file.read()
                            nonlocal alert_analyzed, last_alert_file
                            alert_analyzed = True  # Отмечаем, что алерт был проанализирован
                            last_alert_file = selected_file
                    except Exception as e:
                        error = FileOperationError(f"Ошибка при чтении оригинального алерта: {str(e)}")
                        logger.error(format_exception(error))
                        original_alert_text = "Текст алерта не удалось прочитать"
                    
                    print("🤖 :", result)
                    return result
                
                # Используем safe_execute для безопасного выполнения функции
                result = safe_execute(
                    analyze_alert_handler,
                    error_message="Ошибка при анализе файла алерта",
                    logger=logger,
                    expected_exceptions=[FileOperationError, DataProcessingError]
                )
                
                if isinstance(result, str) and result.startswith("❌"):
                    print("🤖 :", result)
                    
                continue
            
            # Проверяем запрос на повторный анализ предыдущего алерта
            if user_input.lower() in ["повторно проанализировать", "проанализировать снова", "повторный анализ"]:
                if alert_analyzed and last_alert_file:
                    logger.info(f"Повторный анализ последнего алерта из файла: {last_alert_file}")
                    
                    def reanalyze_alert_handler():
                        print(f"\n📄 Повторный анализ файла: {os.path.basename(last_alert_file)}")
                        
                        # Используем агент анализа алертов для повторного анализа
                        result = alert_agent.analyze_alert_file(last_alert_file)
                        print("🤖 :", result)
                        logger.info(f"Бот (повторный анализ): результат получен")
                        
                        return result
                    
                    # Используем safe_execute для безопасного выполнения функции
                    result = safe_execute(
                        reanalyze_alert_handler,
                        error_message="Ошибка при повторном анализе файла алерта",
                        logger=logger,
                        expected_exceptions=[FileOperationError, DataProcessingError]
                    )
                    
                    if isinstance(result, str) and result.startswith("❌"):
                        print("🤖 :", result)
                        
                    continue
                else:
                    print("🤖 : Вы еще не анализировали ни одного алерта в этой сессии. Введите 'файл' или 'анализ файла алерта' для начала анализа.")
                    logger.info("Запрос на повторный анализ отклонен - алерт не был проанализирован")
                    continue
            
            # Проверяем, если пользователь запрашивает информацию о последнем алерте
            if user_input.lower() in ["последний алерт", "расскажи о последнем алерте", "что там с алертом", "данные алерта"]:
                logger.info("Пользователь запрашивает информацию о последнем проанализированном алерте")
                if alert_analyzed:
                    def get_alert_info_handler():
                        # Читаем содержимое файла с последним алертом
                        try:
                            with open(last_alert_file, 'r', encoding='utf-8') as file:
                                alert_text = file.read()
                        except Exception as e:
                            error = FileOperationError(f"Ошибка при чтении файла алерта: {str(e)}")
                            logger.error(format_exception(error))
                            return f"❌ Не удалось прочитать файл с алертом: {str(e)}"
                        
                        # Формируем запрос к агенту анализа алертов
                        result = alert_agent.analyze_alert(alert_text)
                        print("🤖 :", result)
                        return result
                    
                    # Используем safe_execute для безопасного выполнения функции
                    result = safe_execute(
                        get_alert_info_handler,
                        error_message="Ошибка при получении информации о последнем алерте",
                        logger=logger,
                        expected_exceptions=[FileOperationError, DataProcessingError]
                    )
                    
                    if isinstance(result, str) and result.startswith("❌"):
                        print("🤖 :", result)
                        
                    continue
                else:
                    print("🤖 : Вы еще не анализировали ни одного алерта в этой сессии. Введите 'файл' или 'анализ файла алерта' для начала анализа.")
                    logger.info("Запрос информации о последнем алерте отклонен - алерт не был проанализирован")
                    continue
            
            # Для всех остальных запросов используем интерактивного ассистента
            def chat_with_assistant_handler():
                logger.info(f"Обработка запроса пользователя интерактивным ассистентом: {user_input[:50]}...")
                
                # Используем интерактивного ассистента для обработки запроса
                result = assistant_agent.process_request(user_input, thread_id)
                print("🤖 :", result)
                logger.info(f"Бот: ответ получен длиной {len(result)} символов")
                
                return result
            
            # Используем safe_execute для безопасного выполнения функции
            result = safe_execute(
                chat_with_assistant_handler,
                error_message="Ошибка при обработке запроса",
                logger=logger,
                expected_exceptions=[AIAgentError]
            )
            
            if isinstance(result, str) and result.startswith("❌"):
                print("🤖 :", result)
                
        except KeyboardInterrupt:
            print("\n🤖 : Прервано пользователем. Для выхода введите 'exit'.")
            logger.info("Прервано пользователем (KeyboardInterrupt)")
        except Exception as e:
            error_msg = f"Непредвиденная ошибка: {str(e)}"
            print(f"🤖 : {error_msg}")
            logger.error(error_msg, exc_info=True)

def select_alert_file():
    """
    Функция для выбора файла алерта из доступных.
    
    Returns:
        str: Путь к выбранному файлу алерта
    """
    try:
        # Получаем путь к директории с файлами алертов
        test_alerts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'fixtures')
        data_alerts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'alerts')
        
        # Создаем директорию для алертов, если она не существует
        os.makedirs(data_alerts_dir, exist_ok=True)
        
        # Список директорий для поиска файлов алертов
        alert_dirs = []
        
        # Добавляем директории, если они существуют
        if os.path.exists(test_alerts_dir):
            alert_dirs.append(test_alerts_dir)
        if os.path.exists(data_alerts_dir):
            alert_dirs.append(data_alerts_dir)
        
        if not alert_dirs:
            raise FileOperationError("Не найдены директории с файлами алертов")
        
        # Собираем все файлы из всех директорий
        all_files = []
        for directory in alert_dirs:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            text_files = [f for f in files if f.endswith(('.txt', '.log', '.json'))]
            all_files.extend([(f, directory) for f in text_files])
        
        if not all_files:
            # Создаем пример файла с алертом, если нет ни одного файла
            sample_file = os.path.join(data_alerts_dir, "sample_alert.txt")
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write("""ALERT: High CPU Usage
Service: api-gateway
Severity: Critical
Time: 2023-05-15 14:32:45
Metrics: CPU: 95%, Memory: 87%
Details: The API Gateway service has been experiencing high CPU usage for the last 15 minutes.
""")
            all_files = [("sample_alert.txt", data_alerts_dir)]
        
        # Выводим список файлов для выбора
        print("\nДоступные файлы с алертами:")
        for i, (file, directory) in enumerate(all_files, 1):
            print(f"{i}. {file} ({os.path.basename(directory)})")
        
        # Запрашиваем выбор пользователя
        while True:
            try:
                choice = input("\nВыберите номер файла (или введите 'q' для отмены): ")
                
                if choice.lower() == 'q':
                    raise KeyboardInterrupt("Выбор файла отменен пользователем")
                
                index = int(choice) - 1
                if 0 <= index < len(all_files):
                    selected_file, directory = all_files[index]
                    return os.path.join(directory, selected_file)
                else:
                    print("❌ Некорректный номер. Пожалуйста, выберите номер из списка.")
            except ValueError:
                print("❌ Пожалуйста, введите число или 'q' для отмены.")
    except Exception as e:
        error_message = f"Ошибка при выборе файла алерта: {str(e)}"
        logger.error(error_message)
        raise FileOperationError(error_message)

if __name__ == "__main__":
    # Создаем уникальный идентификатор для сессии
    thread_id = datetime.now().strftime('session_%Y%m%d_%H%M%S')
    
    # Запускаем основной цикл общения с агентами
    chat(thread_id)