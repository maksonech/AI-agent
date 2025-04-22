"""
Тестовый скрипт для проверки функции analyze_file_alert
"""
import os
import sys
import logging
import time
import traceback

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_script')

# Добавляем директорию проекта в пути поиска модулей
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Импорт функции форматирования алерта
try:
    from Source.alert_formatter import format_alert_to_one_line
    logger.info("Функция форматирования алерта успешно импортирована")
except ImportError as e:
    logger.error(f"Ошибка импорта функции форматирования алерта: {str(e)}")
    format_alert_to_one_line = None

def create_test_file_with_multiple_alerts():
    """
    Создает тестовый файл с несколькими алертами разных статусов,
    если файл не существует. Если файл существует, использует его.
    """
    file_path = os.path.join(project_dir, 'TestAlerts/multiple_alerts.txt')
    
    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        logger.info(f"Используем существующий файл с несколькими алертами: {file_path}")
        return file_path
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            # Первый алерт (OPEN)
            f.write("""ПРОМ | АС Рефлекс OPEN P-250443890 | Уровень CUSTOM_ALERT ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий on Web request service default web request ----- ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий: OPEN Custom Alert P-250443890 in environment Sber PROM2 Problem detected at: 22:39 (MSK) 12.04.2025 - 22:43 (MSK) 12.04.2025 (was open for 4 min) 1 impacted service Web request service default web request ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий The CI03467697_CI03474496_WS_LP-traffic_count_failed value was above normal behavior -общий. ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР, WS_LP PROM 001 - console.ar426hj5.k8s.ca.sbrf.ru PROM 002 - console.ar2qob4m.k8s.ca.sbrf.ru Request: Dimension=/paramsv2/5.0/configuration/get 503 POST , dt.entity.service.name=default web request, dt.entity.service=SERVICE-DFB13954956393AE Stand: default web request threshold: 15 Root cause Based on our dependency analysis all incidents are part of the same overall problem.\n\n""")
            
            # Второй алерт (RESOLVED)
            f.write("""ПРОМ | АС Рефлекс RESOLVED P-250443891 | Уровень CUSTOM_ALERT ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий on Web request service default web request ----- ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий: RESOLVED Custom Alert P-250443891 in environment Sber PROM2 Problem detected at: 23:10 (MSK) 12.04.2025 - 23:15 (MSK) 12.04.2025 (was open for 5 min) 1 impacted service Web request service default web request ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий The CI03467697_CI03474496_WS_LP-traffic_count_failed value was above normal behavior -общий. ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР, WS_LP PROM 001 - console.ar426hj5.k8s.ca.sbrf.ru PROM 002 - console.ar2qob4m.k8s.ca.sbrf.ru Request: Dimension=/api/startpage/v1/getStartPage 404 GET , dt.entity.service.name=default web request, dt.entity.service=SERVICE-DFB13954956393AE Stand: default web request threshold: 15 Root cause Based on our dependency analysis all incidents are part of the same overall problem.\n\n""")
            
            # Третий алерт (ACTIVE)
            f.write("""ПРОМ | АС Рефлекс ACTIVE P-250443892 | Уровень CUSTOM_ALERT ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий on Web request service default web request ----- ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий: ACTIVE Custom Alert P-250443892 in environment Sber PROM2 Problem detected at: 01:22 (MSK) 13.04.2025 - 01:30 (MSK) 13.04.2025 (was open for 8 min) 1 impacted service Web request service default web request ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий The CI03467697_CI03474496_WS_LP-traffic_count_failed value was above normal behavior -общий. ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР, WS_LP PROM 001 - console.ar426hj5.k8s.ca.sbrf.ru PROM 002 - console.ar2qob4m.k8s.ca.sbrf.ru Request: Dimension=/api/rating/v1/state 500 POST , dt.entity.service.name=default web request, dt.entity.service=SERVICE-DFB13954956393AE Stand: default web request threshold: 15 Root cause Based on our dependency analysis all incidents are part of the same overall problem.""")
        
        logger.info(f"Создан тестовый файл с несколькими алертами: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Ошибка при создании тестового файла: {str(e)}")
        return None

def prepare_one_line_alert():
    """
    Подготавливает однострочный алерт из sample_alert.txt, если имеется.
    Возвращает путь к файлу с однострочным алертом.
    """
    sample_alert_path = os.path.join(project_dir, 'TestAlerts/sample_alert.txt')
    one_line_alert_path = os.path.join(project_dir, 'TestAlerts/one_line_alert.txt')
    
    # Проверяем существование директории и создаем, если не существует
    os.makedirs(os.path.dirname(one_line_alert_path), exist_ok=True)
    
    # Если функция форматирования доступна и существует файл sample_alert.txt,
    # преобразуем его в однострочный формат
    if format_alert_to_one_line and os.path.exists(sample_alert_path):
        logger.info(f"Выполняем преобразование файла {sample_alert_path} в однострочный формат")
        try:
            success = format_alert_to_one_line(sample_alert_path, one_line_alert_path)
            if success:
                logger.info(f"Алерт успешно преобразован в однострочный формат: {one_line_alert_path}")
                return one_line_alert_path
            else:
                logger.warning("Не удалось преобразовать алерт в однострочный формат")
        except Exception as e:
            logger.error(f"Ошибка при преобразовании алерта: {str(e)}", exc_info=True)
    
    # Если файл one_line_alert.txt уже существует, используем его
    if os.path.exists(one_line_alert_path):
        logger.info(f"Используем существующий файл с однострочным алертом: {one_line_alert_path}")
        return one_line_alert_path
    
    # Если ничего не помогло, создаем файл с базовым алертом
    logger.warning("Создаем файл с базовым однострочным алертом")
    try:
        with open(one_line_alert_path, 'w', encoding='utf-8') as f:
            f.write("ПРОМ | АС Рефлекс RESOLVED P-250443890 | Уровень CUSTOM_ALERT ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий on Web request service default web request ----- ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий: RESOLVED Custom Alert P-250443890 in environment Sber PROM2 Problem detected at: 22:39 (MSK) 12.04.2025 - 22:43 (MSK) 12.04.2025 (was open for 4 min) 1 impacted service Web request service default web request")
        logger.info(f"Создан базовый файл с однострочным алертом: {one_line_alert_path}")
        return one_line_alert_path
    except Exception as e:
        logger.error(f"Ошибка при создании базового файла с алертом: {str(e)}", exc_info=True)
        return None

def test_file_analyzer(test_multi_alerts=False):
    """
    Вызывает функцию analyze_file_alert и выводит результат
    """
    print("====================================================")
    print("Запускаем тестирование функции analyze_file_alert...")
    print("====================================================\n")
    
    # Импорт функции analyze_file_alert внутри функции
    # для предотвращения проблем с циклическим импортом
    try:
        from Source.tools import analyze_file_alert
    except ImportError as e:
        print(f"❌ Ошибка импорта: {str(e)}")
        logger.exception("Ошибка при импорте функции analyze_file_alert")
        return
    
    # Определяем путь к файлу для анализа
    if test_multi_alerts:
        file_path = create_test_file_with_multiple_alerts()
        if not file_path:
            print("❌ Не удалось создать тестовый файл с несколькими алертами")
            return
    else:
        # Подготавливаем однострочный алерт из sample_alert.txt
        file_path = prepare_one_line_alert()
        if not file_path:
            print("❌ Не удалось подготовить файл с однострочным алертом")
            return
    
    print(f"Проверка файла по пути: {file_path}")
    if os.path.exists(file_path):
        print(f"✅ Файл существует, размер: {os.path.getsize(file_path)} байт")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Первые 100 символов: {content[:100]}...\n")
        except Exception as e:
            print(f"⚠️ Предупреждение: Не удалось прочитать содержимое файла: {str(e)}")
    else:
        print(f"❌ ОШИБКА: Файл не найден: {file_path}")
        print("Создание тестового файла с образцом алерта...")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("ПРОМ | АС Рефлекс RESOLVED P-250443890 | Уровень CUSTOM_ALERT ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий on Web request service default web request ----- ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий: RESOLVED Custom Alert P-250443890 in environment Sber PROM2 Problem detected at: 22:39 (MSK) 12.04.2025 - 22:43 (MSK) 12.04.2025 (was open for 4 min) 1 impacted service Web request service default web request ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий The CI03467697_CI03474496_WS_LP-traffic_count_failed value was above normal behavior -общий. ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР, WS_LP PROM 001 - console.ar426hj5.k8s.ca.sbrf.ru PROM 002 - console.ar2qob4m.k8s.ca.sbrf.ru Request: Dimension=/paramsv2/5.0/configuration/get 503 POST , dt.entity.service.name=default web request, dt.entity.service=SERVICE-DFB13954956393AE Stand: default web request threshold: 15 Root cause Based on our dependency analysis all incidents are part of the same overall problem.")
            print(f"✅ Тестовый файл успешно создан: {file_path}")
        except Exception as e:
            print(f"❌ Не удалось создать тестовый файл: {str(e)}")
            logger.exception("Ошибка при создании тестового файла")
            return
    
    # Вызываем функцию analyze_file_alert с пустой строкой в качестве tool_input
    print("\n🔍 Вызов функции analyze_file_alert(''):")
    try:
        print("Ожидайте, идет анализ...")
        start_time = time.time()
        result = analyze_file_alert.invoke(file_path)
        execution_time = time.time() - start_time
        print(f"\n✅ Успешно получен результат анализа (за {execution_time:.2f} сек):\n")
        print(result)
    except Exception as e:
        print(f"\n❌ Произошла ошибка при анализе файла: {str(e)}")
        print("\nТрассировка ошибки:")
        traceback.print_exc()
        logger.exception("Ошибка при вызове analyze_file_alert")

def main():
    """
    Основная функция скрипта.
    Позволяет выбрать интерактивный или автоматический режим.
    """
    try:
        # Если скрипт запущен с аргументом -i, то запускаем интерактивный режим
        if len(sys.argv) > 1 and sys.argv[1] == '-i':
            print("Запуск в интерактивном режиме")
            while True:
                print("\n1. Тестировать анализ файла с одним алертом")
                print("2. Тестировать анализ файла с несколькими алертами")
                print("0. Выход")
                choice = input("\nВыберите опцию: ")
                
                if choice == '1':
                    test_file_analyzer(test_multi_alerts=False)
                elif choice == '2':
                    test_file_analyzer(test_multi_alerts=True)
                elif choice == '0':
                    print("Выход из программы")
                    break
                else:
                    print("Неверный выбор. Попробуйте снова.")
        elif len(sys.argv) > 1 and sys.argv[1] == '-m':
            # Автоматический режим с множественными алертами
            test_file_analyzer(test_multi_alerts=True)
        else:
            # Автоматический режим
            test_file_analyzer(test_multi_alerts=False)
    except KeyboardInterrupt:
        print("\nРабота скрипта прервана пользователем.")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")
        logger.exception("Неожиданная ошибка в main()")

if __name__ == "__main__":
    main() 