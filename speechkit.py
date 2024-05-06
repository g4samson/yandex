import requests
import config
import creds

def text_to_speech(text):
    headers = {
        'Authorization': f'Bearer {creds.YANDEX_IAM_TOKEN}',
    }
    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': 'filipp',
        'folderId': creds.YANDEX_FOLDER_ID,
    }
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content
    else:
        return False, "Error occurred while requesting SpeechKit"

def speech_to_text(data):
    params = "&".join([
        "topic=general",
        f"folderId={creds.YANDEX_FOLDER_ID}",
        "lang=ru-RU"
    ])
    url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}"
    headers = {
        'Authorization': f'Bearer {creds.YANDEX_IAM_TOKEN}',
    }
    response = requests.post(url=url, headers=headers, data=data)
    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")
    else:
        return False, "Error occurred while requesting SpeechKit"

def generate_response(prompt):
    headers = {
        'Authorization': f'Bearer {creds.YANDEX_IAM_TOKEN}',
    }
    data = {
        'text': prompt,
        'model': 'general',
        'folderId': creds.YANDEX_FOLDER_ID,
    }
    response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate', headers=headers, json=data)
    if response.status_code == 200:
        return True, response.json()['translations'][0]['text']
    else:
        return False, "Error occurred while generating response from YandexGPT"
