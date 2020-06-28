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


from telegram import Bot, ParseMode
from telegram.error import BadRequest, RetryAfter, TimedOut, Unauthorized, NetworkError
from telegram.utils.request import Request
from time import sleep

# Parse config
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
api_key_common = config.get('main', 'api_key')
proxy_url_common = config.has_option('proxy', 'url') and config.get('proxy', 'url') or None
proxy_user_common = config.has_option('proxy', 'user') and config.get('proxy', 'user') or None
proxy_pass_common = config.has_option('proxy', 'password') and config.get('proxy', 'password') or None

def replace_unsafe(text):
	text = text.replace("xrb_1", "xrb\_1").replace("xrb_3", "xrb\_3")
	return text


def push(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, 
			text=message, 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except BadRequest as e:
		try:
			bot.sendMessage(chat_id=chat_id, 
				text=replace_unsafe(message), 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)
		except BadRequest:
			bot.sendMessage(chat_id=chat_id, 
				text=message.replace("_", "\_"), 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)
	except RetryAfter as e:
		sleep(240)
		bot.sendMessage(chat_id=chat_id, 
			text=replace_unsafe(message), 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except TimedOut as e:
		sleep(60)
		bot.sendMessage(chat_id=chat_id, 
			text=replace_unsafe(message), 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except Unauthorized as e:
		sleep(0.25)
	except NetworkError as e:
		sleep(30)
		bot.sendMessage(chat_id=chat_id, 
			text=replace_unsafe(message), 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except Exception as e:
		sleep(1)
		try:
			bot.sendMessage(chat_id=chat_id, 
				text=message, 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)
		except:
			sleep(2.5)
			bot.sendMessage(chat_id=chat_id, 
				text=message, 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)


def push_simple(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, text=message)
	except BadRequest as e:
		bot.sendMessage(chat_id=chat_id, text=replace_unsafe(message))
	except RetryAfter as e:
		sleep(240)
		bot.sendMessage(chat_id=chat_id, text=message)
	except TimedOut as e:
		sleep(60)
		bot.sendMessage(chat_id=chat_id, text=message)
	except Unauthorized as e:
		sleep(0.25)
	except NetworkError as e:
		sleep(30)
		bot.sendMessage(chat_id=chat_id, text=message)
	except Exception as e:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, text=message)


def message_markdown(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except BadRequest:
		bot.sendMessage(chat_id=chat_id, 
					text=replace_unsafe(message),
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except RetryAfter:
		sleep(240)
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except TimedOut as e:
		sleep(60)
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except Unauthorized as e:
		sleep(0.25)
	except NetworkError as e:
		sleep(30)
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except Exception as e:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)


def text_reply(update, text):
	try:
		update.message.reply_text(text)
	except TimedOut as e:
		sleep(60)
		update.message.reply_text(text)
	except NetworkError as e:
		sleep(30)
		update.message.reply_text(text)
	except Exception as e:
		sleep(1)
		update.message.reply_text(text)


def mrai_text(rai):
	mrai = int(rai / (10 ** 6))
	floating = int(rai - (mrai * (10 ** 6)))
	if (floating == 0):
		mrai_text = "{:,}".format(mrai)
	else:
		if (floating < 10):
			floating_text = '00000{0}'.format(floating)
		elif (floating < 100):
			floating_text = '0000{0}'.format(floating)
		elif (floating < 1000):
			floating_text = '000{0}'.format(floating)
		elif (floating < 10000):
			floating_text = '00{0}'.format(floating)
		elif (floating < 100000):
			floating_text = '0{0}'.format(floating)
		else:
			floating_text = '{0}'.format(floating)
		if (floating_text.endswith('00000')):
			floating_text = floating_text[:-5]
		elif (floating_text.endswith('0000')):
			floating_text = floating_text[:-4]
		elif (floating_text.endswith('000')):
			floating_text = floating_text[:-3]
		elif (floating_text.endswith('00')):
			floating_text = floating_text[:-2]
		elif (floating_text.endswith('0')):
			floating_text = floating_text[:-1]
		mrai_text = '{0}.{1}'.format("{:,}".format(mrai), floating_text)
	return mrai_text

def bot_start():
	# set bot
	if (proxy_url is None):
		bot = Bot(api_key_common)
	else:
		proxy = Request(proxy_url = proxy_url_common, urllib3_proxy_kwargs = {'username': proxy_user_common, 'password': proxy_pass_common })
		bot = Bot(token=api_key_common, request = proxy)
	return bot
