# Генерация VAPID ключей для Render

## Проблема

Ключи, сгенерированные через `npx web-push generate-vapid-keys`, не работают с `pywebpush` из-за формата.

## Решение: Используйте Python для генерации

### Вариант 1: Локально (если Python 3.12 установлен)

```bash
cd backend
python generate_vapid_keys.py
```

Скопируйте сгенерированные ключи в Render.

### Вариант 2: Через Render (временный)

1. Временно добавьте в `backend/main.py` в начало файла (после импортов):

```python
# ВРЕМЕННО: Генерация ключей при запуске
if not os.getenv("VAPID_PRIVATE_KEY"):
    import base64
    vapid_key = py_vapid.Vapid01()
    vapid_key.generate_keys()
    VAPID_PRIVATE_KEY = vapid_key.private_key.pem
    public_key_bytes = vapid_key.public_key.public_key_bytes
    VAPID_PUBLIC_KEY_BASE64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    print("="*60)
    print("СКОПИРУЙТЕ ЭТИ КЛЮЧИ В RENDER:")
    print("="*60)
    print(f"VAPID_PRIVATE_KEY={VAPID_PRIVATE_KEY}")
    print(f"VAPID_PUBLIC_KEY={VAPID_PUBLIC_KEY_BASE64}")
    print("="*60)
```

2. Задеплойте и проверьте логи Render
3. Скопируйте ключи из логов
4. Добавьте их в переменные окружения Render
5. Удалите временный код

### Вариант 3: Использовать онлайн генератор

Откройте Python REPL онлайн (например, https://replit.com) и выполните:

```python
import py_vapid
import base64

vapid_key = py_vapid.Vapid01()
vapid_key.generate_keys()

private_key = vapid_key.private_key.pem
public_key_bytes = vapid_key.public_key.public_key_bytes
public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

print("VAPID_PRIVATE_KEY:")
print(private_key)
print("\nVAPID_PUBLIC_KEY:")
print(public_key_base64)
```

Скопируйте ключи в Render.
