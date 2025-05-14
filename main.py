"""Главный модуль для взаимодействия с агентом GigaChat."""

# Импорты
import os
import logging
from datetime import datetime
from src.core.agent import agent

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


# Основной цикл общения с агентом
def chat(thread_id: str):
    """
    Основная функция для общения с агентом.
    """
    # Настройка логирования с помощью централизованной конфигурации
    logger = setup_chat_logger()
    logger.info(f"Сессия чата начата с thread_id: {thread_id}")
    
    # Получение настроек приложения
    settings = get_settings()
    
    # Флаг для отслеживания, был ли проанализирован алерт в этой сессии
    alert_analyzed = False
    last_alert_file = ""
    
    config = {"configurable": {"thread_id": thread_id}}
    welcome_message = "Добро пожаловать в терминал общения с GigaChat!"
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
            
            if user_input.lower() == "exit":
                farewell_message = "До свидания!"
                print(farewell_message)
                logger.info(f"Бот: {farewell_message}")
                logger.info("Сессия чата завершена")
                break
            
            # Проверяем, если пользователь хочет узнать статус токенов GigaChat
            if user_input.lower() in ["токены", "проверить токены", "статус токенов", "токен", "проверить токен"]:
                logger.info("Прямой вызов функции check_token_status без использования агента")
                
                def check_token_handler():
                    print("\n🔑 Проверка статуса токенов GigaChat:")
                    logger.info("Запрос информации о статусе токенов GigaChat")
                    
                    result = check_token_status.invoke("")
                    print("🤖 :", result)
                    logger.info(f"Бот (прямой вызов check_token_status): результат получен")
                
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
                logger.info("Прямой вызов функции analyze_file_alert без использования агента")
                
                def analyze_alert_handler():
                    # Предлагаем пользователю выбрать файл алерта
                    selected_file = select_alert_file()
                    
                    print(f"\n📄 Анализ файла: {os.path.basename(selected_file)}")
                    logger.info(f"Выбран файл для анализа: {selected_file}")
                    
                    result = analyze_file_alert.invoke(selected_file)
                    
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
                    
                    # Сохраняем анализ алерта в контексте диалога для дальнейшего взаимодействия
                    save_to_context = f"""Я проанализировал алерт из файла {os.path.basename(selected_file)}. 

Оригинальный текст алерта:
```
{original_alert_text}
```

Результат анализа:
{result}"""
                    
                    # Добавляем результат анализа в историю диалога
                    try:
                        response = agent.invoke({"messages": [("user", "Сохрани информацию о проанализированном алерте:"), ("assistant", save_to_context)]}, config=config)
                        logger.info("Результат анализа алерта сохранен в истории диалога с ботом")
                        print("📋 Информация об алерте сохранена в памяти бота. Вы можете задавать вопросы по этому алерту.")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении анализа алерта в истории диалога: {str(e)}", exc_info=True)
                        print("⚠️ Не удалось сохранить информацию об алерте в памяти бота.")
                    
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
                        
                        result = analyze_file_alert.invoke(last_alert_file)
                        print("🤖 :", result)
                        logger.info(f"Бот (повторный вызов): {result}")
                        
                        # Обновляем сохраненную информацию об алерте
                        try:
                            with open(last_alert_file, 'r', encoding='utf-8') as alert_file:
                                original_alert_text = alert_file.read()
                        except Exception as e:
                            error = FileOperationError(f"Ошибка при чтении оригинального алерта: {str(e)}")
                            logger.error(format_exception(error))
                            original_alert_text = "Текст алерта не удалось прочитать"
                        
                        # Сохраняем обновленный анализ алерта в контексте диалога
                        save_to_context = f"""Я повторно проанализировал алерт из файла {os.path.basename(last_alert_file)}. 

Оригинальный текст алерта:
```
{original_alert_text}
```

Результат анализа:
{result}"""
                        
                        # Добавляем результат анализа в историю диалога
                        try:
                            response = agent.invoke({"messages": [("user", "Сохрани обновленную информацию о проанализированном алерте:"), ("assistant", save_to_context)]}, config=config)
                            logger.info("Обновленный результат анализа алерта сохранен в истории диалога с ботом")
                            print("📋 Обновленная информация об алерте сохранена в памяти бота.")
                        except Exception as e:
                            logger.error(f"Ошибка при сохранении обновленного анализа алерта в истории диалога: {str(e)}", exc_info=True)
                            print("⚠️ Не удалось сохранить обновленную информацию об алерте в памяти бота.")
                        
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
                        chat_request = f"Расскажи мне подробнее о проанализированном алерте. Какая была проблема, и в чем ее причина? Предложи варианты решения."
                        logger.info(f"Отправка запроса агенту о последнем алерте: {chat_request}")
                        
                        response = agent.invoke({"messages": [("user", chat_request)]}, config=config)
                        
                        if "output" in response:
                            bot_response = response["output"]
                            print("🤖 :", bot_response)
                            logger.info(f"Бот: {bot_response}")
                            return bot_response
                        else:
                            error_message = "Не удалось получить ответ от бота о последнем алерте"
                            logger.warning(error_message)
                            raise AIAgentError(error_message)
                    
                    # Используем safe_execute для безопасного выполнения функции
                    result = safe_execute(
                        get_alert_info_handler,
                        error_message="Ошибка при запросе информации о последнем алерте",
                        logger=logger,
                        expected_exceptions=[AIAgentError]
                    )
                    
                    if isinstance(result, str) and result.startswith("❌"):
                        print("🤖 : Извините, не удалось получить ответ от бота.")
                        
                    continue
                else:
                    print("🤖 : Вы еще не анализировали ни одного алерта в этой сессии. Введите 'файл' или 'анализ файла алерта' для начала анализа.")
                    logger.info("Запрос информации о последнем алерте отклонен - алерт не был проанализирован")
                    continue
            
            # Обычный запрос к агенту
            def chat_with_agent_handler():
                logger.info(f"Отправка запроса агенту: {user_input}")
                response = agent.invoke({"messages": [("user", user_input)]}, config=config)
                
                if "output" in response:
                    bot_response = response["output"]
                    print("🤖 :", bot_response)
                    logger.info(f"Бот: {bot_response}")
                    return bot_response
                else:
                    error_message = "Не удалось получить ответ от бота"
                    logger.warning(error_message)
                    raise AIAgentError(error_message)
            
            # Используем safe_execute для безопасного выполнения функции
            result = safe_execute(
                chat_with_agent_handler,
                error_message="Ошибка при обработке запроса",
                logger=logger,
                expected_exceptions=[AIAgentError]
            )
            
            if isinstance(result, str) and result.startswith("❌"):
                print("🤖 : Извините, не удалось получить ответ от бота.")
                
        except KeyboardInterrupt:
            logger.info("Пользователь прервал выполнение с помощью Ctrl+C")
            print("\n\nПрограмма завершена пользователем.")
            break
        except Exception as e:
            error_msg = f"Критическая ошибка в главном цикле: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"\n\nКритическая ошибка: {str(e)}")
            print("Попробуйте снова или перезапустите программу.")


def select_alert_file():
    """
    Функция для выбора файла алерта для анализа.
    
    Returns:
        str: Путь к выбранному файлу.
        
    Raises:
        FileOperationError: Если возникла ошибка при работе с файлами алертов
    """
    project_dir = os.path.dirname(os.path.abspath(__file__))
    settings = get_settings()
    
    # Получаем путь к директории с тестовыми алертами
    alerts_dir = os.path.join(project_dir, 'TestAlerts')
    
    # Проверяем существование директории
    if not os.path.exists(alerts_dir):
        error_message = f"Директория с алертами не найдена: {alerts_dir}"
        logger.error(error_message)
        raise FileOperationError(error_message)
    
    # Получаем список всех файлов .txt в директории TestAlerts
    alert_files_dict = {}
    alert_file_index = 1
    
    try:
        for filename in sorted(os.listdir(alerts_dir)):
            if filename.endswith('.txt'):
                file_path = os.path.join(alerts_dir, filename)
                # Определяем тип алерта на основе имени файла
                file_type = "Стандартный алерт"
                if "multiple" in filename:
                    file_type = "Множественные алерты"
                elif "problematic" in filename:
                    file_type = "Проблемный алерт"
                elif "three" in filename:
                    file_type = "Три алерта"
                elif "sample" in filename:
                    file_type = "Образец алерта"
                
                alert_files_dict[str(alert_file_index)] = {
                    'name': file_type,
                    'path': file_path
                }
                alert_file_index += 1
    except Exception as e:
        error_message = f"Ошибка при чтении директории с алертами: {str(e)}"
        logger.error(error_message)
        raise FileOperationError(error_message)
    
    # Проверяем, что найдены файлы алертов
    if not alert_files_dict:
        error_message = f"В директории {alerts_dir} не найдены файлы алертов с расширением .txt"
        logger.error(error_message)
        raise FileOperationError(error_message)
    
    print("\nВыберите файл с алертом для анализа:")
    for key, file_info in alert_files_dict.items():
        print(f"{key}. {file_info['name']} ({os.path.basename(file_info['path'])})")
    
    while True:
        choice = input(f"\nВведите номер файла (1-{len(alert_files_dict)}) или нажмите Enter для стандартного алерта: ")
        
        if not choice:  # Если пустой ввод, используем первый файл в списке
            return alert_files_dict['1']['path']
        
        if choice in alert_files_dict:
            return alert_files_dict[choice]['path']
        else:
            print(f"❌ Некорректный выбор. Пожалуйста, введите число от 1 до {len(alert_files_dict)}.")


if __name__ == "__main__":
    print("Запуск AI-агента для анализа алертов...")
    
    # Создаем уникальный идентификатор для сессии
    session_id = datetime.now().strftime('session_%Y%m%d_%H%M%S')
    
    try:
        chat(session_id)
    except Exception as e:
        # Получаем и настраиваем логгер для критических ошибок
        logger = setup_chat_logger()
        logger.critical(f"Критическая ошибка при запуске приложения: {str(e)}", exc_info=True)
        print(f"\n\nКритическая ошибка при запуске приложения: {str(e)}")
        print("Пожалуйста, проверьте логи для получения дополнительной информации.")