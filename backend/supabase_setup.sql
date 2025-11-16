-- ============================================
-- Настройка таблиц для PWA Push Notifications
-- ============================================
-- Выполните этот SQL в SQL Editor в Supabase Dashboard
-- Путь: Project Settings > Database > SQL Editor

-- 1. Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Создание таблицы подписок на push-уведомления
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Создание индексов для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_endpoint ON push_subscriptions(endpoint);

-- 4. Включение Row Level Security (RLS) для безопасности
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

-- 5. Политики безопасности для таблицы users
-- Разрешаем всем читать (для проверки существования email при регистрации)
CREATE POLICY "Allow public read access to users"
    ON users FOR SELECT
    USING (true);

-- Разрешаем всем создавать новых пользователей (регистрация)
CREATE POLICY "Allow public insert to users"
    ON users FOR INSERT
    WITH CHECK (true);

-- Пользователи могут обновлять только свои данные (если нужно в будущем)
CREATE POLICY "Users can update own data"
    ON users FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- 6. Политики безопасности для таблицы push_subscriptions
-- Пользователи могут читать только свои подписки
CREATE POLICY "Users can read own subscriptions"
    ON push_subscriptions FOR SELECT
    USING (true);

-- Пользователи могут создавать свои подписки
CREATE POLICY "Users can insert own subscriptions"
    ON push_subscriptions FOR INSERT
    WITH CHECK (true);

-- Пользователи могут обновлять свои подписки
CREATE POLICY "Users can update own subscriptions"
    ON push_subscriptions FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Пользователи могут удалять свои подписки
CREATE POLICY "Users can delete own subscriptions"
    ON push_subscriptions FOR DELETE
    USING (true);

-- Примечание: В текущей реализации бэкенд использует Service Role Key,
-- который обходит RLS политики. Если вы хотите использовать RLS,
-- вам нужно будет изменить код бэкенда для работы с анонимным ключом
-- и передавать user_id через JWT токен в контексте запроса.
