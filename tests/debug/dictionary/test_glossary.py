import sys
import io
from src.agents.assistant_agent import get_assistant_agent
from src.tools.dictionary_tools import search_glossary

# Устанавливаем кодировку вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Прямой вызов функции поиска в глоссарии
query = "что такое API"
print(f"Прямой вызов функции search_glossary:")
print(f"Запрос: {query}")
result = search_glossary(query)
print(f"Результат:\n{result}")
print("\n" + "-" * 50 + "\n")

# Вызов через агента
agent = get_assistant_agent()
print(f"Вызов через агента:")
print(f"Запрос: {query}")
response = agent.process_request(query, "test_thread_id")
print(f"Ответ:\n{response}") 