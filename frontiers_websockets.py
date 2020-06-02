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
Press Ctrl-C on the command line or send a signal to the process to stop the server.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Bot, ParseMode
from telegram.error import BadRequest
from telegram.utils.request import Request
import logging
import json
import time, math

import asyncio, websockets

# Parse config
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
log_file_frontiers = config.get('main', 'log_file_frontiers')
large_amount_warning = int(config.get('main', 'large_amount_warning'))
proxy_url = config.get('proxy', 'url')
proxy_user = config.get('proxy', 'user')
proxy_pass = config.get('proxy', 'password')

ws_url = config.get('main', 'ws_url')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_frontiers)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

hash_url = 'https://nanocrawler.cc/explorer/block/'

# MySQL requests
from common_mysql import *


# Request to node
from common_rpc import *

# Frontiers functions
from common_sender import *


# Common functions
from common import push, mrai_text

# Translation
with open('language.json') as lang_file:    
	language = json.load(lang_file)
def lang_text(text_id, lang_id):
	try:
		return language[lang_id][text_id]
	except KeyError:
		return language['en'][text_id]


def subscription(topic: str, ack: bool=False, options: dict=None):
	d = {"action": "subscribe", "topic": topic, "ack": ack}
	if options is not None:
		d["options"] = options
	return d

async def websockets_receive():
	async with websockets.connect(ws_url) as websocket:
		if (proxy_url is None):
			bot = Bot(api_key)
		else:
			proxy = Request(proxy_url = proxy_url, urllib3_proxy_kwargs = {'username': proxy_user, 'password': proxy_pass })
			bot = Bot(token=api_key, request = proxy)
		
		await websocket.send(json.dumps(subscription("confirmation", options={"include_election_info": "false", "include_block":"true", "all_local_accounts": "true"}, ack=True)))
		connect = json.loads(await websocket.recv()) # ack
		print(connect)
		logging.info(connect)

		while 1:
			rec = json.loads(await websocket.recv())
			topic = rec.get("topic", None)
			if topic:
				item = rec["message"]
				if topic == "confirmation":
					item['type'] = item['block']['subtype']
					if (item['type'] == 'receive' or item['type'] == 'change' or item['type'] == 'epoch'):
						balance = int(math.floor(int(item['block']['balance']) / (10 ** 24)))
						account_mysql = mysql_select_by_account(item['account'])
						extra = False
						if (account_mysql is False):
							account_mysql = mysql_select_by_account_extra(item['account'])
							extra = True
						if (account_mysql[2] != item['hash']): # Compare frontiers
							if (extra):
								mysql_update_frontier_extra(item['account'], item['hash'])
							else:
								mysql_update_frontier(item['account'], item['hash'])
							if (item['type'] == 'receive'): # Receive blocks
								sender_account = rpc({"action": "block_info", "hash": item['block']['link']}, 'block_account')
								lang_id = mysql_select_language(account_mysql[0])
								#logging.info('{0} --> {1}	{2}'.format(mrai_text(account_mysql[3]), mrai_text(balance), item['hash']))
								sender = find_sender (item, account_mysql, sender_account, balance, lang_text)
								received_amount = int(math.floor(int(item['amount']) / (10 ** 24)))
								text = lang_text('frontiers_receive', lang_id).format(mrai_text(received_amount), mrai_text(balance), mrai_text(0), item['hash'], hash_url, sender)
								push(bot, account_mysql[0], text)
								logging.info('{0} Nano (XRB) received by {1}, hash: {2}'.format(mrai_text(received_amount), account_mysql[0], item['hash']))
								#print(text)
								# Large amount check
								if (received_amount >= large_amount_warning):
									time.sleep(0.1)
									push(bot, account_mysql[0], lang_text('frontiers_large_amount_warning', lang_id))
							elif (item['type'] == 'change'): # Change blocks
								logging.warning('Change block {0} for account {1}'.format(item['hash'], item['account']))
								if (balance != int(account_mysql[3])):
									logging.error('Balance change: {0} --> {1}'.format(mrai_text(balance), mrai_text(int(account_mysql[3]))))
							elif (item['type'] == 'epoch'): # Epoch blocks
								logging.warning('Epoch block {0} for account {1}'.format(item['hash'], item['account']))
								if (balance != int(account_mysql[3])):
									logging.error('Balance change: {0} --> {1}'.format(mrai_text(balance), mrai_text(int(account_mysql[3]))))
							# Previous block check
							previous_zero = (item['block']['previous'] == '0000000000000000000000000000000000000000000000000000000000000000' and account_mysql[2] is None)
							if ((previous_zero is False) and item['block']['previous'] != account_mysql[2]):
								logging.error('Mismatch for previous block. Expected {0}, received {1}'.format(account_mysql[2], item['block']['previous']))
								if (item['type'] == 'receive'):
									time.sleep(0.1)
									push(bot, account_mysql[0], 'Please check received block in explorer, you can receive notification for some older block')
				else:
					logging.warning('Unexpected WebSockets message: {0}'.format(json.dumps(item)))

stopped = False
while (stopped is False):
	try:
		asyncio.get_event_loop().run_until_complete(websockets_receive())
	except KeyboardInterrupt:
		stopped = True
		pass
	except ConnectionRefusedError:
		logging.warning("Error connecting to websocket server")
		print("Error connecting to websocket server")
	except Exception as e:
		logging.exception("message")
		time.sleep(60)

