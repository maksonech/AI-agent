"""
Интерактивный ассистент - агент для обработки пользовательских запросов,
поиска в документации и координации взаимодействия с пользователем.
"""
import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union

# Добавляем корневую директорию проекта в путь для импорта при прямом запуске файла
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Импортируем утилиты для централизованной инициализации модели
from src.core.utils import initialize_gigachat_model

# Импортируем конфигурационные модули
try:
    from config import get_settings, CredentialsManager
    from config.logging_config import setup_tool_logger
    from config.exceptions import (
        AIAgentError, FileOperationError, GigaChatAPIError, DataProcessingError,
        format_exception, safe_execute
    )
except ImportError:
    # Резервный импорт, если не получилось импортировать из корневого конфига
    from src.config import get_settings, CredentialsManager
    from src.config.logging_config import setup_tool_logger
    from src.config.exceptions import (
        AIAgentError, FileOperationError, GigaChatAPIError, DataProcessingError,
        format_exception, safe_execute
    )

# Импортируем инструменты для работы с API
from src.tools.api_tools import find_endpoint_info
from src.tools.gigachat_tools import check_token_status
# Импортируем инструменты для работы со словарями
from src.tools.dictionary_tools import search_glossary_tool, search_endpoint_tool

# Системный промпт для интерактивного ассистента
ASSISTANT_SYSTEM_PROMPT = """Ты - интеллектуальный ассистент, помогающий пользователям с техническими вопросами.
Твоя задача - обеспечить максимально полезную и точную информацию, отвечать на вопросы пользователя
и помогать в решении технических задач.

При ответе на вопросы:
1. Используй структурированный формат с markdown для лучшей читаемости
2. Предоставляй конкретные и точные ответы, основанные на имеющейся информации
3. Если запрос касается API или технических деталей, используй инструменты для поиска информации
4. Если не знаешь ответ, честно признай это и предложи альтернативные источники информации
5. При необходимости запрашивай дополнительную информацию для уточнения запроса

Ты можешь:
- Отвечать на общие вопросы пользователей
- Искать информацию об API-эндпоинтах
- Проверять статус токенов GigaChat
- Искать определения терминов в глоссарии
- Перенаправлять запросы по анализу алертов специализированному агенту"""

# Настройка логгера для ассистента
assistant_logger = setup_tool_logger("assistant_agent")

class AssistantAgent:
    """
    Интерактивный ассистент для обработки пользовательских запросов.
    """
    
    def __init__(self):
        """
        Инициализация интерактивного ассистента.
        """
        # Загрузка настроек
        self.settings = get_settings()
        
        # Инициализация модели GigaChat с использованием централизованной функции
        self.model = initialize_gigachat_model()
        
        # Инициализация агента с инструментами
        self.agent = None
        
        # Логирование информации об инициализации
        assistant_logger.info(f"Инициализирован интерактивный ассистент, модель: {self.settings.get('gigachat_model', 'GigaChat-2')}")
    
    def _create_agent(self):
        """
        Создает агента с инструментами для обработки пользовательских запросов.
        
        Returns:
            Агент LangGraph с инструментами
        """
        # Инструменты для интерактивного ассистента
        assistant_tools = [
            find_endpoint_info, 
            check_token_status,
            search_glossary_tool,
            search_endpoint_tool
        ]
        
        # Создаем агента с инструментами для интерактивного ассистента
        return create_react_agent(
            model=self.model,
            tools=assistant_tools,
            state_modifier=ASSISTANT_SYSTEM_PROMPT,
            checkpointer=MemorySaver()
        )
    
    def get_agent(self):
        """
        Получает агента, создавая его при первом вызове.
        
        Returns:
            Агент LangGraph
        """
        if self.agent is None:
            self.agent = self._create_agent()
        return self.agent
    
    def process_request(self, user_input: str, thread_id: str) -> str:
        """
        Обрабатывает запрос пользователя и возвращает ответ.
        
        Args:
            user_input: Запрос пользователя
            thread_id: Идентификатор потока беседы
            
        Returns:
            Ответ на запрос пользователя
        """
        try:
            # Проверяем, не является ли запрос запросом на анализ алерта
            if any(keyword in user_input.lower() for keyword in ["алерт", "alert", "анализ", "проблема"]):
                assistant_logger.info(f"Запрос на анализ алерта перенаправлен специализированному агенту: {user_input[:50]}...")
                return self._redirect_to_alert_agent(user_input)
            
            # Проверяем, не является ли запрос запросом на поиск термина в глоссарии
            if any(pattern in user_input.lower() for pattern in ["что такое", "что означает", "значение термина", "определение"]):
                assistant_logger.info(f"Запрос на поиск термина в глоссарии: {user_input[:50]}...")
                return search_glossary_tool.func(user_input)
            
            # Проверяем, не является ли запрос запросом на поиск информации о ссылке или API
            if any(pattern in user_input.lower() for pattern in ["что за ссылка", "что за api", "что за эндпоинт", "информация о ссылке", "api endpoint"]):
                assistant_logger.info(f"Запрос на поиск информации о ссылке или API: {user_input[:50]}...")
                return search_endpoint_tool.func(user_input)
            
            # Получаем агента
            agent = self.get_agent()
            
            # Конфигурация для агента
            config = {"configurable": {"thread_id": thread_id}}
            
            # Отправляем запрос агенту
            response = agent.invoke({"messages": [("user", user_input)]}, config=config)
            
            assistant_logger.info(f"Обработан запрос пользователя длиной {len(user_input)} символов")
            
            # Извлекаем ответ из результата
            if "output" in response:
                return response["output"]
            else:
                return "Не удалось получить ответ от агента."
        except Exception as e:
            error_msg = f"Ошибка при обработке запроса: {str(e)}"
            assistant_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"
    
    def _redirect_to_alert_agent(self, user_input: str) -> str:
        """
        Перенаправляет запрос специализированному агенту для анализа алертов.
        
        Args:
            user_input: Запрос пользователя
            
        Returns:
            Ответ от агента анализа алертов
        """
        try:
            # Импортируем агента анализа алертов только при необходимости
            from src.agents.alert_agent import get_alert_agent
            
            # Получаем агента анализа алертов
            alert_agent = get_alert_agent()
            
            # Проверяем, содержит ли запрос текст алерта
            if "ALERT:" in user_input or "алерт:" in user_input.lower():
                # Если запрос содержит текст алерта, анализируем его напрямую
                return alert_agent.analyze_alert(user_input)
            else:
                # Иначе отвечаем, что для анализа алерта нужен текст алерта
                return """Для анализа алерта мне нужен текст алерта. 
                
Вы можете:
1. Ввести текст алерта напрямую
2. Использовать команду 'файл' или 'анализ файла алерта' для выбора файла с алертом
3. Указать путь к файлу с алертом"""
        except ImportError:
            return "Не удалось перенаправить запрос агенту анализа алертов. Модуль не найден."
        except Exception as e:
            error_msg = f"Ошибка при перенаправлении запроса: {str(e)}"
            assistant_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"
    
    def search_documentation(self, query: str) -> str:
        """
        Поиск информации в документации по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Найденная информация
        """
        try:
            # Формируем запрос к модели
            messages = [
                SystemMessage(content=f"{ASSISTANT_SYSTEM_PROMPT}\nОтвечай на вопросы пользователя, используя доступную документацию."),
                HumanMessage(content=f"Найди информацию по запросу: {query}")
            ]
            
            # Запрашиваем информацию у модели
            response = self.model.invoke(messages)
            assistant_logger.info(f"Выполнен поиск в документации по запросу: {query}")
            
            return response.content
        except Exception as e:
            error_msg = f"Ошибка при поиске в документации: {str(e)}"
            assistant_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"
    
    def check_api_endpoint(self, endpoint: str) -> str:
        """
        Проверяет информацию об API-эндпоинте.
        
        Args:
            endpoint: Название или путь эндпоинта
            
        Returns:
            Информация об эндпоинте
        """
        try:
            # Используем инструмент для поиска информации об эндпоинте
            result = find_endpoint_info.invoke(endpoint)
            assistant_logger.info(f"Получена информация об API-эндпоинте: {endpoint}")
            
            return result
        except Exception as e:
            error_msg = f"Ошибка при поиске информации об API-эндпоинте: {str(e)}"
            assistant_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"

# Создаем глобальный экземпляр интерактивного ассистента
assistant_agent = AssistantAgent()

def get_assistant_agent():
    """
    Получает глобальный экземпляр интерактивного ассистента.
    
    Returns:
        Экземпляр AssistantAgent
    """
    global assistant_agent
    return assistant_agent

if __name__ == "__main__":
    # Тестирование ассистента при прямом запуске файла
    agent = get_assistant_agent()
    test_request = "Расскажи о возможностях API GigaChat"
    result = agent.process_request(test_request, "test_thread_id")
    print(result) 