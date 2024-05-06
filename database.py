import sqlite3

import config
from creds import *
import requests

DB_NAME = 'usage.db'

def create_usage_table():
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usage (
                            user_id INTEGER PRIMARY KEY,
                            char_count INTEGER DEFAULT 0,
                            audio_blocks_used INTEGER DEFAULT 0,
                            used_tokens INTEGER DEFAULT 0
                            )''')

def get_token_usage(user_id):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT used_tokens FROM usage WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
    return result[0] if result else 0

def update_token_usage(user_id, token_usage):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE usage SET used_tokens=? WHERE user_id=?", (token_usage, user_id))
def is_users_limit(USERS_LIMIT=3):
    """Проверяет, не превышает ли количество уникальных пользователей заданный предел."""
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(f'SELECT COUNT(DISTINCT user_id) FROM usage')
        result = cursor.fetchone()
        unique_users = result[0] if result else 0
        return unique_users >= USERS_LIMIT

def update_char_count(user_id, char_count):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO usage (user_id) VALUES (?)", (user_id,))
        cursor.execute("UPDATE usage SET char_count = char_count + ? WHERE user_id = ?", (char_count, user_id,))
        connection.commit()

def get_char_count(user_id):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT char_count FROM usage WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
    return result[0] if result else 0

def update_audio_blocks_used(user_id, blocks_used):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO usage (user_id) VALUES (?)", (user_id,))
        cursor.execute("UPDATE usage SET audio_blocks_used = audio_blocks_used + ? WHERE user_id = ?", (blocks_used, user_id,))
        connection.commit()

def get_audio_blocks_used(user_id):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT audio_blocks_used FROM usage WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
    return result[0] if result else 0

def count_tokens_in_dialog(messages: sqlite3.Row):
    headers = {
        'Authorization': f'Bearer {YANDEX_IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
       "maxTokens": config.MAX_TOKENS,
       "messages": []
    }

    for row in messages:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )

    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
            json=data,
            headers=headers
        ).json()["tokens"]
    )

create_usage_table()
