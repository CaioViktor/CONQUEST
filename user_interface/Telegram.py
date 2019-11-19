from dialog.constants import *
from config import *

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests

updater = None
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
    reply(update,messages['welcome'].replace("$chatbot_name",chatbot_name))
    # update.message.reply_text()




def help(update, context):
    """Send a message when the command /help is issued."""
    url = server_url+"list_qais/"
    r = requests.get(url = url,) 
    data = r.json() 
    keyboard = []
    for qai in data['message']:
        keyboard.append([InlineKeyboardButton(qai[2], callback_data=str(qai[0])+"@"+SELECT_QAI)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(messages['help'], reply_markup=reply_markup)  
    # reply(update,'Help!')
    # update.message.reply_text('Help!')


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
    process_server_response(update,context,data)

def process_server_response(update,context,data):
    if 'message' in data:
        if data['status'] == 0 or data['status'] == 1:
            for message in data['message']:
                reply(update,message)
                # update.message.reply_text(message)
        elif data['status'] == WAITING_DESAMBIGUATION:
            keyboard = []
            if len(data['message']) > 0:
                idx = 0
                for message in data['message'][0]:
                    keyboard.append([InlineKeyboardButton(message['text'], callback_data=str(idx)+"@"+WAITING_DESAMBIGUATION)])
                    idx+=1
                # print("vai inserir cancel")
                keyboard.append([InlineKeyboardButton(messages['cancel_desambiugation'], callback_data="-1"+"@"+WAITING_DESAMBIGUATION)])
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(messages['desambiguation_header'], reply_markup=reply_markup)  
        elif data['status'] == WAITING_CV_VALUE:
            for message in data['message']:
                reply(update,message)
                # update.message.reply_text(message)
    else:
        reply(update,messages['Internal_error'])
        # update.message.reply_text(messages['Internal_error'])

def button(update, context):
    # print("\n\n\nButton\n\n\n")
    query = update.callback_query
    # query.edit_message_text(text="Selected option: {}".format(query.data))
    # print("Query:\n",query)
    # print("Update:\n",update)
    chat_id = query.message.chat.id
    if query.data.split("@")[1] == WAITING_DESAMBIGUATION:
        # print("\nDESAM\n")
        text = query.data.split("@")[0]
        data = query_server(chat_id, text)
        if 'message' in data:
            if data['status'] == 0 or data['status'] == 1:
                for message in data['message']:
                    reply(query,message)
                    # query.message.reply_text(message)
            elif data['status'] == INVALID_OPTION:
                keyboard = []
                options = data['message']
                header = options[0]
                idx = 0
                for message in options[2]:
                    keyboard.append([InlineKeyboardButton(message['text'], callback_data=str(idx)+"@"+WAITING_DESAMBIGUATION)])
                    idx+=1
                keyboard.append([InlineKeyboardButton(messages['cancel_desambiugation'], callback_data="-1"+"@"+WAITING_DESAMBIGUATION)])
                reply_markup = InlineKeyboardMarkup(keyboard)
                reply(query,'"{}"'.format(options[1]))
                # query.message.reply_text('"{}"'.format(options[1]))
                query.message.reply_text(header, reply_markup=reply_markup) 
            elif data['status'] == WAITING_CV_VALUE:
                for message in data['message']:
                    reply(query,message)
                    # query.message.reply_text(message)   
        else:
            reply(query,messages['Internal_error'])
            # update.message.reply_text(messages['Internal_error'])
    elif query.data.split("@")[1] == SELECT_QAI:
        url = server_url+"select_qai/"
        r = requests.get(url = url, params = {'user_id':chat_id,'qai_id':query.data.split("@")[0]}) 
        data = r.json() 
        process_server_response(query,context,data)

def reply(update, text):
    if isinstance(text,str) and len(text.strip()) > 0:
        update.message.reply_text(text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def shutdown():
    updater.stop()
    updater.is_idle = False

# def stop(bot, update):
#     threading.Thread(target=shutdown).start()

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    global updater
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("ajuda", help))
    # dp.add_handler(CommandHandler('stop', stop))

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
    # updater.idle()
    print("Telegram bot on and listening")


if __name__ == '__main__':
    main()