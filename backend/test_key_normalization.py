"""
Тестовый скрипт для проверки функции normalize_vapid_private_key
"""
import sys
import os

# Добавляем путь к модулю main
sys.path.insert(0, os.path.dirname(__file__))

from main import normalize_vapid_private_key
import py_vapid


def test_key_normalization():
    """Тестирует функцию нормализации ключа с разными форматами"""
    
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ ФУНКЦИИ normalize_vapid_private_key")
    print("=" * 70)
    
    # Тестовый ключ в правильном формате (как вы вставили в Render)
    correct_format_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+w
Uzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L
2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY
-----END PRIVATE KEY-----"""
    
    # Тестовый ключ без переносов строк (как может быть в переменной окружения)
    single_line_key = "-----BEGIN PRIVATE KEY-----MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+wUzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY-----END PRIVATE KEY-----"
    
    # Тестовый ключ с литеральными \n
    literal_newline_key = "-----BEGIN PRIVATE KEY-----\\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+w\\nUzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L\\n2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY\\n-----END PRIVATE KEY-----"
    
    test_cases = [
        ("Правильный формат (с переносами строк)", correct_format_key),
        ("Без переносов строк (одна строка)", single_line_key),
        ("С литеральными \\n", literal_newline_key),
    ]
    
    all_passed = True
    
    for test_name, test_key in test_cases:
        print(f"\n{'=' * 70}")
        print(f"ТЕСТ: {test_name}")
        print(f"{'=' * 70}")
        print(f"\nИсходный ключ (первые 80 символов):")
        preview = test_key[:80].replace("\n", "\\n")
        print(f"{preview}...")
        print(f"Количество строк: {test_key.count(chr(10)) + 1}")
        
        try:
            # Нормализуем ключ
            normalized = normalize_vapid_private_key(test_key)
            
            print(f"\nНормализованный ключ (первые 80 символов):")
            preview_norm = normalized[:80].replace("\n", "\\n")
            print(f"{preview_norm}...")
            print(f"Количество строк: {normalized.count(chr(10)) + 1}")
            
            # Проверяем, что ключ можно использовать с py_vapid
            try:
                vapid = py_vapid.Vapid01()
                vapid.from_pem(normalized)
                print("✅ УСПЕХ: Ключ успешно загружен в py_vapid!")
                
                # Проверяем, что можно получить публичный ключ
                public_key_bytes = vapid.public_key.public_key_bytes
                print(f"✅ УСПЕХ: Публичный ключ получен (длина: {len(public_key_bytes)} байт)")
                
            except Exception as e:
                print(f"❌ ОШИБКА: Не удалось загрузить ключ в py_vapid: {e}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ОШИБКА: Ошибка при нормализации: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print(f"\n{'=' * 70}")
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    print(f"{'=' * 70}\n")
    
    return all_passed


def test_with_real_key():
    """Тестирует с реальным ключом из переменной окружения"""
    print("\n" + "=" * 70)
    print("ТЕСТ С РЕАЛЬНЫМ КЛЮЧОМ ИЗ ПЕРЕМЕННОЙ ОКРУЖЕНИЯ")
    print("=" * 70)
    
    from main import VAPID_PRIVATE_KEY
    
    if not VAPID_PRIVATE_KEY:
        print("⚠️  VAPID_PRIVATE_KEY не установлен в переменных окружения")
        print("   Создайте файл .env в папке backend/ с содержимым:")
        print("   VAPID_PRIVATE_KEY=ваш_ключ")
        return False
    
    print(f"\nКлюч из переменной окружения найден!")
    print(f"Длина ключа: {len(VAPID_PRIVATE_KEY)} символов")
    print(f"Первые 80 символов: {VAPID_PRIVATE_KEY[:80].replace(chr(10), '\\n')}...")
    print(f"Количество строк: {VAPID_PRIVATE_KEY.count(chr(10)) + 1}")
    
    try:
        normalized = normalize_vapid_private_key(VAPID_PRIVATE_KEY)
        print(f"\nПосле нормализации:")
        print(f"Длина ключа: {len(normalized)} символов")
        print(f"Первые 80 символов: {normalized[:80].replace(chr(10), '\\n')}...")
        print(f"Количество строк: {normalized.count(chr(10)) + 1}")
        
        # Проверяем с py_vapid
        vapid = py_vapid.Vapid01()
        vapid.from_pem(normalized)
        print("✅ УСПЕХ: Ключ успешно загружен в py_vapid!")
        
        # Получаем публичный ключ
        public_key_bytes = vapid.public_key.public_key_bytes
        import base64
        public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        print(f"✅ Публичный ключ (base64): {public_key_base64}")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    
    # Тест 1: Тестирование функции с разными форматами
    test1_passed = test_key_normalization()
    
    # Тест 2: Тестирование с реальным ключом (если есть)
    test2_passed = test_with_real_key()
    
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 70)
    if test1_passed:
        print("✅ Тест функции нормализации: ПРОЙДЕН")
    else:
        print("❌ Тест функции нормализации: НЕ ПРОЙДЕН")
    
    if test2_passed:
        print("✅ Тест с реальным ключом: ПРОЙДЕН")
    elif VAPID_PRIVATE_KEY:
        print("❌ Тест с реальным ключом: НЕ ПРОЙДЕН")
    else:
        print("⚠️  Тест с реальным ключом: ПРОПУЩЕН (ключ не найден)")
    print("=" * 70 + "\n")

