import requests
import logging
from config import *
from creds import *



def ask_gpt(prompt):
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {YANDEX_IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 100
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        logging.info(f"Request status code: {response.status_code}")
        if response.status_code != 200:
            result = f"Status code {response.status_code}"
            return result
        result = response.json()['result']['alternatives'][0]['message']['text']
    except Exception as e:
        result = "An unexpected error occurred. Details in the log."
        logging.error(f"An unexpected error occurred: {e}")
    return result

def save_gpt_logs():
    log_file = "gpt_logs.txt"
    try:
        with open(log_file, "w") as file:
            for handler in logging.getLogger().handlers:
                for record in handler.buffer:
                    file.write(record.getMessage() + "\n")
        return log_file
    except Exception as e:
        logging.error(f"An error occurred while saving GPT logs: {e}")
        return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
