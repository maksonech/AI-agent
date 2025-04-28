"""Главный модуль для взаимодействия с агентом GigaChat."""

# Импорты
import os
import logging
from datetime import datetime
from Source.agent import agent
from Source.tools import analyze_file_alert, check_token_status

# Настройка логирования
def setup_logging():
    """
    Настройка логирования для записи диалогов с ботом.
    """
    # Создание директории для логов, если она не существует
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Формирование имени файла лога с текущей датой и временем
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = os.path.join(log_dir, f'chat_log_{current_time}.log')
    
    # Настройка логгера
    logger = logging.getLogger('chat_logger')
    logger.setLevel(logging.INFO)
    
    # Обработчик для записи в файл
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Форматтер для логов
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Добавление обработчика к логгеру
    logger.addHandler(file_handler)
    
    return logger

def select_alert_file():
    """
    Функция для выбора файла алерта для анализа.
    
    Returns:
        str: Путь к выбранному файлу.
    """
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Список доступных файлов алертов
    alert_files = {
        '1': {
            'name': 'Стандартный алерт',
            'path': os.path.join(project_dir, 'TestAlerts/one_line_alert.txt')
        },
        '2': {
            'name': 'Множественные алерты',
            'path': os.path.join(project_dir, 'TestAlerts/multiple_alerts.txt')
        },
        '3': {
            'name': 'Проблемный алерт',
            'path': os.path.join(project_dir, 'TestAlerts/one_line_problematic_alert.txt')
        }
    }
    
    print("\nВыберите файл с алертом для анализа:")
    for key, file_info in alert_files.items():
        print(f"{key}. {file_info['name']} ({os.path.basename(file_info['path'])})")
    
    while True:
        choice = input("\nВведите номер файла (1-3) или нажмите Enter для стандартного алерта: ")
        
        if not choice:  # Если пустой ввод, используем стандартный алерт
            return alert_files['1']['path']
        
        if choice in alert_files:
            return alert_files[choice]['path']
        else:
            print("❌ Некорректный выбор. Пожалуйста, введите число от 1 до 3.")

# Основной цикл общения с агентом
def chat(thread_id: str):
    """
    Основная функция для общения с агентом.
    """
    # Настройка логирования
    logger = setup_logging()
    logger.info(f"Сессия чата начата с thread_id: {thread_id}")
    
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
                try:
                    print("\n🔑 Проверка статуса токенов GigaChat:")
                    logger.info("Запрос информации о статусе токенов GigaChat")
                    
                    result = check_token_status.invoke("")
                    print("🤖 :", result)
                    logger.info(f"Бот (прямой вызов check_token_status): результат получен")
                    
                    continue
                except Exception as e:
                    error_msg = f"Ошибка при прямом вызове check_token_status: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    print("🤖 :", f"Произошла ошибка при проверке токенов: {str(e)}")
                    continue
            
            # Проверяем, если пользователь хочет проанализировать файл алерта
            if user_input.lower() in ["проанализировать алерт из файла", "анализ файла алерта",
                                      "прочитать one_line_alert.txt", "анализ one_line_alert", "файл"]:
                logger.info("Прямой вызов функции analyze_file_alert без использования агента")
                try:
                    # Предлагаем пользователю выбрать файл алерта
                    selected_file = select_alert_file()
                    
                    print(f"\n📄 Анализ файла: {os.path.basename(selected_file)}")
                    logger.info(f"Выбран файл для анализа: {selected_file}")
                    
                    result = analyze_file_alert.invoke(selected_file)
                    print("🤖 :", result)
                    logger.info(f"Бот (прямой вызов): {result}")
                    
                    # Читаем оригинальный текст алерта для сохранения
                    original_alert_text = ""
                    try:
                        with open(selected_file, 'r', encoding='utf-8') as alert_file:
                            original_alert_text = alert_file.read()
                            alert_analyzed = True  # Отмечаем, что алерт был проанализирован
                            last_alert_file = selected_file
                    except Exception as e:
                        logger.error(f"Ошибка при чтении оригинального алерта: {str(e)}")
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
                    
                    continue
                except Exception as e:
                    error_msg = f"Ошибка при прямом вызове analyze_file_alert: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    print("🤖 :", f"Произошла ошибка при анализе файла: {str(e)}")
                    continue
            
            # Проверяем запрос на повторный анализ предыдущего алерта
            if user_input.lower() in ["повторно проанализировать", "проанализировать снова", "повторный анализ"]:
                if alert_analyzed and last_alert_file:
                    logger.info(f"Повторный анализ последнего алерта из файла: {last_alert_file}")
                    try:
                        print(f"\n📄 Повторный анализ файла: {os.path.basename(last_alert_file)}")
                        
                        result = analyze_file_alert.invoke(last_alert_file)
                        print("🤖 :", result)
                        logger.info(f"Бот (повторный вызов): {result}")
                        
                        # Обновляем сохраненную информацию об алерте
                        try:
                            with open(last_alert_file, 'r', encoding='utf-8') as alert_file:
                                original_alert_text = alert_file.read()
                        except Exception as e:
                            logger.error(f"Ошибка при чтении оригинального алерта: {str(e)}")
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
                        
                        continue
                    except Exception as e:
                        error_msg = f"Ошибка при повторном анализе файла: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        print("🤖 :", f"Произошла ошибка при повторном анализе файла: {str(e)}")
                        continue
                else:
                    print("🤖 : Вы еще не анализировали ни одного алерта в этой сессии. Введите 'файл' или 'анализ файла алерта' для начала анализа.")
                    logger.info("Запрос на повторный анализ отклонен - алерт не был проанализирован")
                    continue
            
            # Проверяем, если пользователь запрашивает информацию о последнем алерте
            if user_input.lower() in ["последний алерт", "расскажи о последнем алерте", "что там с алертом", "данные алерта"]:
                logger.info("Пользователь запрашивает информацию о последнем проанализированном алерте")
                if alert_analyzed:
                    safe_input = "Расскажи подробнее о последнем проанализированном алерте, который был сохранен в памяти. Какие там были проблемы, HTTP коды, статусы?"
                else:
                    print("🤖 : Вы еще не анализировали ни одного алерта в этой сессии. Введите 'файл' или 'анализ файла алерта' для начала анализа.")
                    logger.info("Запрос информации об алерте отклонен - алерт не был проанализирован")
                    continue
            
            # Логирование момента отправки запроса боту
            logger.info("Отправка запроса боту...")
            
            # Формируем безопасную кодировку ввода
            safe_input = user_input.encode('utf-8', errors='replace').decode('utf-8')
            
            # Вызов агента для получения ответа
            response = agent.invoke({"messages": [("user", safe_input)]}, config=config)
            
            # Получение ответа бота
            bot_response = response["messages"][-1].content
            
            # Вывод ответа и логирование
            print("🤖 :", bot_response)
            logger.info(f"Бот: {bot_response}")
            
        except KeyboardInterrupt:
            interrupt_message = "\nВыход из программы. До свидания!"
            print(interrupt_message)
            logger.warning("Сессия прервана пользователем (KeyboardInterrupt)")
            logger.info(f"Бот: {interrupt_message}")
            break
        except Exception as e:
            error_message = f"Произошла ошибка: {str(e)}"
            print(error_message)
            logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)

if __name__ == "__main__":
    chat('SberAX_consultant')