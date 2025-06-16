"""
Агент для анализа алертов - специализируется на обработке технических алертов,
их парсинге, анализе и формировании рекомендаций.
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

# Импортируем инструменты для работы с алертами
from src.tools.alert_tools import get_data_alert, analyze_file_alert
from src.alert_processing.alert_parser import parse_alert

# Системный промпт для агента анализа алертов
ALERT_AGENT_SYSTEM_PROMPT = """Ты - опытный инженер по эксплуатации и мониторингу, специалист по анализу алертов.
Твоя задача - проанализировать предоставленный алерт, извлечь из него всю важную информацию,
определить причину проблемы и предложить конкретные шаги для её решения.

При анализе алертов:
1. Структурируй информацию в удобном формате с использованием markdown и эмодзи
2. Выделяй ключевую информацию: ID, сервис, тип ошибки, время, метрики
3. Указывай на возможные причины проблемы, основываясь на данных из алерта
4. Предлагай конкретные действия для проверки и устранения проблемы
5. Оценивай критичность проблемы

Отвечай структурированно, используя следующие разделы:
- Сводка (краткая информация о проблеме)
- Основная информация (ключевые параметры алерта)
- Дополнительные детали (технические подробности)
- Возможные причины (что могло вызвать проблему)
- Рекомендуемые действия (как решить проблему)"""

# Настройка логгера для агента
alert_agent_logger = setup_tool_logger("alert_agent")

class AlertAnalysisAgent:
    """
    Агент для анализа алертов с использованием GigaChat.
    """
    
    def __init__(self):
        """
        Инициализация агента для анализа алертов.
        """
        # Загрузка настроек
        self.settings = get_settings()
        
        # Инициализация менеджера учетных данных
        credentials_manager = CredentialsManager(load_from_env=True)
        gigachat_credentials = credentials_manager.get_gigachat_credentials()
        
        # Инициализация модели GigaChat
        self.model = GigaChat(
            model=self.settings.get("gigachat_model", "GigaChat-2"),
            credentials=gigachat_credentials.get("credentials"),
            scope=gigachat_credentials.get("scope"),
            verify_ssl_certs=gigachat_credentials.get("verify_ssl_certs", False)
        )
        
        # Инициализация агента с инструментами
        self.agent = None
        
        # Логирование информации об инициализации
        alert_agent_logger.info(f"Инициализирован агент анализа алертов, модель: {self.settings.get('gigachat_model', 'GigaChat-2')}")
    
    def _create_agent(self):
        """
        Создает агента с инструментами для анализа алертов.
        
        Returns:
            Агент LangGraph с инструментами
        """
        # Инструменты для анализа алертов
        alert_tools = [get_data_alert, analyze_file_alert]
        
        # Создаем агента с инструментами для анализа алертов
        return create_react_agent(
            model=self.model,
            tools=alert_tools,
            state_modifier=ALERT_AGENT_SYSTEM_PROMPT,
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
    
    def analyze_alert(self, alert_text: str) -> str:
        """
        Анализирует текст алерта и возвращает результат анализа.
        
        Args:
            alert_text: Текст алерта для анализа
            
        Returns:
            Результат анализа алерта
        """
        try:
            # Парсим алерт для получения структурированных данных
            parsed_data = parse_alert(alert_text)
            
            # Формируем запрос к модели с системным промптом
            messages = [
                SystemMessage(content=ALERT_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=f"Проанализируй следующий алерт и предоставь подробный анализ:\n\n{alert_text}")
            ]
            
            # Запрашиваем анализ у модели
            response = self.model.invoke(messages)
            alert_agent_logger.info(f"Получен анализ алерта длиной {len(response.content)} символов")
            
            return response.content
        except Exception as e:
            error_msg = f"Ошибка при анализе алерта: {str(e)}"
            alert_agent_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"
    
    def analyze_alert_file(self, file_path: str) -> str:
        """
        Анализирует алерт из файла.
        
        Args:
            file_path: Путь к файлу с алертом
            
        Returns:
            Результат анализа алерта из файла
        """
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                raise FileOperationError(f"Файл не найден: {file_path}")
            
            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as file:
                alert_text = file.read()
            
            # Анализируем алерт
            return self.analyze_alert(alert_text)
        except Exception as e:
            error_msg = f"Ошибка при анализе файла алерта: {str(e)}"
            alert_agent_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"
    
    def find_solution(self, alert_text: str, additional_context: Optional[str] = None) -> str:
        """
        Поиск решения для проблемы, описанной в алерте.
        
        Args:
            alert_text: Текст алерта
            additional_context: Дополнительный контекст для поиска решения
            
        Returns:
            Предлагаемое решение проблемы
        """
        try:
            # Формируем запрос для поиска решения
            prompt = f"""На основе следующего алерта, предложи детальный план решения проблемы:
            
{alert_text}"""
            
            # Добавляем дополнительный контекст, если он предоставлен
            if additional_context:
                prompt += f"\n\nДополнительный контекст:\n{additional_context}"
            
            # Формируем запрос к модели
            messages = [
                SystemMessage(content=ALERT_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            
            # Запрашиваем решение у модели
            response = self.model.invoke(messages)
            alert_agent_logger.info(f"Получено решение для алерта длиной {len(response.content)} символов")
            
            return response.content
        except Exception as e:
            error_msg = f"Ошибка при поиске решения: {str(e)}"
            alert_agent_logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"

# Создаем глобальный экземпляр агента для анализа алертов
alert_agent = AlertAnalysisAgent()

def get_alert_agent():
    """
    Получает глобальный экземпляр агента для анализа алертов.
    
    Returns:
        Экземпляр AlertAnalysisAgent
    """
    global alert_agent
    return alert_agent

if __name__ == "__main__":
    # Тестирование агента при прямом запуске файла
    agent = get_alert_agent()
    test_alert = """
    ALERT: High CPU Usage
    Service: api-gateway
    Severity: Critical
    Time: 2023-05-15 14:32:45
    Metrics: CPU: 95%, Memory: 87%
    Details: The API Gateway service has been experiencing high CPU usage for the last 15 minutes.
    """
    result = agent.analyze_alert(test_alert)
    print(result) 