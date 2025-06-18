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
        
        # Инициализация модели GigaChat с использованием централизованной функции
        self.model = initialize_gigachat_model()
        
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
            
            return self._add_model_info(response.content)
        except Exception as e:
            error_msg = f"Ошибка при анализе алерта: {str(e)}"
            alert_agent_logger.error(error_msg, exc_info=True)
            return self._add_model_info(f"❌ {error_msg}")
    
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
            
            # Пробуем различные кодировки для чтения файла
            encodings = ['utf-8', 'cp1251', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin1']
            alert_text = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        alert_text = file.read()
                    alert_agent_logger.info(f"Файл успешно прочитан с кодировкой: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            # Если не удалось прочитать файл ни в одной кодировке, пробуем бинарное чтение
            if alert_text is None:
                try:
                    with open(file_path, 'rb') as file:
                        binary_data = file.read()
                        # Пробуем определить кодировку по BOM
                        if binary_data.startswith(b'\xff\xfe'):
                            alert_text = binary_data.decode('utf-16-le')
                        elif binary_data.startswith(b'\xfe\xff'):
                            alert_text = binary_data.decode('utf-16-be')
                        elif binary_data.startswith(b'\xef\xbb\xbf'):
                            alert_text = binary_data.decode('utf-8-sig')
                        else:
                            # Последняя попытка - декодирование как latin1 (всегда работает)
                            alert_text = binary_data.decode('latin1')
                    alert_agent_logger.info("Файл успешно прочитан с бинарным определением кодировки")
                except Exception as e:
                    raise FileOperationError(f"Не удалось прочитать файл ни в одной кодировке: {str(e)}")
            
            if not alert_text:
                raise FileOperationError("Файл пуст или не удалось определить кодировку")
            
            # Анализируем алерт
            return self.analyze_alert(alert_text)
        except Exception as e:
            error_msg = f"Ошибка при анализе файла алерта: {str(e)}"
            alert_agent_logger.error(error_msg, exc_info=True)
            return self._add_model_info(f"❌ {error_msg}")
    
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
            
            return self._add_model_info(response.content)
        except Exception as e:
            error_msg = f"Ошибка при поиске решения: {str(e)}"
            alert_agent_logger.error(error_msg, exc_info=True)
            return self._add_model_info(f"❌ {error_msg}")
    
    def _add_model_info(self, response: str) -> str:
        """
        Добавляет информацию о модели GigaChat к ответу.
        
        Args:
            response: Исходный ответ
            
        Returns:
            Ответ с добавленной информацией о модели
        """
        if response:
            # Добавляем информацию в конец ответа
            from config.settings import get_settings
            settings = get_settings()
            model_name = settings.get("gigachat_model", "GigaChat")
            return f"{response}\n\n_Ответ сформирован с помощью модели {model_name}_"
        return response

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