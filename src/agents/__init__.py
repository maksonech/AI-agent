"""
Пакет с агентами для обработки различных типов запросов.
"""

from src.agents.alert_agent import get_alert_agent, AlertAnalysisAgent
from src.agents.assistant_agent import get_assistant_agent, AssistantAgent

__all__ = [
    'get_alert_agent', 'AlertAnalysisAgent',
    'get_assistant_agent', 'AssistantAgent',
] 