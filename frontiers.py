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
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
log_file_frontiers = config.get('main', 'log_file_frontiers')
wallet = config.get('main', 'wallet')
fee_account = config.get('main', 'fee_account')
welcome_account = config.get('main', 'welcome_account')
proxy_url = config.get('proxy', 'url')
proxy_user = config.get('proxy', 'user')
proxy_pass = config.get('proxy', 'password')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_frontiers)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

account_url = 'https://www.nanode.co/account/'
hash_url = 'https://www.nanode.co/block/'
faucet_account = 'xrb_13ezf4od79h1tgj9aiu4djzcmmguendtjfuhwfukhuucboua8cpoihmh8byo'

# MySQL requests
from common_mysql import *


# Request to node
from common_rpc import *


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


# frontiers check
def frontiers():
	time_start = int(time.time())
	# set bot
	if (proxy_url is None):
		bot = Bot(api_key)
	else:
		proxy = Request(proxy_url = proxy_url, urllib3_proxy_kwargs = {'username': proxy_user, 'password': proxy_pass })
		bot = Bot(token=api_key, request = proxy)
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
			received_amount = int(math.floor(int(item['amount']) / (10 ** 24)))
			# retrieve sender
			block_account = item['account']
			lang_id = mysql_select_language(account[0])
			sender = lang_text('frontiers_sender_account', lang_id).format(block_account)
			# Sender info
			if (block_account == faucet_account):
				sender = lang_text('frontiers_sender_faucet', lang_id)
			elif ((block_account == fee_account) or (block_account == welcome_account)):
				sender = lang_text('frontiers_sender_bot', lang_id)
			elif (block_account == account[1]):
				sender = lang_text('frontiers_sender_self', lang_id)
			else:
				# Sender from bot
				account_mysql = mysql_select_by_account_extra(block_account)
				if (account_mysql is False):
					# sender from users accounts
					account_mysql = mysql_select_by_account(block_account)
					if (account_mysql is not False):
						if ((account_mysql[4] is not None) and (account_mysql[4])):
							sender = lang_text('frontiers_sender_username', lang_id).format(account_mysql[4])
						elif (block_account != account[1]):
							sender = lang_text('frontiers_sender_users', lang_id).format(block_account)
				else:
					# sender from extra accounts
					user_sender = mysql_select_user(account_mysql[0])
					if ((user_sender[8] is not None) and (user_sender[8]) and (account[0] != sender_account[0])):
						sender = lang_text('frontiers_sender_username', lang_id).format(user_sender[8])
					elif (block_account != account[1]):
						sender = lang_text('frontiers_sender_users', lang_id).format(block_account)
			try:
				z = account[5]
				sender = lang_text('frontiers_sender_by', lang_id).format(sender, account[1].replace("_", "\_"))
				mysql_update_balance_extra(account[1], balance)
			except IndexError as e:
				mysql_update_balance(account[1], balance)
			logging.info(sender)
			logging.info(block_account)
			logging.warning('NoCallback {0} Nano (XRB) received by {1}, hash: {2}'.format(mrai_text(received_amount), account[0], item['hash']))
			text = lang_text('frontiers_receive', lang_id).format(mrai_text(received_amount), mrai_text(balance), mrai_text(0), item['hash'], hash_url, sender)
			mysql_set_sendlist(account[0], text.encode("utf8"))
			#print(text)
			push(bot, account[0], text)
			mysql_delete_sendlist(account[0])
			time.sleep(0.25)

# send old data
def frontiers_sendlist():
	if (proxy_url is None):
		bot = Bot(api_key)
	else:
		proxy = Request(proxy_url = proxy_url, urllib3_proxy_kwargs = {'username': proxy_user, 'password': proxy_pass })
		bot = Bot(token=api_key, request = proxy)
	sendlist = mysql_select_sendlist()
	for send in sendlist:
		time.sleep(5) # if long push to user
		sendlist_new = mysql_select_sendlist()
		if (send in sendlist_new):
			try:
				push(bot, send[0], send[1].replace("_", "\_"))
				logging.warning('NoCallback From sendlist: {0} :: {1}'.format(send[0], send[1].encode("utf8")))
			except Exception as e:
				logging.warning('NoCallback From sendlist + exception: {0} :: {1}'.format(send[0], send[1].encode("utf8")))
				logging.error(e)
			mysql_delete_sendlist(send[0])


def frontiers_usual():
	frontiers_sendlist()
	run_time = frontiers()
	if (run_time < 60):
		time.sleep(60-run_time)
		frontiers()


frontiers_usual()
