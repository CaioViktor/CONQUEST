from dialog.constants import *
from config import *

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup



import requests
#messages - source in dialog.constants
#host,port,TELEGRAM_TOKEN - source in config

server_url = "http://{}:{}/".format(host,port)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text(messages['welcome'].replace("$chatbot_name",chatbot_name))




def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def query_server(chat_id, text):
    url = server_url+"query/"
    r = requests.get(url = url, params = {'user_id':chat_id,'text':text}) 
    data = r.json() 
    return data

def receive_message(update, context):
    """Echo the user message."""
    # print("\n\n\nReceive\n\n\n")
    text = update.message.text
    chat_id = update.message.chat.id
    data = query_server(chat_id, text)
    # print(data)

    if 'message' in data:
        if data['status'] == 0 or data['status'] == 1:
            for message in data['message']:
                update.message.reply_text(message)
        elif data['status'] == WAITING_DESAMBIGUATION:
            keyboard = []
            if len(data['message']) > 0:
                idx = 0
                for message in data['message'][0]:
                    keyboard.append([InlineKeyboardButton(message['text'], callback_data=str(idx))])
                    idx+=1
                # print("vai inserir cancel")
                keyboard.append([InlineKeyboardButton(messages['cancel_desambiugation'], callback_data="-1")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(messages['desambiguation_header'], reply_markup=reply_markup)  
        elif data['status'] == WAITING_CV_VALUE:
            for message in data['message']:
                update.message.reply_text(message)
    else:
        update.message.reply_text(messages['Internal_error'])

def button(update, context):
    # print("\n\n\nButton\n\n\n")
    query = update.callback_query
    # query.edit_message_text(text="Selected option: {}".format(query.data))
    # print(query)
    # print(update)
    chat_id = query.message.chat.id
    text = query.data
    data = query_server(chat_id, text)
    if 'message' in data:
        if data['status'] == 0 or data['status'] == 1:
            for message in data['message']:
                query.message.reply_text(message)
        elif data['status'] == INVALID_OPTION:
            keyboard = []
            options = data['message']
            header = options[0]
            idx = 0
            for message in options[2]:
                keyboard.append([InlineKeyboardButton(message['text'], callback_data=str(idx))])
                idx+=1
            keyboard.append([InlineKeyboardButton(messages['cancel_desambiugation'], callback_data="-1")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text('"{}"'.format(options[1]))
            query.message.reply_text(header, reply_markup=reply_markup) 
        elif data['status'] == WAITING_CV_VALUE:
            for message in data['message']:
                query.message.reply_text(message)   
    else:
        update.message.reply_text(messages['Internal_error'])


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, receive_message))
    dp.add_handler(CallbackQueryHandler(button))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()