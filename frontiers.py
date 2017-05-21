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
# 
# Run by cron every minute
# 

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Bot, ParseMode
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
fee_amount = int(config.get('main', 'fee_amount'))
raw_fee_amount = fee_amount * (10 ** 24)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_frontiers)

logger = logging.getLogger(__name__)

account_url = 'https://raiblockscommunity.net/account/index.php?acc='
hash_url = 'https://raiblockscommunity.net/block/index.php?h='
faucet_url = 'https://faucet.raiblockscommunity.net/form.php?a='
faucet_account = 'xrb_13ezf4od79h1tgj9aiu4djzcmmguendtjfuhwfukhuucboua8cpoihmh8byo'

# MySQL requests
from common_mysql import mysql_update_balance, mysql_update_frontier, mysql_select_accounts_list, mysql_set_price, mysql_select_language, mysql_set_sendlist, mysql_delete_sendlist, mysql_select_sendlist, mysql_select_frontiers, mysql_set_frontiers


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
	bot = Bot(api_key)
	# list from MySQL
	accounts_list = mysql_select_accounts_list()
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
				balance = account_balance(account[1])
				# check if balance changed
				mysql_update_frontier(account[1], frontier)
				logging.info('{0} --> {1}	{2}'.format(mrai_text(account[3]), mrai_text(balance), frontier))
				#print(balance)
				if (int(account[3]) < balance):
					received_amount = balance - int(account[3])
					max_send = balance - fee_amount
					if (max_send < 0):
						max_send = 0
					# retrieve sender
					send_tx = json.loads(rpc({"action":"block","hash":frontier}, 'contents'))
					send_source = send_tx['source']
					block_account = rpc({"action":"block_account","hash":send_source}, 'account')
					sender = ''
					lang_id = mysql_select_language(account[0])
					# Sender info
					if (block_account == faucet_account):
						sender = lang_text('frontiers_sender_faucet', lang_id)
					elif (block_account == fee_account):
						sender = lang_text('frontiers_sender_bot', lang_id)
					elif (block_account == account[1]):
						sender = lang_text('frontiers_sender_self', lang_id)
					else:
						for sender_account in accounts_list:
							if (sender_account[1] == block_account):
								if ((sender_account[4] is not None) and (sender_account[4])):
									sender = lang_text('frontiers_sender_username', lang_id).format(sender_account[4])
								else:
									sender = lang_text('frontiers_sender_users', lang_id)
					logging.info(sender)
					
					logging.info(block_account)
					mysql_update_balance(account[1], balance)
					logging.warning('NoCallback {0} Mrai (XRB) received by {1}, hash: {2}'.format(mrai_text(received_amount), account[0], frontier))
					text = lang_text('frontiers_receive', lang_id).format(mrai_text(received_amount), mrai_text(balance), mrai_text(max_send), frontier, hash_url, sender)
					mysql_set_sendlist(account[0], text.encode("utf8"))
					#print(text)
					push(bot, account[0], text)
					mysql_delete_sendlist(account[0])
					time.sleep(0.25)
		# no frontier. No transactions
		except KeyError:
			# doesn't exist
			x = 0 # do something
	time_end = int(time.time())
	total_time = time_end - time_start 
	#print(total_time)
	if (total_time > 15):
		logging.warning(('WARNING!!! \nMore than 15 seconds execution time!!!'))
	return total_time


# send old data
def frontiers_sendlist():
	bot = Bot(api_key)
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


def mercatox():
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	url = 'https://mercatox.com/public/json24'
	response = http.request('GET', url)
	json_mercatox = json.loads(response.data)
	json_array = json_mercatox['pairs']['XRB_BTC']
	try:
		last_price = int(float(json_array['last']) * (10 ** 8))
	except KeyError:
		last_price = 0
	high_price = int(float(json_array['high24hr']) * (10 ** 8))
	low_price = int(float(json_array['low24hr']) * (10 ** 8))
	ask_price = int(float(json_array['lowestAsk']) * (10 ** 8))
	bid_price = int(float(json_array['highestBid']) * (10 ** 8))
	volume = int(float(json_array['baseVolume']))
	btc_volume = int(float(json_array['quoteVolume']) * (10 ** 8))
	
	mysql_set_price(1, last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume)


def bitgrail():
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	url = 'https://bitgrail.com/api/v1/BTC-XRB/ticker'
	response = http.request('GET', url)
	json_bitgrail = json.loads(response.data)
	json_array = json_bitgrail['response']
	last_price = int(float(json_array['last']) * (10 ** 8))
	high_price = int(float(json_array['high']) * (10 ** 8))
	low_price = int(float(json_array['low']) * (10 ** 8))
	ask_price = int(float(json_array['ask']) * (10 ** 8))
	bid_price = int(float(json_array['bid']) * (10 ** 8))
	volume = int(float(json_array['coinVolume']))
	btc_volume = int(float(json_array['volume']) * (10 ** 8))
	
	mysql_set_price(2, last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume)


def frontiers_usual():
	frontiers_sendlist()
	run_time = frontiers()
	if (run_time < 30):
		time.sleep(30-run_time)
		frontiers()
	
	try:
		mercatox()
	except:
		time.sleep(1) # too many errors from Mercatox API
	try:
		bitgrail()
	except:
		time.sleep(5)
		bitgrail()



frontiers_usual()
