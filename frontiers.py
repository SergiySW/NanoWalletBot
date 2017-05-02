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
import os, sys

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
faucet_url = 'https://faucet.raiblockscommunity.net/form.php?a='

# MySQL requests
from common_mysql import mysql_update_balance, mysql_update_frontier, mysql_select_accounts_list, mysql_set_price, mysql_select_language


# Request to node
from common_rpc import *


# Common functions
from common import push


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
					lang_id = mysql_select_language(account[0])
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
					#print (sender)
					logging.info(sender)
					logging.info(block_account)
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
						#print(lang_text('frontiers_receive', lang_id).format("{:,}".format(received_amount), "{:,}".format(balance), "{:,}".format(max_send), frontier, hash_url, sender))
						push(bot, account[0], lang_text('frontiers_receive', lang_id).format("{:,}".format(received_amount), "{:,}".format(balance), "{:,}".format(max_send), frontier, hash_url, sender))
					time.sleep(0.1)
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


'''
def cryptopia():
	http = urllib3.PoolManager()
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


def mercatox():
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	url = 'https://mercatox.com/public/json24'
	response = http.request('GET', url)
	json_mercatox = json.loads(response.data)
	json_array = json_mercatox['pairs']['XRB_BTC']
	last_price = int(float(json_array['last']) * (10 ** 8))
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
	run_time = frontiers()
	while run_time < 55:
		time.sleep(3)
		run_time = run_time + 3 + frontiers()
	
	#cryptopia()
	try:
		mercatox()
	except:
		time.sleep(5)
		mercatox()
	try:
		bitgrail()
	except:
		time.sleep(5)
		bitgrail()


# check if already running
def frontiers_proc_check():
	for dirname in os.listdir('/proc'):
		if dirname == 'curproc':
			continue

		try:
			with open('/proc/{}/cmdline'.format(dirname), mode='rb') as fd:
				content = fd.read().decode().split('\x00')
		except Exception:
			continue

		cont3 = ''
		if (len(content) == 3):
			cont3 = content[2]
		if (('python' in content[0]) or ('python' in cont3)):
			if (((content[1] in sys.argv[0]) or (sys.argv[0] in cont3)) and ('self' not in dirname)):
				frontiers_usual()


#frontiers_proc_check()
frontiers_usual()
