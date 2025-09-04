import psycopg2
import sys, time
from datetime import datetime
from typing import Optional, Dict

class DbWriter:
    def __init__(self, db_host, db_port, db_name, db_user, db_password, max_retries, retry_delay):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.conn = None
        self._connect()

    def _connect(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    dbname=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    sslmode='disable'
                )
                self._create_table_if_not_exists()
                self._ensure_sim_info_schema()
                return
            except psycopg2.OperationalError as e:
                retry_count += 1
                print(f"Could not connect. Attempt {retry_count}/{self.max_retries}")
                print(f"host {self.db_host}/ port {self.db_port}/ dbname {self.db_name} / user {self.db_user}")
                print(f"Error details: {e}")
            except psycopg2.OperationalError:
                retry_count += 1
                print(f"Could not connect. Attempt {retry_count}/{self.max_retries}")
                print(f"host {self.db_host}/ port {self.db_port}/ dbname {self.db_name} / user {self.db_user}")
                if retry_count >= self.max_retries:
                    print("Error: Could not connect to the database.")
                    sys.exit(1)
                time.sleep(self.retry_delay)

    def _create_table_if_not_exists(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms_messages (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                phone TEXT NOT NULL,
                text TEXT NOT NULL
            )
        """)
        self.conn.commit()
    
    def _message_exists(self, message):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM sms_messages WHERE date = %s AND phone = %s AND text = %s
        """, (message['date'], message['from'], message['text']))
        result = cursor.fetchone()[0]
        return result > 0
    
    def write(self, message):
        if self._message_exists(message):
            return False  
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sms_messages (date, phone, text) VALUES (%s, %s, %s)
        """, (message['date'], message['from'], message['text']))
        self.conn.commit()
        return True  
    
    def _ensure_sim_info_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sim_info (
            id           BIGSERIAL PRIMARY KEY,
            channel_id   INT NOT NULL CHECK (channel_id BETWEEN 1 AND 32),
            dt           TIMESTAMPTZ DEFAULT now(),
            operator     TEXT,
            phone        TEXT,
            name         TEXT,
            pin          INT,
            imsi         BIGINT,
            last_digits  INT,
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
        """)
        self.conn.commit()

    def upsert_sim_info_rows(self, rows):

        cur = self.conn.cursor()
        try:
            for r in rows:
                ch = r.get('channel_id')
                if ch is None:
                    continue

                cur.execute("""
                    SELECT id FROM sim_info
                    WHERE channel_id = %s AND is_current = true AND valid_to IS NULL
                    FOR UPDATE
                """, (ch,))
                row = cur.fetchone()

                now = datetime.utcnow()

                if row:
                    cur.execute("""
                        UPDATE sim_info
                           SET valid_to = %s, is_current = false
                         WHERE id = %s
                    """, (now, row[0]))

                cur.execute("""
                    INSERT INTO sim_info (
                        channel_id, dt, operator, phone, name, pin, imsi, last_digits,
                        valid_from, valid_to, is_current
                    ) VALUES (
                        %s, now(), %s, %s, %s, %s, %s, %s,
                        %s, NULL, true
                    )
                """, (
                    ch,
                    r.get('operator'),
                    r.get('phone'),
                    r.get('name'),
                    r.get('pin'),
                    r.get('imsi'),
                    r.get('last_digits'),
                    now
                ))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_sim_info_by_channel(self, channel_id: int) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT channel_id, operator, phone, name, pin, imsi, last_digits
            FROM sim_info_current
            WHERE channel_id = %s
            LIMIT 1
        """, (channel_id,))
        row = cur.fetchone()
        if not row:
            return None
        keys = ["channel_id","operator","phone","name","pin","imsi","last_digits"]
        return dict(zip(keys, row))

    def load_sim_info_current_map(self) -> Dict[int, dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT channel_id, operator, phone, name, pin, imsi, last_digits
            FROM sim_info_current
        """)
        res = {}
        keys = ["channel_id","operator","phone","name","pin","imsi","last_digits"]
        for row in cur.fetchall():
            d = dict(zip(keys, row))
            res[d["channel_id"]] = d
        return res