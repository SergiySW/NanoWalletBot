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
import urllib3, socket, json
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
raw_fee_amount = fee_amount * (10 ** 30)
incoming_fee = int(config.get('main', 'incoming_fee'))
raw_incoming_fee = incoming_fee * (10 ** 30)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_frontiers)

logger = logging.getLogger(__name__)

account_url = 'https://raiblockscommunity.net/account/index.php?acc='
hash_url = 'https://raiblockscommunity.net/block/index.php?h='
faucet_url = 'https://raiblockscommunity.net/faucet/mobile.php?a='

# MySQL requests
from common_mysql import mysql_update_balance, mysql_update_frontier, mysql_select_accounts_list, mysql_set_price


# Request to node
from common_rpc import *


# Common functions
from common import push



# frontiers check
def frontiers():
	time_start = int(time.time())
	# set bot
	bot = Bot(api_key)
	# list from MySQL
	accounts_list = mysql_select_accounts_list()
	# list from node. Replace with wallet_frontiers once released
	frontiers = rpc({"action":"frontiers","account":"xrb_1111111111111111111111111111111111111111111111111117353trpda","count":65536}, 'frontiers')
	#print(len(frontiers))
	
	faucet_account = 'xrb_13ezf4od79h1tgj9aiu4djzcmmguendtjfuhwfukhuucboua8cpoihmh8byo'
	
	for account in accounts_list:
		try:
			frontier = frontiers[account[1]]
		#if ((account[1] == r.keys()[0]) and (account[2] != frontier)):
			if (account[2] != frontier):
				# update frontier
				balance = account_balance(account[1])
				# check if balance changed
				mysql_update_frontier(account[1], frontier)
				#print('{0} --> {1}	{2}'.format(account[3], balance, frontier))
				logging.info('{0} --> {1}	{2}'.format(account[3], balance, frontier))
				#print(balance)
				if (int(account[3]) < int(balance)):
					received_amount = int(balance) - int(account[3])
					max_send = int(balance) - int(fee_amount)
					if (max_send < 0):
						max_send = 0
					# retrieve sender
					send_tx = json.loads(rpc({"action":"block","hash":frontier}, 'contents'))
					#print (send_tx)
					send_source = send_tx['source']
					#print (send_source)
					block_account = rpc({"action":"block_account","hash":send_source}, 'account')
					#print (block_account)
					sender = ''
					if (block_account == faucet_account):
						sender = ' from Faucet/Landing'
					elif (block_account == fee_account):
						sender = ' from @RaiWalletBot itself'
					elif (block_account == account[1]):
						sender = ' from you'
					else:
						for sender_account in accounts_list:
							if (sender_account[1] == block_account):
								if ((sender_account[4] is not None) and (sender_account[4])):
									sender = ' from @{0}'.format(sender_account[4])
								else:
									sender = ' from one of our users'
					#print (sender)
					logging.info(sender)
					# receive fee protection
					mysql_update_balance(account[1], int(balance))
					logging.info('{0} Mrai (XRB) received by {1}, hash: {2}'.format(received_amount, account[0], frontier))
					if (incoming_fee >= 1):
						fee = rpc({"action": "send", "wallet": wallet, "source": account[1], "destination": fee_account, "amount": raw_incoming_fee}, 'block')
						balance = account_balance(account[1])
						push(bot, account[0], '*{0} Mrai (XRB)* received{7}. Transaction hash: [{5}]({6}{5})\nIncoming fee: *{4} Mrai (XRB)*. Your current balance: {1} Mrai (XRB). Send limit: {2} Mrai (XRB)'.format("{:,}".format(received_amount), "{:,}".format(balance), "{:,}".format(max_send), incoming_fee, frontier, hash_url, sender))
						logging.info('Incoming fee deducted')
					else:
						#print(account[0])
						#print('*{0} Mrai (XRB)* received{5}. Transaction hash: [{3}]({4}{3})\nYour current balance: *{1} Mrai (XRB)*. Send limit: {2} Mrai (XRB)'.format("{:,}".format(received_amount), "{:,}".format(balance), "{:,}".format(max_send), frontier, hash_url, sender))
						push(bot, account[0], '*{0} Mrai (XRB)* received{5}. Transaction hash: [{3}]({4}{3})\nYour current balance: *{1} Mrai (XRB)*. Send limit: {2} Mrai (XRB)'.format("{:,}".format(received_amount), "{:,}".format(balance), "{:,}".format(max_send), frontier, hash_url, sender))
					time.sleep(0.1)
		# no frontier. No transactions
		except KeyError:
			# doesn't exist
			x = 0 # do something
	time_end = int(time.time())
	total_time = time_end - time_start 
	#print(total_time)
	if (total_time > 20):
		logging.warning(('WARNING!!! \nMore than 20 seconds execution time!!!'))
	return total_time


'''
#def cryptopia():
#	http = urllib3.PoolManager()
	url = 'https://www.cryptopia.co.nz/api/GetMarket/4874'
	response = http.request('GET', url)
	json_cryptopia = json.loads(response.data)
	json_array = json_cryptopia['Data']
	last_price = int(json_array['LastPrice'] * (10 ** 8))
	high_price = int(json_array['High'] * (10 ** 8))
	low_price = int(json_array['Low'] * (10 ** 8))
	ask_price = int(json_array['AskPrice'] * (10 ** 8))
	bid_price = int(json_array['BidPrice'] * (10 ** 8))
	volume = int(json_array['Volume'])
	
	mysql_set_price(last_price, high_price, low_price, ask_price, bid_price, volume)
'''


run_time = frontiers()
if (run_time < 15):
	time.sleep(15-run_time)
	run_time = frontiers()
	if (run_time < 15):
		time.sleep(15-run_time)
		run_time = frontiers()
		if (run_time < 15):
			time.sleep(15-run_time)
			frontiers()
elif (run_time <= 30):
	time.sleep(30-run_time)
	frontiers()

# every 2 minutes
#timer = time.time() % 120
#if (timer > 60):
#	cryptopia()
#cryptopia()