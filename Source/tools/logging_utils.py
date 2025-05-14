"""
Модуль для настройки логирования инструментов.
"""
import os
import logging
from datetime import datetime

def setup_tool_logger(logger_name='tool_logger'):
    """
    Настраивает и возвращает логгер для инструментов.
    
    Args:
        logger_name: Имя логгера (по умолчанию 'tool_logger')
        
    Returns:
        logging.Logger: Настроенный объект логгера
    """
    # Создаем логгер если он еще не существует
    tool_logger = logging.getLogger(logger_name)
    
    # Проверяем, если логгер уже настроен (имеет обработчики)
    if tool_logger.handlers:
        return tool_logger
        
    # Настраиваем уровень логирования
    tool_logger.setLevel(logging.DEBUG)
    
    # Создание директории для логов, если она не существует
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Logs')
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
    
    return tool_logger

# Создаем и экспортируем логгер для использования в модулях инструментов
tool_logger = setup_tool_logger() 