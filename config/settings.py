"""
Модуль для работы с настройками приложения.
Хранит и предоставляет доступ к базовым настройкам, таким как пути к файлам,
настройки форматирования и другие параметры.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from .exceptions import ConfigError, FileOperationError, exception_handler

# Настройка базового логгера (для избежания циклической зависимости)
logger = logging.getLogger("settings")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

# Базовые пути приложения
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(APP_ROOT, 'Data')
CONFIG_DIR = os.path.join(APP_ROOT, 'Config')
LOGS_DIR = os.path.join(APP_ROOT, 'Logs')
TEST_ALERTS_DIR = os.path.join(APP_ROOT, 'TestAlerts')

# Пути к файлам настроек
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'Seting.json')  # По историческим причинам файл называется "Seting.json", а не "Settings.json"

# Настройки по умолчанию, если файл не найден
DEFAULT_SETTINGS = {
    "course_data_path": "Data/integration_endpoints.json",
    "glossary_data_path": "Data/architect_glossary.json",
    "default_similarity_threshold": 0.3,
    "gigachat_model": "GigaChat-2",
    "gigachat_auth_url": "https://gigachat.devices.sberbank.ru/api/v1/oauth/token",
    "gigachat_info_url": "https://gigachat.devices.sberbank.ru/api/v1/accounts/info",
    "default_alert_file": "TestAlerts/sample_alert.txt",
    "default_max_tokens": 800
}

# Настройки для выделения различных типов сущностей в тексте
ALERT_FORMAT_SETTINGS = {
    "http_code_pattern": r'HTTP (?:ERROR )?(\d{3})|(\d{3}) POST',
    "alert_id_pattern": r'P-(\d+)',
    "timestamp_patterns": [
        r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})',
        r'(\d{2}:\d{2} \(\w+\) \d{2}\.\d{2}\.\d{4})'
    ]
}

# Кэш настроек для поддержания одного экземпляра
_settings_cache = None

@exception_handler(
    error_message="Ошибка при загрузке настроек",
    logger=logger,
    expected_exceptions=[FileNotFoundError, json.JSONDecodeError]
)
def load_settings() -> Dict[str, Any]:
    """
    Загружает настройки из файла конфигурации.
    Если файл не найден, возвращает настройки по умолчанию.
    
    Returns:
        Dict[str, Any]: Словарь с настройками приложения
        
    Raises:
        ConfigError: Если возникла ошибка при загрузке настроек
    """
    if not os.path.exists(SETTINGS_FILE):
        logger.warning(f"Файл настроек не найден: {SETTINGS_FILE}, используются настройки по умолчанию")
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        # Дополняем загруженные настройки значениями по умолчанию для отсутствующих ключей
        for key, value in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = value
                
        logger.info(f"Настройки успешно загружены из {SETTINGS_FILE}")
        return settings
    except FileNotFoundError:
        raise ConfigError(f"Файл настроек не найден: {SETTINGS_FILE}")
    except json.JSONDecodeError:
        raise ConfigError(f"Ошибка при разборе файла настроек: {SETTINGS_FILE}")
    except Exception as e:
        raise ConfigError(f"Ошибка при загрузке настроек: {str(e)}")

@exception_handler(
    error_message="Ошибка при сохранении настроек",
    logger=logger,
    expected_exceptions=[PermissionError]
)
def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Сохраняет настройки в файл конфигурации.
    
    Args:
        settings: Словарь с настройками для сохранения
        
    Returns:
        bool: True, если сохранение успешно, иначе False
        
    Raises:
        ConfigError: Если возникла ошибка при сохранении настроек
    """
    global _settings_cache
    
    try:
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        
        # Обновляем кэш
        _settings_cache = settings
        logger.info(f"Настройки успешно сохранены в {SETTINGS_FILE}")
        return True
    except PermissionError:
        raise ConfigError(f"Нет доступа для записи в файл настроек: {SETTINGS_FILE}")
    except Exception as e:
        raise ConfigError(f"Ошибка при сохранении настроек: {str(e)}")

def get_settings() -> Dict[str, Any]:
    """
    Получает настройки приложения. Использует кэш для оптимизации.
    
    Returns:
        Dict[str, Any]: Словарь с настройками приложения
    """
    global _settings_cache
    
    if _settings_cache is None:
        _settings_cache = load_settings()
    
    return _settings_cache

def update_setting(key: str, value: Any) -> bool:
    """
    Обновляет конкретную настройку и сохраняет в файл.
    
    Args:
        key: Ключ настройки для обновления
        value: Новое значение
        
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    settings = get_settings()
    settings[key] = value
    logger.info(f"Обновлена настройка {key}: {value}")
    return save_settings(settings)

def get_data_path(relative_path: Optional[str] = None) -> str:
    """
    Возвращает абсолютный путь к файлу данных.
    
    Args:
        relative_path: Относительный путь к файлу данных
        
    Returns:
        str: Абсолютный путь к файлу данных
    """
    if relative_path is None:
        return DATA_DIR
    
    # Если путь уже абсолютный, возвращаем его как есть
    if os.path.isabs(relative_path):
        return relative_path
        
    # Если путь относительный и начинается с "Data/"
    if relative_path.startswith("Data/"):
        relative_path = relative_path[5:]  # Убираем префикс "Data/"
    
    return os.path.join(DATA_DIR, relative_path)

@exception_handler(
    error_message="Ошибка при получении пути к файлу алерта",
    logger=logger,
    expected_exceptions=[FileOperationError]
)
def get_alert_file_path(filename: Optional[str] = None) -> str:
    """
    Возвращает абсолютный путь к файлу алерта.
    
    Args:
        filename: Имя файла алерта или относительный путь
        
    Returns:
        str: Абсолютный путь к файлу алерта
        
    Raises:
        FileOperationError: Если файл не существует или недоступен
    """
    if filename is None:
        # Используем значение из настроек
        settings = get_settings()
        filename = settings.get("default_alert_file", "sample_alert.txt")
    
    # Если путь уже абсолютный, возвращаем его как есть
    if os.path.isabs(filename):
        result_path = filename
    else:
        # Если путь относительный и начинается с "TestAlerts/"
        if filename.startswith("TestAlerts/"):
            filename = filename[11:]  # Убираем префикс "TestAlerts/"
        
        result_path = os.path.join(TEST_ALERTS_DIR, filename)
    
    # Проверяем существование файла
    if not os.path.exists(result_path):
        error_message = f"Файл алерта не найден: {result_path}"
        logger.error(error_message)
        raise FileOperationError(error_message)
    
    return result_path

def get_log_file_path(log_type: str, timestamp: Optional[str] = None) -> str:
    """
    Возвращает абсолютный путь к файлу лога.
    
    Args:
        log_type: Тип лога (например, 'chat', 'tools', 'error')
        timestamp: Временная метка для имени файла (например, '%Y-%m-%d_%H-%M-%S')
        
    Returns:
        str: Абсолютный путь к файлу лога
    """
    from datetime import datetime
    
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y-%m-%d')
    
    log_filename = f"{log_type}_{timestamp}.log"
    
    # Создаем директорию, если она не существует
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    return os.path.join(LOGS_DIR, log_filename)

def get_format_settings() -> Dict[str, Any]:
    """
    Возвращает настройки форматирования для анализа алертов.
    
    Returns:
        Dict[str, Any]: Словарь с настройками форматирования
    """
    return ALERT_FORMAT_SETTINGS 