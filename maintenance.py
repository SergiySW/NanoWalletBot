#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Nano Telegram bot
# @NanoWalletBot https://t.me/NanoWalletBot
# 
# Source code:
# https://github.com/SergiySW/NanoWalletBot
# 
# Released under the BSD 3-Clause License
# 
"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram import Bot
import logging
import time

# Parse config
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
url = config.get('main', 'url')
log_file = config.get('main', 'log_file')
domain = config.get('main', 'domain')
listen_port = config.get('main', 'listen_port')
proxy_url = config.has_option('proxy', 'url') and config.get('proxy', 'url') or None
proxy_user = config.has_option('proxy', 'user') and config.get('proxy', 'user') or None
proxy_pass = config.has_option('proxy', 'password') and config.get('proxy', 'password') or None

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)

logger = logging.getLogger(__name__)

text = input("Please enter text: ")
minutes = int(input("Please enter ETA (minutes): "))
time_start = int(time.time())
end_time = time_start + (minutes * 60)

@run_async
def maintenance(bot, update):
	if (minutes > 0):
		time_remain = end_time - int(time.time())
		sec_remain = time_remain % 60
		min_remain = time_remain // 60
		update.message.reply_text('@NanoWalletBot Maintenance\n{0}\n~{1}:{2} minutes remain'.format(text, min_remain, '{0:02d}'.format(sec_remain)))
	else:
		update.message.reply_text('@NanoWalletBot Maintenance\n{0}'.format(text))

def error(bot, update, error):
	logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
	# Create the EventHandler and pass it your bot's token.
	if (proxy_url is None):
		updater = Updater(api_key, workers=64)
	else:
		updater = Updater(token=api_key, workers=64, request_kwargs={'proxy_url': proxy_url, 'urllib3_proxy_kwargs': {'username': proxy_user, 'password': proxy_pass}})

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on noncommand i.e message - return not found
	dp.add_handler(MessageHandler(Filters.command, maintenance))
	dp.add_handler(MessageHandler(Filters.text, maintenance))
	
	# log all errors
	dp.add_error_handler(error)

	# Start the Bot
	#updater.start_polling()
	updater.start_webhook(listen='127.0.0.1', port=int(listen_port), url_path=api_key)
	updater.bot.setWebhook('https://{0}/{1}'.format(domain, api_key))
	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
	print('Starting MAINTENANCE bot server')
	main()
