
CREATE TABLE IF NOT EXISTS sms_messages (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    phone TEXT NOT NULL,
    text TEXT NOT NULL,
    is_sent_http BOOLEAN DEFAULT FALSE,
    is_sent_email BOOLEAN DEFAULT FALSE,
    insertdate TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_sms_messages_dpt
  ON sms_messages (date, phone, text);

CREATE TABLE IF NOT EXISTS sim_info (
    id           BIGSERIAL PRIMARY KEY,
    channel_id   INT NOT NULL CHECK (channel_id BETWEEN 1 AND 32),
    dt           TIMESTAMPTZ DEFAULT now(),
    operator     TEXT,
    phone        TEXT,
    name         TEXT,
    pin          TEXT,
    imsi         TEXT,
    last_digits  TEXT,
    valid_from   TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to     TIMESTAMPTZ,
    is_current   BOOLEAN NOT NULL DEFAULT true
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_sim_info_channel_current
  ON sim_info (channel_id)
  WHERE (is_current = true AND valid_to IS NULL);

CREATE INDEX IF NOT EXISTS ix_sim_info_channel_timeline
  ON sim_info (channel_id, valid_from, COALESCE(valid_to, 'infinity'));

CREATE OR REPLACE VIEW sim_info_current AS
SELECT *
FROM sim_info
WHERE is_current = true AND valid_to IS NULL;

-- SCD2
CREATE OR REPLACE FUNCTION sim_info_scdupdate()
RETURNS TRIGGER AS $$
BEGIN

    NEW.channel_id := OLD.channel_id;

    UPDATE sim_info
       SET valid_to   = now(),
           is_current = false
     WHERE id = OLD.id;

    INSERT INTO sim_info (
        channel_id, dt, operator, phone, name, pin, imsi, last_digits,
        valid_from, valid_to, is_current
    ) VALUES (
        OLD.channel_id,
        COALESCE(NEW.dt,          OLD.dt),
        COALESCE(NEW.operator,    OLD.operator),
        COALESCE(NEW.phone,       OLD.phone),
        COALESCE(NEW.name,        OLD.name),
        COALESCE(NEW.pin,         OLD.pin),
        COALESCE(NEW.imsi,        OLD.imsi),
        COALESCE(NEW.last_digits, OLD.last_digits),
        now(), NULL, true
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

--  SCD2
CREATE TRIGGER IF NOT EXISTS sim_info_scd_trg
BEFORE UPDATE ON sim_info
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION sim_info_scdupdate();
