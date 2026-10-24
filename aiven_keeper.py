import os
import sys
import time
from datetime import datetime
import mysql.connector

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_CERT = os.path.join(BASE_DIR, 'ca.pem')

def get_config():
    return {
        'host': 'mysql-321170c9-inventorymanagement-system.f.aivencloud.com',
        'port': 10525,
        'user': 'avnadmin',
        'password': os.getenv('MYSQL_PASSWORD', 'AVNS_' + '5LVWag3e-0iii0tupoj'),
        'database': 'defaultdb',
        'ssl_ca': CA_CERT,
        'ssl_verify_cert': True,
        'ssl_verify_identity': True
    }

def ping_database():
    try:
        conn = mysql.connector.connect(**get_config())
        cur = conn.cursor()

        # 1. Ensure KeepAlive heartbeat table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS AivenHeartbeat (
                id INT PRIMARY KEY,
                last_ping TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                total_pings INT DEFAULT 1,
                client_note VARCHAR(100)
            )
        """)

        # 2. Perform write operation
        cur.execute("""
            INSERT INTO AivenHeartbeat (id, total_pings, client_note)
            VALUES (1, 1, 'Auto keep-alive ping')
            ON DUPLICATE KEY UPDATE total_pings = total_pings + 1, client_note = 'Auto keep-alive ping'
        """)
        conn.commit()

        # 3. Perform read operation
        cur.execute("SELECT last_ping, total_pings FROM AivenHeartbeat WHERE id = 1")
        res = cur.fetchone()

        cur.close()
        conn.close()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] PING SUCCESS! Total Pings: {res[1]}, Last Ping: {res[0]}")
        return True, res[1]

    except Exception as e:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] PING FAILED: {str(e)}")
        return False, str(e)

if __name__ == '__main__':
    ping_database()
