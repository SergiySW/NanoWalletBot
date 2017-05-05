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


