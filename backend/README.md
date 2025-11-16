# Backend для PWA Push Notifications

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `.env.example` и заполните его:
```bash
cp .env.example .env
```

3. Запустите сервер:
```bash
python main.py
```

Или с помощью uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Настройка Supabase

1. Создайте проект на https://supabase.com
2. Перейдите в SQL Editor и выполните следующий SQL для создания таблицы:

```sql
CREATE TABLE push_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  endpoint TEXT UNIQUE NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_endpoint ON push_subscriptions(endpoint);
```

3. Скопируйте URL и ключ из настроек проекта в `.env` файл

## Генерация VAPID ключей

Если ключи не указаны в `.env`, они будут сгенерированы автоматически при первом запуске.
Сохраните их в `.env` файле для постоянного использования.

## API Endpoints

- `GET /` - Проверка статуса API
- `GET /api/vapid-public-key` - Получить публичный VAPID ключ
- `POST /api/subscribe` - Подписаться на уведомления
- `POST /api/unsubscribe` - Отписаться от уведомлений
- `POST /api/send-notification` - Отправить уведомление всем подписчикам
- `GET /api/subscriptions` - Получить список всех подписок

