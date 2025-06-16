"""
Модуль для работы со словарями и справочниками.
Содержит инструменты для поиска информации в глоссарии и справочнике API-эндпоинтов.
"""
import os
import json
import re
from typing import Dict, List, Any, Optional, Union
from langchain.tools import Tool

# Импортируем конфигурационные модули
try:
    from config.logging_config import setup_tool_logger
    from config.exceptions import (
        DataProcessingError, FileOperationError,
        exception_handler, format_exception
    )
    from config import get_settings
except ImportError:
    # Резервный импорт, если не получилось импортировать из корневого конфига
    from src.config.logging_config import setup_tool_logger
    from src.config.exceptions import (
        DataProcessingError, FileOperationError,
        exception_handler, format_exception
    )
    from src.config import get_settings

# Инициализируем логгер
dictionary_logger = setup_tool_logger("dictionary_tools")

# Пути к файлам словарей
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(APP_ROOT, 'data')
GLOSSARY_FILE = os.path.join(DATA_DIR, 'architect_glossary.json')
ENDPOINTS_FILE = os.path.join(DATA_DIR, 'integration_endpoints.json')

@exception_handler(
    error_message="Ошибка при загрузке словаря",
    logger=dictionary_logger,
    expected_exceptions=[FileNotFoundError, json.JSONDecodeError]
)
def load_dictionary(file_path: str) -> List[Dict[str, Any]]:
    """
    Загружает словарь из JSON-файла.
    
    Args:
        file_path: Путь к файлу словаря
        
    Returns:
        Список записей словаря
        
    Raises:
        FileOperationError: Если файл не существует или недоступен
        DataProcessingError: Если возникла ошибка при обработке данных
    """
    try:
        if not os.path.exists(file_path):
            raise FileOperationError(f"Файл словаря не найден: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            dictionary = json.load(f)
            
        dictionary_logger.info(f"Словарь успешно загружен из {file_path}, {len(dictionary)} записей")
        return dictionary
    except json.JSONDecodeError:
        raise DataProcessingError(f"Ошибка при разборе файла словаря: {file_path}")
    except Exception as e:
        raise DataProcessingError(f"Ошибка при загрузке словаря: {str(e)}")

@exception_handler(
    error_message="Ошибка при поиске в глоссарии",
    logger=dictionary_logger,
    expected_exceptions=[DataProcessingError]
)
def search_glossary(query: str) -> str:
    """
    Ищет термин в глоссарии.
    
    Args:
        query: Поисковый запрос
        
    Returns:
        Найденная информация о термине или сообщение, что термин не найден
    """
    try:
        # Загружаем глоссарий
        glossary = load_dictionary(GLOSSARY_FILE)
        
        # Нормализуем запрос
        query = query.lower().strip()
        
        # Проверяем, является ли запрос прямым вопросом о термине
        term_match = re.search(r'что (?:такое|означает|значит)(?: термин| понятие)? ["\']?([^"\'?]+)["\']?', query.lower())
        if term_match:
            query = term_match.group(1).strip()
        
        # Ищем точное совпадение
        exact_matches = [item for item in glossary if item["term"].lower() == query]
        if exact_matches:
            result = []
            for match in exact_matches:
                result.append(f"**{match['term']}**: {match['description']}")
            return "\n\n".join(result)
        
        # Ищем частичное совпадение
        partial_matches = [item for item in glossary if query in item["term"].lower()]
        if partial_matches:
            result = ["Найдены похожие термины:"]
            for match in partial_matches[:5]:  # Ограничиваем количество результатов
                result.append(f"**{match['term']}**: {match['description']}")
            return "\n\n".join(result)
        
        return f"Термин '{query}' не найден в глоссарии."
    except Exception as e:
        dictionary_logger.error(f"Ошибка при поиске в глоссарии: {str(e)}", exc_info=True)
        return f"Ошибка при поиске в глоссарии: {str(e)}"

@exception_handler(
    error_message="Ошибка при поиске API-эндпоинта",
    logger=dictionary_logger,
    expected_exceptions=[DataProcessingError]
)
def search_endpoint(query: str) -> str:
    """
    Ищет информацию об API-эндпоинте.
    
    Args:
        query: Поисковый запрос (часть URL или описания)
        
    Returns:
        Найденная информация об API-эндпоинте или сообщение, что эндпоинт не найден
    """
    try:
        # Загружаем справочник эндпоинтов
        endpoints = load_dictionary(ENDPOINTS_FILE)
        
        # Нормализуем запрос
        query = query.lower().strip()
        
        # Проверяем, является ли запрос прямым вопросом о ссылке
        url_match = re.search(r'что (?:такое|означает|значит|за)(?: ссылка| эндпоинт| url| api)? ["\']?([^"\'?]+)["\']?', query.lower())
        if url_match:
            query = url_match.group(1).strip()
        
        # Ищем по URL (request)
        url_matches = [item for item in endpoints if query in item["request"].lower()]
        
        # Если не нашли по URL, ищем по описанию
        if not url_matches:
            url_matches = [item for item in endpoints if "description" in item and query in item["description"].lower()]
        
        if url_matches:
            result = ["Найдена информация о следующих API-эндпоинтах:"]
            for match in url_matches[:5]:  # Ограничиваем количество результатов
                result.append(f"**Запрос**: {match['request']}")
                if match.get("host"):
                    result.append(f"**Хост**: {match['host']}")
                if match.get("direction"):
                    result.append(f"**Направление**: {match['direction']}")
                if match.get("description"):
                    result.append(f"**Описание**: {match['description']}")
                result.append("")  # Пустая строка между записями
            return "\n".join(result)
        
        return f"API-эндпоинт или информация по запросу '{query}' не найдены."
    except Exception as e:
        dictionary_logger.error(f"Ошибка при поиске API-эндпоинта: {str(e)}", exc_info=True)
        return f"Ошибка при поиске API-эндпоинта: {str(e)}"

# Создаем инструмент для поиска в глоссарии
search_glossary_tool = Tool(
    name="search_glossary",
    description="Поиск термина в глоссарии. Используйте этот инструмент, когда нужно найти определение термина.",
    func=search_glossary
)

# Создаем инструмент для поиска API-эндпоинтов
search_endpoint_tool = Tool(
    name="search_endpoint",
    description="Поиск информации об API-эндпоинте. Используйте этот инструмент, когда нужно найти информацию о ссылке или API.",
    func=search_endpoint
)

if __name__ == "__main__":
    # Тестирование инструментов при прямом запуске файла
    print("Тестирование поиска в глоссарии:")
    print(search_glossary("Искусственный интеллект"))
    print("\nТестирование поиска API-эндпоинтов:")
    print(search_endpoint("/api/webchat")) 