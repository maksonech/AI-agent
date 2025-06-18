"""Этот модуль будет хранить вспомогательный код для агента"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Импортируем модель GigaChat
try:
    from langchain_gigachat.chat_models import GigaChat
except ImportError:
    # Если не удалось импортировать, добавляем заглушку для типизации
    class GigaChat:
        pass

# Определение корневого пути проекта
root_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Загрузка файла настроек
def load_settings(settings_path: str) -> Dict[str, Any]:
    """Загружает файл с настройками из указанного пути."""
    with open(settings_path, 'r', encoding='utf-8', errors='replace') as file:
        return json.load(file)

# Путь к файлу настроек
settings_path: str = os.path.join(root_dir, 'config/settings.json')
settings: Dict[str, Any] = load_settings(settings_path)

# Загрузка базы данных курсов
def load_database(file_path: str) -> List[Dict[str, Any]]:
    """Загружает базу данных курсов в формате JSON."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Путь к базе данных курсов из settings.json
course_data_path: str = os.path.join(root_dir, settings.get("course_data_path", "data/courses.json"))
courses_database: List[Dict[str, Any]] = load_database(course_data_path)

def initialize_gigachat_model() -> GigaChat:
    """
    Централизованная инициализация модели GigaChat с настройками из конфигурации.
    
    Returns:
        GigaChat: Инициализированная модель GigaChat
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Импортируем зависимости для получения настроек и учетных данных
    try:
        from config import get_settings, CredentialsManager
    except ImportError:
        from src.config import get_settings, CredentialsManager
        
    # Получаем настройки
    settings = get_settings()
    
    # Инициализируем менеджер учетных данных
    credentials_manager = CredentialsManager(load_from_env=True)
    gigachat_credentials = credentials_manager.get_gigachat_credentials()
    
    # Инициализируем модель GigaChat
    model = GigaChat(
        model=settings.get("gigachat_model", "GigaChat-2"),
        credentials=gigachat_credentials.get("credentials"),
        scope=gigachat_credentials.get("scope"),
        verify_ssl_certs=gigachat_credentials.get("verify_ssl_certs", False)
    )
    
    return model



