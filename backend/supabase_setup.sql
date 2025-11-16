-- SQL скрипт для настройки таблицы push_subscriptions в Supabase

-- Создание таблицы для хранения подписок на push-уведомления
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  endpoint TEXT UNIQUE NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индекса для быстрого поиска по endpoint
CREATE INDEX IF NOT EXISTS idx_endpoint ON push_subscriptions(endpoint);

-- Комментарии к таблице и полям
COMMENT ON TABLE push_subscriptions IS 'Таблица для хранения подписок на push-уведомления';
COMMENT ON COLUMN push_subscriptions.endpoint IS 'URL endpoint для отправки push-уведомлений';
COMMENT ON COLUMN push_subscriptions.p256dh IS 'Публичный ключ клиента (p256dh)';
COMMENT ON COLUMN push_subscriptions.auth IS 'Секретный ключ аутентификации (auth)';
COMMENT ON COLUMN push_subscriptions.created_at IS 'Дата и время создания подписки';

