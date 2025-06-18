import sys
import io
from src.agents.assistant_agent import get_assistant_agent
from src.tools.dictionary_tools import search_endpoint

# Устанавливаем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Конкретный эндпоинт из вашего примера
endpoint = "/paramsv2/5.0/configuration/get"

# Прямой вызов функции поиска эндпоинта
print(f"Прямой вызов функции search_endpoint:")
print(f"Запрос: {endpoint}")
result = search_endpoint(endpoint)
print(f"Результат:\n{result}")
print("\n" + "-" * 50 + "\n")

# Вызов через агента
agent = get_assistant_agent()
print(f"Вызов через агента:")
query = f"что за эндпоинт {endpoint}"
print(f"Запрос: {query}")
response = agent.process_request(query, "test_thread_id")
print(f"Ответ:\n{response}") 