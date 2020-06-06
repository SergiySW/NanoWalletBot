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
# 
# Run by cron every minute
# 

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Bot, ParseMode
from telegram.utils.request import Request
import logging
import urllib3, certifi, socket, json
import time, math

# Parse config
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
log_file_frontiers = config.get('main', 'log_file_frontiers')
wallet = config.get('main', 'wallet')
fee_account = config.get('main', 'fee_account')
welcome_account = config.get('main', 'welcome_account')
large_amount_warning = int(config.get('main', 'large_amount_warning'))

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
from common import push, mrai_text, bot_start


# Translation
with open('language.json') as lang_file:    
	language = json.load(lang_file)
def lang_text(text_id, lang_id):
	try:
		return language[lang_id][text_id]
	except KeyError:
		return language['en'][text_id]


# frontiers check
def frontiers():
	time_start = int(time.time())
	# set bot
	bot = bot_start()
	# list from MySQL
	accounts_list_orig = mysql_select_accounts_list()
	accounts_list_extra = mysql_select_accounts_list_extra()
	accounts_list = accounts_list_orig + accounts_list_extra
	# list from node
	frontiers = rpc({"action":"wallet_frontiers","wallet":wallet}, 'frontiers')
	frontiers_old = json.loads(mysql_select_frontiers())
	mysql_set_frontiers(json.dumps(frontiers))
	
	for account in accounts_list:
		try:
			frontier = frontiers[account[1]]
			frontier_old = frontiers_old[account[1]]
			if ((account[2] != frontier) and (frontier == frontier_old)):
				# update frontier
				try:
					z = account[5]
					account_mysql = mysql_select_by_account_extra(account[1])
					if (account[2] == account_mysql[2]): # no changes in MySQL
						mysql_update_frontier_extra(account[1], frontier)
					else:
						account = account_mysql
				except IndexError as e:
					account_mysql = mysql_select_by_account(account[1])
					if (account[2] == account_mysql[2]): # no changes in MySQL
						mysql_update_frontier(account[1], frontier)
					else:
						account = account_mysql
				# check if balance changed
				balance = account_balance(account[1])
				logging.info('{0} --> {1}	{2}'.format(mrai_text(account[3]), mrai_text(balance), frontier))
				#print(balance)
				if (int(account[3]) < balance):
					receive_messages(bot, account, balance)
					
		# no frontier. No transactions
		except KeyError as e:
			# doesn't exist
			x = 0 # do something
	time_end = int(time.time())
	total_time = time_end - time_start 
	#print(total_time)
	if (total_time > 15):
		logging.warning(('WARNING!!! \nMore than 15 seconds execution time!!!'))
	return total_time

def receive_messages(bot, account, balance):
	history = rpc({"action":"account_history","account":account[1], "count": "50"}, 'history')
	for item in history:
		if (item['hash'] == account[2]):
			break
		if (item['type'] == 'receive'):
			lang_id = mysql_select_language(account[0])
			sender_account = item['account']
			sender = find_sender (item, account, sender_account, balance, lang_text)
			received_amount = int(math.floor(int(item['amount']) / (10 ** 24)))
			logging.warning('NoCallback {0} Nano (XRB) received by {1}, hash: {2}'.format(mrai_text(received_amount), account[0], item['hash']))
			text = lang_text('frontiers_receive', lang_id).format(mrai_text(received_amount), mrai_text(balance), mrai_text(0), item['hash'], hash_url, sender)
			mysql_set_sendlist(account[0], text)
			#print(text)
			push(bot, account[0], text)
			mysql_delete_sendlist(account[0])
			time.sleep(0.25)
			if (received_amount >= large_amount_warning):
				push(bot, account[0], lang_text('frontiers_large_amount_warning', lang_id))
				time.sleep(0.25)

# send old data
def frontiers_sendlist():
	bot = bot_start()
	sendlist = mysql_select_sendlist()
	for send in sendlist:
		time.sleep(5) # if long push to user
		sendlist_new = mysql_select_sendlist()
		if (send in sendlist_new):
			try:
				push(bot, send[0], send[1].replace("_", "\_"))
				logging.warning('NoCallback From sendlist: {0} :: {1}'.format(send[0], send[1]))
			except Exception as e:
				logging.warning('NoCallback From sendlist + exception: {0} :: {1}'.format(send[0], send[1]))
				logging.error(e)
			mysql_delete_sendlist(send[0])


def frontiers_usual():
	frontiers_sendlist()
	run_time = frontiers()
	if (run_time < 60):
		time.sleep(60-run_time)
		frontiers()


frontiers_usual()
