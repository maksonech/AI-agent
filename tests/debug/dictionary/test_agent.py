import sys
import io
from src.agents.assistant_agent import get_assistant_agent

# Устанавливаем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Получаем экземпляр агента
agent = get_assistant_agent()

# Тестируем запрос информации об эндпоинте
query = "что за эндпоинт /paramsv2/5.0/configuration/get"
print(f"Запрос: {query}")

# Обрабатываем запрос
response = agent.process_request(query, "test_thread_id")
print(f"Ответ:\n{response}") 