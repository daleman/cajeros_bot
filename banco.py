# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler
from commands import start, cajero, send_photo, ayuda, error
import json
import logging


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    with open('secrets.json') as json_data:
        secrets_json = json.load(json_data)

    telegram_token = secrets_json['token']
    google_api_key = secrets_json['google_api_key']
    updater = Updater(token=telegram_token)

    ##### Creo variables de los handlers ##########

    location_handler = MessageHandler(
        Filters.location, send_photo, pass_user_data=True)
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', ayuda)
    cajero_handler = RegexHandler(r'\b(?i)banelco\b|\b(?i)link\b', cajero,pass_user_data=True)

    dispatcher = updater.dispatcher

    ##### Agrego los handlers al dispatcher ##########

    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(cajero_handler)
    dispatcher.add_handler(location_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_error_handler(error)
    
    # El bot arranca a escuchar
    updater.start_polling()

    updater.idle()
