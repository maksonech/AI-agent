import os
import sys

# Добавляем корневую директорию проекта в путь для импорта при прямом запуске файла
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Dict, List, Any, Optional, Union, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from src.core.prompts import system_prompt  # Изменено с Source на src

# Импортируем инструменты из новой модульной структуры
try:
    # Импортируем только то, что не вызовет циклического импорта
    # alert_tools будем импортировать позже внутри функций
    from src.tools.api_tools import find_endpoint_info
    from src.tools.gigachat_tools import check_token_status
except ImportError:
    # Резервный импорт
    from src.tools import find_endpoint_info, check_token_status

# Импортируем конфигурационные модули
try:
    from config import get_settings, CredentialsManager
    from config.logging_config import setup_tool_logger
except ImportError:
    # Резервный импорт, если не получилось импортировать из корневого конфига
    from src.config import get_settings, CredentialsManager
    from src.config.logging_config import setup_tool_logger

# Загрузка переменных окружения и получение настроек
load_dotenv()
settings: Dict[str, Any] = get_settings()

# Инициализация менеджера учетных данных
credentials_manager: CredentialsManager = CredentialsManager(load_from_env=True)
gigachat_credentials: Dict[str, Any] = credentials_manager.get_gigachat_credentials()

# Инициализация модели GigaChat с настройками из централизованной конфигурации
model: GigaChat = GigaChat(
    model=settings.get("gigachat_model", "GigaChat-2"),
    credentials=gigachat_credentials.get("credentials"),
    scope=gigachat_credentials.get("scope"),
    verify_ssl_certs=gigachat_credentials.get("verify_ssl_certs", False)
)

# Настройка логгера для агента
agent_logger = setup_tool_logger("agent")

# Логирование информации об инициализации
agent_logger.info(f"Инициализирована модель GigaChat, модель: {settings.get('gigachat_model', 'GigaChat-2')}")
agent_logger.info(f"Учетные данные: {gigachat_credentials.get('credentials')[:5]}...{gigachat_credentials.get('credentials')[-5:] if gigachat_credentials.get('credentials') else 'None'}")
agent_logger.info(f"Scope: {gigachat_credentials.get('scope')}")

def get_bot_response(prompt: str, max_tokens: Optional[int] = None, alert_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Функция для получения ответа от бота на основе переданного промпта с возможным
    использованием структурированных данных алерта для углубленного анализа.
    
    Args:
        prompt: Текст запроса к боту
        max_tokens: Максимальное количество токенов в ответе
        alert_data: Словарь с структурированными данными об алерте (опционально)
        
    Returns:
        Ответ бота с углубленным анализом
    """
    try:
        # Если max_tokens не указан, берем из настроек
        if max_tokens is None:
            max_tokens = settings.get("default_max_tokens", 500)
            
        # Добавляем системный промпт для улучшения анализа алертов
        if "алерт" in prompt.lower() or "alert" in prompt.lower():
            system_message: str = """Ты - опытный инженер по эксплуатации и мониторингу, специалист по анализу алертов.
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
        else:
            system_message: str = "Ты - полезный ассистент, отвечающий на вопросы пользователя."
            
        enhanced_prompt: str = prompt
        
        # Если предоставлены структурированные данные, дополняем запрос
        if alert_data:
            additional_context: str = "\n\nКраткая информация об алерте:\n"
            
            # Добавляем только самые важные технические детали
            if alert_data.get('status'):
                additional_context += f"- Статус: {alert_data['status']}\n"
            
            if alert_data.get('http_code'):
                additional_context += f"- HTTP код: {alert_data['http_code']}\n"
                
            if alert_data.get('service'):
                additional_context += f"- Сервис: {alert_data['service']}\n"
                
            enhanced_prompt += additional_context
        
        agent_logger.info(f"Запрос к боту: {enhanced_prompt[:100]}...")
        
        # Вызываем модель с расширенным промптом и системным сообщением
        messages: List[Union[SystemMessage, HumanMessage]] = [
            SystemMessage(content=system_message),
            HumanMessage(content=enhanced_prompt)
        ]
        
        response = model.invoke(messages)
        agent_logger.info(f"Получен ответ от бота длиной {len(response.content)} символов")
        
        return response.content
    except Exception as e:
        error_msg: str = f"Ошибка анализа: {str(e)}"
        agent_logger.error(error_msg, exc_info=True)
        return error_msg


# Функция для создания агента с инструментами
def create_agent():
    """
    Создает агента с полным набором инструментов.
    Выделено в отдельную функцию для предотвращения циклического импорта.
    
    Returns:
        Агент LangGraph с инструментами
    """
    # Базовые инструменты
    available_tools = [find_endpoint_info, check_token_status]
    
    # Пытаемся импортировать дополнительные инструменты
    try:
        # Импортируем только когда функция вызвана
        from src.tools.alert_tools import get_data_alert, analyze_file_alert
        available_tools.extend([get_data_alert, analyze_file_alert])
    except ImportError as e:
        agent_logger.error(f"Не удалось импортировать инструменты из alert_tools: {str(e)}")
    
    # Создаем агента с доступными инструментами
    return create_react_agent(
        model=model,
        tools=available_tools,
        state_modifier=system_prompt,
        checkpointer=MemorySaver()
    )

# Инициализируем агента только когда он нужен
agent = None

def get_agent():
    """
    Получает агента, создавая его при первом вызове.
    
    Returns:
        Агент LangGraph
    """
    global agent
    if agent is None:
        agent = create_agent()
    return agent

def chat(thread_id: str) -> None:
    """
    Функция для общения с агентом через консоль.
    
    Args:
        thread_id: Идентификатор потока беседы
    """
    print(f"Начинаем чат с thread_id: {thread_id}")
    # Получаем агента при необходимости
    agent = get_agent()
    # Здесь бы был код чат-интерфейса

if __name__ == "__main__":
    chat('SberAX_consultant') 