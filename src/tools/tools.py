"""
Этот модуль реэкспортирует инструменты из новой модульной структуры.
Сохранен для обратной совместимости со старым кодом.
"""
import logging
from datetime import datetime
import os

# Настройка логирования для инструментов
tool_logger = logging.getLogger('tool_logger')
tool_logger.setLevel(logging.DEBUG)

# Создание директории для логов, если она не существует
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Настройка обработчика для вывода в файл
tool_log_file = os.path.join(log_dir, f'tools_debug_{datetime.now().strftime("%Y-%m-%d")}.log')
file_handler = logging.FileHandler(tool_log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
tool_logger.addHandler(file_handler)

tool_logger.info("Загрузка инструментов из новой модульной структуры")

# Импортируем инструменты из нового модульного расположения
try:
    from Source.tools.alert_tools import get_data_alert, analyze_file_alert, fallback_bot_response
    from Source.tools.api_tools import find_endpoint_info
    from Source.tools.gigachat_tools import check_token_status
    
    tool_logger.info("Инструменты успешно импортированы из новой модульной структуры")
except ImportError as e:
    tool_logger.error(f"Ошибка импорта инструментов из новой структуры: {str(e)}")
    # Заглушки на случай проблем с импортом
    def get_data_alert(alert_text):
        return {"error": "Ошибка импорта модуля alert_tools"}
        
    def find_endpoint_info(query):
        return f"Ошибка импорта модуля api_tools: {str(e)}"
        
    def analyze_file_alert(file_path=None):
        return f"Ошибка импорта модуля alert_tools: {str(e)}"
        
    def check_token_status(input_text=""):
        return f"Ошибка импорта модуля gigachat_tools: {str(e)}"
        
    def fallback_bot_response(prompt, max_tokens=1000, alert_data=None):
        return f"Ошибка импорта модуля alert_tools: {str(e)}"

# Убеждаемся, что инструменты доступны
if __name__ == "__main__":
    # Простая проверка доступности инструментов
    print("Проверка доступности инструментов:")
    print(f"get_data_alert: {get_data_alert.__module__}")
    print(f"find_endpoint_info: {find_endpoint_info.__module__}")
    print(f"analyze_file_alert: {analyze_file_alert.__module__}")
    print(f"check_token_status: {check_token_status.__module__}")