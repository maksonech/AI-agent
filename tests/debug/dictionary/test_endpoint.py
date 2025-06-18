from src.tools.dictionary_tools import search_endpoint

# Тестируем поиск конкретного эндпоинта
result = search_endpoint('/paramsv2/5.0/configuration/get')
print(result) 