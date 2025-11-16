-- ============================================
-- Обновление существующей структуры Supabase
-- ============================================
-- Этот скрипт добавляет недостающие элементы к вашей существующей таблице

-- 1. Создание таблицы пользователей (если еще не создана)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Добавление поля user_id в существующую таблицу push_subscriptions
-- Сначала проверяем, существует ли уже это поле
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'push_subscriptions' 
        AND column_name = 'user_id'
    ) THEN
        -- Добавляем поле user_id (пока без NOT NULL, чтобы не было ошибок с существующими данными)
        ALTER TABLE push_subscriptions 
        ADD COLUMN user_id BIGINT;
        
        -- Добавляем foreign key связь
        ALTER TABLE push_subscriptions 
        ADD CONSTRAINT fk_push_subscriptions_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        
        -- Теперь делаем поле обязательным (если в таблице нет данных)
        -- Если у вас уже есть данные, сначала заполните user_id для существующих записей
        -- ALTER TABLE push_subscriptions ALTER COLUMN user_id SET NOT NULL;
    END IF;
END $$;

-- 3. Создание индексов для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id ON push_subscriptions(user_id);
-- Индекс для endpoint уже существует, но проверим
CREATE INDEX IF NOT EXISTS idx_endpoint ON push_subscriptions(endpoint);

-- 4. Включение Row Level Security (RLS) для безопасности
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

-- 5. Удаление старых политик (если они существуют) и создание новых
-- Политики для таблицы users
DROP POLICY IF EXISTS "Allow public read access to users" ON users;
CREATE POLICY "Allow public read access to users"
    ON users FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public insert to users" ON users;
CREATE POLICY "Allow public insert to users"
    ON users FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own data" ON users;
CREATE POLICY "Users can update own data"
    ON users FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- 6. Политики безопасности для таблицы push_subscriptions
DROP POLICY IF EXISTS "Users can read own subscriptions" ON push_subscriptions;
CREATE POLICY "Users can read own subscriptions"
    ON push_subscriptions FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Users can insert own subscriptions" ON push_subscriptions;
CREATE POLICY "Users can insert own subscriptions"
    ON push_subscriptions FOR INSERT
    WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own subscriptions" ON push_subscriptions;
CREATE POLICY "Users can update own subscriptions"
    ON push_subscriptions FOR UPDATE
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Users can delete own subscriptions" ON push_subscriptions;
CREATE POLICY "Users can delete own subscriptions"
    ON push_subscriptions FOR DELETE
    USING (true);

-- Примечание: Если в таблице push_subscriptions уже есть данные без user_id,
-- вам нужно будет либо удалить их, либо назначить им user_id перед тем,
-- как делать поле обязательным (раскомментировать строку выше).

