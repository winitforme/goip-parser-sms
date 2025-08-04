import psycopg2
import sys, time

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


