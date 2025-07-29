DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'sms_messages') THEN
        CREATE DATABASE sms_messages;
    END IF;
END $$;

\c sms_messages;

CREATE TABLE IF NOT EXISTS sms_messages (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    phone TEXT NOT NULL,
    text TEXT NOT NULL
);
