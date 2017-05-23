#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# RaiBlocks Telegram bot
# @RaiWalletBot https://t.me/RaiWalletBot
# 
# Source code:
# https://github.com/SergiySW/RaiWalletBot
# 
# Released under the BSD 3-Clause License
# 


from telegram import Bot, ParseMode
from telegram.error import BadRequest, RetryAfter
from time import sleep


def replace_unsafe(text):
	text = text.replace("xrb_1", "xrb\_1").replace("xrb_3", "xrb\_3")
	return text


def push(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, 
			text=message, 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except BadRequest:
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
	except RetryAfter:
		sleep(240)
		bot.sendMessage(chat_id=chat_id, 
			text=replace_unsafe(message), 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except:
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
	except BadRequest:
		bot.sendMessage(chat_id=chat_id, text=replace_unsafe(message))
	except RetryAfter:
		sleep(240)
		bot.sendMessage(chat_id=chat_id, text=replace_unsafe(message))
	except:
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
					text=replace_unsafe(message),
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)


def text_reply(update, text):
	try:
		update.message.reply_text(text)
	except:
		sleep(1)
		update.message.reply_text(text)


def mrai_text(rai):
	mrai = rai / (10 ** 6)
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
		if (floating_text.endswith('0',1,2) and floating_text.endswith('0')):
			floating_text = floating_text[:-5]
		elif (floating_text.endswith('0',2,3) and floating_text.endswith('0')):
			floating_text = floating_text[:-4]
		elif (floating_text.endswith('0',3,4) and floating_text.endswith('0')):
			floating_text = floating_text[:-3]
		elif (floating_text.endswith('0',4,5) and floating_text.endswith('0')):
			floating_text = floating_text[:-2]
		elif (floating_text.endswith('0')):
			floating_text = floating_text[:-1]
		mrai_text = '{0}.{1}'.format("{:,}".format(mrai), floating_text)
	return mrai_text

