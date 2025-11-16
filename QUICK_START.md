# Быстрый старт

## Шаг 1: Настройка фронтенда

1. Установите зависимости:
```bash
npm install
```

2. Создайте файл `.env` в корне проекта:
```
VITE_API_URL=http://localhost:8000
```

3. Запустите dev сервер:
```bash
npm run dev
```

## Шаг 2: Настройка бэкенда

1. Перейдите в папку backend:
```bash
cd backend
```

2. Создайте виртуальное окружение (рекомендуется):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Сгенерируйте VAPID ключи:
```bash
python generate_vapid_keys.py
```

5. Создайте файл `.env` в папке `backend/`:
```env
VAPID_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
(вставьте приватный ключ из шага 4)
-----END PRIVATE KEY-----
VAPID_PUBLIC_KEY=(вставьте публичный ключ из шага 4)
VAPID_EMAIL=mailto:your-email@example.com

# Опционально: Supabase (если не используете, будет локальное хранилище)
SUPABASE_URL=
SUPABASE_KEY=
```

6. Запустите бэкенд:
```bash
python main.py
```

## Шаг 3: Тестирование

1. Откройте фронтенд в браузере (обычно http://localhost:5173)
2. Нажмите "Включить уведомления" и разрешите уведомления
3. Нажмите "Подписаться на уведомления"
4. Нажмите "Отправить тестовое уведомление"
5. Должно появиться push-уведомление!

## Шаг 4: Настройка Supabase (опционально)

Если хотите использовать Supabase для хранения подписок:

1. Создайте проект на https://supabase.com
2. Перейдите в SQL Editor
3. Выполните SQL из файла `backend/supabase_setup.sql`
4. Получите URL и ключ из Settings → API
5. Добавьте их в `backend/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

## Проблемы?

См. раздел "Решение проблем" в [INSTRUCTION.md](./INSTRUCTION.md)

