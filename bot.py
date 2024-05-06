import logging
import os

import telebot

import config
import creds
import database
import speechkit
import yandex_gpt

bot = telebot.TeleBot(creds.TELEGRAM_BOT_TOKEN)
logging.basicConfig(filename='bot_logs.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not database.is_users_limit():
        logging.info(f"Received message from user {user_id}")
        bot.reply_to(message,
                     "Привет! Я бот-ассистент. Отправьте мне текстовое или голосовое сообщение, и я постараюсь помочь вам.")
    else:
        bot.send_message(user_id, 'Превышен лимит пользователей. Пожалуйста, попробуйте позже.')


@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message,
                 "Этот бот предназначен для обработки текстовых и голосовых сообщений. Он использует Yandex GPT для генерации ответов на текстовые запросы и преобразует текстовые ответы в речь. Просто отправьте мне сообщение, и я постараюсь помочь вам.")


@bot.message_handler(commands=['debug'])
def debug(message):
    try:
        with open("bot_logs.log", 'rb') as file:
            if os.path.getsize("bot_logs.log") > 0:
                bot.send_document(message.chat.id, file)
            else:
                bot.reply_to(message, "Лог-файл пуст.")
    except FileNotFoundError:
        bot.reply_to(message, "Лог-файл не найден.")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")


@bot.message_handler(commands=['stt'])
def handle_stt_command(message):
    if not database.is_users_limit():
        bot.reply_to(message, "Отправьте аудиофайл для распознавания речи.")
        bot.register_next_step_handler(message, handle_stt_voice)


def handle_stt_voice(message):
    if message.content_type == 'voice':
        audio_data = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        success, text = speechkit.speech_to_text(audio_data)
        if success:
            bot.reply_to(message, f"Распознанный текст: {text}")
        else:
            bot.reply_to(message, "Ошибка при распознавании речи.")
    else:
        bot.reply_to(message, "Пожалуйста, отправьте аудиофайл.")


@bot.message_handler(commands=['tts'])
def handle_tts_command(message):
    if not database.is_users_limit():
        bot.reply_to(message, "Отправьте текст для синтеза речи.")
        bot.register_next_step_handler(message, handle_tts_text)


def handle_tts_text(message):
    if message.content_type == 'text':
        text = message.text
        success, voice = speechkit.text_to_speech(text)
        if success:
            bot.send_voice(message.chat.id, voice)
        else:
            bot.reply_to(message, "Ошибка при синтезе речи.")
    else:
        bot.reply_to(message, "Пожалуйста, отправьте текст.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not database.is_users_limit():
        if message.content_type == 'text':
            text = message.text
            user_id = message.from_user.id
            token_count = database.count_tokens_in_dialog([{"role": "user", "content": text}])
            used_tokens = database.get_token_usage(user_id)
            if used_tokens + token_count > config.MAX_TOKENS:
                bot.reply_to(message, 'Превышен лимит использованных токенов.')
            else:
                char_count = len(text)
                current_char_count = database.get_char_count(user_id)
                if current_char_count is not None:
                    current_char_count = int(current_char_count)  # Преобразуем в целое число
                    if current_char_count + char_count > config.CHARACTER_LIMIT:
                        bot.reply_to(message, f"Превышен лимит символов в сообщениях. Максимальное количество символов: {config.CHARACTER_LIMIT}.")
                    else:
                        database.update_char_count(user_id, char_count)
                        response = yandex_gpt.ask_gpt(text)
                        bot.reply_to(message, response)
                        logging.info(f"GPT text response to user {user_id}: {response}")
                else:
                    bot.reply_to(message, "Произошла ошибка при получении количества символов.")
        else:
            bot.reply_to(message, "Пожалуйста, отправьте текстовое сообщение.")
    else:
        bot.reply_to(message, "Превышен лимит пользователей.")




@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    if not database.is_users_limit():
        user_id = message.from_user.id
        audio_data = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        success, text = speechkit.speech_to_text(audio_data)
        if success:
            # Проверяем количество использованных токенов пользователя
            token_count = database.count_tokens_in_dialog([{"role": "user", "content": text}])
            used_tokens = database.get_token_usage(user_id)
            if used_tokens + token_count > config.MAX_TOKENS:
                bot.reply_to(message,
                             f"Превышен лимит токенов в общении с GPT. Максимальное количество токенов: {config.MAX_TOKENS}.")
                return

            # Проверяем количество использованных блоков аудио пользователя
            blocks_used = database.get_audio_blocks_used(user_id)
            if blocks_used >= config.AUDIO_BLOCK_LIMIT:
                bot.reply_to(message, 'Вы использовали все доступные блоки аудио')
                return

            # Обновляем счетчик использованных блоков аудио в базе данных
            database.update_audio_blocks_used(user_id, blocks_used + 1)
            database.update_token_usage(user_id, used_tokens + token_count)

            # Получаем ответ от Yandex GPT
            response = yandex_gpt.ask_gpt(text)
            success, voice = speechkit.text_to_speech(response)
            if success:
                bot.send_voice(message.chat.id, voice)
                logging.info(f"GPT voice response to user {user_id}: {response}")
            else:
                bot.reply_to(message, "Произошла ошибка при синтезе речи.")
        else:
            bot.reply_to(message, "Произошла ошибка при распознавании речи.")





if __name__ == "__main__":
    bot.polling()
