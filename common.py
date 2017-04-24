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
from time import sleep

def push(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, 
			text=message, 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)
	except:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, 
			text=message, 
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True)


def push_simple(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, text=message)
	except:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, text=message)


def message_markdown(bot, chat_id, message):
	try:
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)
	except:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, 
					text=message,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True)


