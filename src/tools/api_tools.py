"""
Модуль для работы с API эндпоинтами.
Содержит инструменты для поиска информации об API эндпоинтах.
"""
from langchain.tools import Tool
from src.core.utils import courses_database  # Импортируем обработанный JSON с эндпоинтами
from .logging_utils import tool_logger

def find_endpoint_info(query: str) -> str:
    """
    Поиск информации об API эндпоинтах по запросу пользователя.
    Использует данные из integration_endpoints.json для формирования ответа.
    
    Args:
        query: Строка запроса для поиска эндпоинтов
        
    Returns:
        str: Отформатированная информация о найденных эндпоинтах
    """
    matching_endpoints = []
    
    # Очистка запроса от лишних символов и приведение к нижнему регистру
    query = query.lower().strip()
    
    tool_logger.info(f"Поиск API эндпоинтов по запросу: '{query}'")
    
    # Поиск по эндпоинтам
    for endpoint in courses_database:
        # Проверка по URL пути
        if query in endpoint.get("request", "").lower():
            matching_endpoints.append(endpoint)
            continue
            
        # Проверка по описанию
        if query in endpoint.get("description", "").lower():
            matching_endpoints.append(endpoint)
            continue
            
        # Проверка по хосту
        if query in endpoint.get("host", "").lower():
            matching_endpoints.append(endpoint)
            continue
    
    # Если найдены подходящие эндпоинты, формируем ответ
    if matching_endpoints:
        result = "Найдены следующие API эндпоинты, соответствующие запросу:\n\n"
        
        for i, endpoint in enumerate(matching_endpoints, 1):
            result += f"{i}. Запрос: {endpoint.get('request', 'Нет данных')}\n"
            result += f"   Описание: {endpoint.get('description', 'Нет описания')}\n"
            result += f"   Хост: {endpoint.get('host', 'Не указан')}\n"
            result += f"   Направление: {endpoint.get('direction', 'Не указано')}\n\n"
        
        tool_logger.info(f"Найдено {len(matching_endpoints)} эндпоинтов по запросу '{query}'")
        return result
    else:
        tool_logger.info(f"Не найдено эндпоинтов по запросу '{query}'")
        return "По вашему запросу не найдено API эндпоинтов. Попробуйте уточнить запрос или использовать другие ключевые слова."

# Создаем инструмент для поиска информации об API эндпоинтах
find_endpoint_info_tool = Tool(
    name="API Endpoint Info",
    func=find_endpoint_info,
    description="Ищу информацию об API эндпоинтах по запросу пользователя."
)

# Экспортируем инструмент
find_endpoint_info = find_endpoint_info_tool 