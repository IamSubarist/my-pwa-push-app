"""
Автономный тест нормализации ключа (не требует установки зависимостей)
Запуск: python test_normalize_standalone.py
"""


def normalize_vapid_private_key(key: str) -> str:
    """Нормализует VAPID приватный ключ из переменной окружения."""
    if not key or not isinstance(key, str):
        return key
    
    # Заменяем литеральные \n на реальные переносы строк
    normalized = key.replace("\\n", "\n")
    
    # Убираем лишние пробелы в начале и конце
    normalized = normalized.strip()
    
    # Проверяем, правильно ли отформатирован ключ
    line_count = normalized.count("\n") + 1 if "\n" in normalized else 1
    
    # Если ключ уже правильно отформатирован (есть переносы строк), возвращаем как есть
    if normalized.startswith("-----BEGIN") and line_count >= 3:
        # Убеждаемся, что в конце есть перенос строки
        if not normalized.endswith("\n"):
            normalized += "\n"
        return normalized
    
    # Если переносы строк потеряны (ключ в одну строку), восстанавливаем их
    if normalized.startswith("-----BEGIN"):
        # Извлекаем содержимое ключа без заголовков
        key_content = normalized.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip().replace(" ", "").replace("\n", "").replace("\r", "")
        # Разбиваем на строки по 64 символа (стандартный формат PEM)
        key_lines = [key_content[i:i+64] for i in range(0, len(key_content), 64)]
        normalized = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_lines) + "\n-----END PRIVATE KEY-----\n"
    
    return normalized


def main():
    """Основная функция для тестирования"""
    print("\n" + "=" * 70)
    print("ТЕСТ НОРМАЛИЗАЦИИ VAPID КЛЮЧА")
    print("=" * 70 + "\n")
    
    # Ваш ключ из Render (в правильном формате)
    test_key_correct = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+w
Uzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L
2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY
-----END PRIVATE KEY-----"""
    
    # Ключ без переносов строк
    test_key_single_line = "-----BEGIN PRIVATE KEY-----MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+wUzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY-----END PRIVATE KEY-----"
    
    # Ключ с литеральными \n
    test_key_literal = "-----BEGIN PRIVATE KEY-----\\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQguQzEToxcoi1JAk+w\\nUzhr6yKaNQGWTbpcCCVu/82O4wihRANCAAQaalrlFw1tW2Uya14SX0DyrMmEvj2L\\n2ZT6plnD4ntI6kjrykbIThEpSG0F+3Oko2pIJttOdpXWCIV4EIudZTDY\\n-----END PRIVATE KEY-----"
    
    test_cases = [
        ("Правильный формат (с переносами строк)", test_key_correct),
        ("Без переносов строк", test_key_single_line),
        ("С литеральными \\n", test_key_literal),
    ]
    
    all_passed = True
    
    for test_name, test_key in test_cases:
        print(f"\n{'-' * 70}")
        print(f"ТЕСТ: {test_name}")
        print(f"{'-' * 70}")
        print(f"Исходный ключ:")
        print(f"  - Длина: {len(test_key)} символов")
        print(f"  - Количество строк: {test_key.count(chr(10)) + 1}")
        preview = test_key[:60].replace(chr(10), '\\n')
        print(f"  - Первые 60 символов: {preview}...")
        
        try:
            normalized = normalize_vapid_private_key(test_key)
            
            print(f"\nНормализованный ключ:")
            print(f"  - Длина: {len(normalized)} символов")
            print(f"  - Количество строк: {normalized.count(chr(10)) + 1}")
            print(f"  - Начинается с BEGIN: {normalized.startswith('-----BEGIN')}")
            print(f"  - Заканчивается на END: {normalized.strip().endswith('-----END PRIVATE KEY-----')}")
            print(f"  - Имеет переносы строк: {chr(10) in normalized}")
            
            # Проверяем структуру PEM
            lines = normalized.split(chr(10))
            if len(lines) >= 3:
                print(f"  - Первая строка: {lines[0]}")
                last_line = lines[-2] if lines[-1] == '' else lines[-1]
                print(f"  - Последняя строка: {last_line}")
                content_lines = [l for l in lines if l and not l.startswith('-----')]
                print(f"  - Количество строк содержимого: {len(content_lines)}")
                print("[OK] Ключ правильно отформатирован!")
            else:
                print("[ERROR] Ключ имеет неправильную структуру PEM!")
                all_passed = False
                
        except Exception as e:
            print(f"[ERROR] Ошибка при нормализации: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("[OK] ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\nФункция normalize_vapid_private_key работает корректно.")
        print("Ключи будут правильно обработаны в main.py.")
    else:
        print("[ERROR] НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    print("=" * 70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    main()

