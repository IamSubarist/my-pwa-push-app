# Подробная инструкция по реализации Push-уведомлений в PWA

## Обзор проекта

Этот проект реализует систему push-уведомлений для Progressive Web App (PWA) с использованием:

- **Фронтенд**: React + Vite
- **Бэкенд**: FastAPI (Python)
- **База данных**: Supabase (PostgreSQL)
- **Push-сервис**: Web Push API с VAPID ключами

## Архитектура решения

1. **Service Worker** обрабатывает push-события и отображает уведомления
2. **React приложение** управляет подписками пользователей
3. **FastAPI бэкенд** хранит подписки и отправляет уведомления
4. **Supabase** хранит данные о подписках пользователей

## Этап 1: Настройка фронтенда

### 1.1. Service Worker (`public/sw.js`)

Service Worker был обновлен для обработки push-уведомлений:

- **`push` событие**: Получает push-уведомления от сервера и отображает их
- **`notificationclick` событие**: Обрабатывает клики по уведомлениям
- **`notificationclose` событие**: Отслеживает закрытие уведомлений

### 1.2. React компонент (`src/App.jsx`)

Добавлена функциональность:

- Проверка поддержки push-уведомлений браузером
- Запрос разрешения на уведомления
- Подписка/отписка на push-уведомления
- Отправка тестовых уведомлений

### 1.3. Переменные окружения

Создайте файл `.env` в корне проекта фронтенда:

```
VITE_API_URL=http://localhost:8000
```

## Этап 2: Настройка бэкенда

### 2.1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2.2. Генерация VAPID ключей

VAPID (Voluntary Application Server Identification) ключи необходимы для аутентификации при отправке push-уведомлений.

**Вариант 1: Автоматическая генерация**
При первом запуске бэкенда ключи будут сгенерированы автоматически. Сохраните их в `.env` файл.

**Вариант 2: Ручная генерация**

```bash
cd backend
python generate_vapid_keys.py
```

Скопируйте сгенерированные ключи в `.env` файл.

### 2.3. Настройка переменных окружения

Создайте файл `backend/.env`:

```env
# Supabase настройки (опционально, можно использовать локальное хранилище)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# VAPID ключи
VAPID_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
VAPID_PUBLIC_KEY=base64_encoded_public_key
VAPID_EMAIL=mailto:your-email@example.com
```

### 2.4. Запуск бэкенда

```bash
cd backend
python main.py
```

Или с помощью uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Бэкенд будет доступен по адресу: `http://localhost:8000`

## Этап 3: Настройка Supabase (опционально)

Supabase предоставляет бесплатный план с PostgreSQL базой данных.

### 3.1. Создание проекта

1. Перейдите на https://supabase.com
2. Создайте новый проект
3. Дождитесь завершения инициализации (обычно 1-2 минуты)

### 3.2. Создание таблицы

1. Перейдите в **SQL Editor** в панели управления Supabase
2. Выполните SQL скрипт из файла `backend/supabase_setup.sql`:

```sql
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  endpoint TEXT UNIQUE NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_endpoint ON push_subscriptions(endpoint);
```

### 3.3. Получение учетных данных

1. Перейдите в **Settings** → **API**
2. Скопируйте:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`
3. Добавьте их в `backend/.env`

**Примечание**: Если Supabase не настроен, бэкенд будет использовать локальное хранилище в памяти (данные будут потеряны при перезапуске).

## Этап 4: Тестирование

### 4.1. Запуск фронтенда

```bash
npm run dev
```

Фронтенд будет доступен по адресу: `http://localhost:5173` (или другой порт, указанный Vite)

### 4.2. Проверка работы

1. Откройте приложение в браузере
2. Нажмите "Включить уведомления" и разрешите уведомления
3. Нажмите "Подписаться на уведомления"
4. Нажмите "Отправить тестовое уведомление"
5. Должно появиться push-уведомление

### 4.3. Проверка API

Откройте в браузере:

- `http://localhost:8000` - статус API
- `http://localhost:8000/docs` - интерактивная документация Swagger
- `http://localhost:8000/api/subscriptions` - список всех подписок

## Этап 5: Развертывание в продакшн

### 5.1. Развертывание фронтенда

1. Соберите проект:

```bash
npm run build
```

2. Разверните папку `build` на хостинге (например, Vercel, Netlify, или любой статический хостинг)

3. Обновите `.env` с URL продакшн бэкенда:

```
VITE_API_URL=https://your-backend-url.com
```

### 5.2. Развертывание бэкенда

**Вариант 1: Railway**

1. Создайте аккаунт на https://railway.app
2. Подключите GitHub репозиторий
3. Railway автоматически определит Python проект
4. Добавьте переменные окружения в настройках проекта

**Вариант 2: Render**

1. Создайте аккаунт на https://render.com
2. Создайте новый Web Service
3. Подключите репозиторий
4. Укажите команду запуска: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Добавьте переменные окружения

**Вариант 3: Heroku**

1. Установите Heroku CLI
2. Создайте приложение: `heroku create your-app-name`
3. Добавьте переменные окружения: `heroku config:set KEY=value`
4. Разверните: `git push heroku main`

### 5.3. HTTPS обязателен

**Важно**: Push-уведомления работают только через HTTPS (кроме localhost). Убедитесь, что:

- Фронтенд доступен по HTTPS
- Бэкенд доступен по HTTPS
- Service Worker зарегистрирован через HTTPS

## API Endpoints

### `GET /api/vapid-public-key`

Возвращает публичный VAPID ключ для подписки на уведомления.

**Ответ:**

```json
{
  "publicKey": "base64_encoded_key"
}
```

### `POST /api/subscribe`

Сохраняет подписку пользователя.

**Тело запроса:**

```json
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": {
    "p256dh": "base64_key",
    "auth": "base64_key"
  }
}
```

### `POST /api/unsubscribe`

Удаляет подписку пользователя.

**Тело запроса:** То же, что и для subscribe

### `POST /api/send-notification`

Отправляет push-уведомление всем подписчикам.

**Тело запроса:**

```json
{
  "title": "Заголовок уведомления",
  "body": "Текст уведомления",
  "icon": "/icon.png",
  "badge": "/badge.png",
  "tag": "unique-tag",
  "data": {
    "url": "/some-page"
  },
  "requireInteraction": false
}
```

**Ответ:**

```json
{
  "status": "success",
  "message": "Уведомления отправлены",
  "success_count": 5,
  "failed_count": 0,
  "failed_endpoints": []
}
```

### `GET /api/subscriptions`

Возвращает список всех подписок (для администрирования).

## Структура проекта

```
my-pwa-push-app/
├── src/
│   ├── App.jsx          # Основной компонент с логикой push
│   ├── App.css          # Стили
│   └── main.jsx         # Точка входа
├── public/
│   ├── sw.js            # Service Worker
│   └── manifest.json    # PWA манифест
├── backend/
│   ├── main.py          # FastAPI приложение
│   ├── requirements.txt # Python зависимости
│   ├── generate_vapid_keys.py  # Генератор VAPID ключей
│   ├── supabase_setup.sql      # SQL для создания таблицы
│   └── README.md        # Документация бэкенда
├── .env                 # Переменные окружения фронтенда
└── INSTRUCTION.md       # Эта инструкция
```

## Решение проблем

### Проблема: Уведомления не приходят

1. **Проверьте HTTPS**: Push работает только через HTTPS (кроме localhost)
2. **Проверьте разрешения**: Убедитесь, что пользователь разрешил уведомления
3. **Проверьте Service Worker**: Откройте DevTools → Application → Service Workers
4. **Проверьте подписки**: Откройте DevTools → Application → Service Workers → Push
5. **Проверьте консоль**: Могут быть ошибки в консоли браузера или сервера

### Проблема: Ошибка при подписке

1. **Проверьте VAPID ключи**: Убедитесь, что они правильно сгенерированы и сохранены
2. **Проверьте CORS**: Убедитесь, что бэкенд разрешает запросы с фронтенда
3. **Проверьте URL бэкенда**: Убедитесь, что `VITE_API_URL` правильный

### Проблема: Ошибка подключения к Supabase

1. **Проверьте учетные данные**: Убедитесь, что URL и ключ правильные
2. **Проверьте таблицу**: Убедитесь, что таблица создана
3. **Проверьте права доступа**: Убедитесь, что используется `anon` ключ с правильными правами

## Дополнительные возможности

### Персонализированные уведомления

Вы можете добавить идентификатор пользователя при подписке:

```javascript
// В App.jsx
const subscribeResponse = await fetch(`${API_URL}/api/subscribe`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    ...subscription,
    userId: "user123", // Добавить идентификатор пользователя
  }),
});
```

И обновить таблицу в Supabase для хранения `user_id`.

### Отправка уведомлений конкретному пользователю

Добавьте endpoint для отправки уведомления конкретному пользователю:

```python
@app.post("/api/send-notification-to-user/{user_id}")
async def send_notification_to_user(user_id: str, notification: NotificationData):
    # Получить подписки пользователя из БД
    # Отправить уведомление только этим подпискам
    pass
```

### Планирование уведомлений

Используйте Celery или аналогичную библиотеку для планирования отправки уведомлений в определенное время.

## Безопасность

1. **VAPID ключи**: Храните приватный ключ в секретах, никогда не коммитьте его в Git
2. **CORS**: В продакшене ограничьте `allow_origins` конкретными доменами
3. **Аутентификация**: Добавьте аутентификацию для endpoints отправки уведомлений
4. **Rate limiting**: Добавьте ограничение частоты запросов для предотвращения злоупотреблений

## Полезные ссылки

- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [VAPID Specification](https://tools.ietf.org/html/rfc8292)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

## Заключение

Вы успешно реализовали систему push-уведомлений для PWA! Теперь вы можете:

- Подписывать пользователей на уведомления
- Отправлять уведомления всем подписчикам
- Хранить подписки в базе данных
- Масштабировать систему для большого количества пользователей

Если у вас возникли вопросы или проблемы, проверьте раздел "Решение проблем" или обратитесь к документации используемых технологий.
