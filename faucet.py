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
# Run by cron every hour, 1-2 minutes after distribution starts
# With new rules it can be inaccurate
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
log_file_faucet = config.get('main', 'log_file_faucet')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_faucet)

logger = logging.getLogger(__name__)




# MySQL requests
from common_mysql import mysql_select_accounts_list, mysql_select_blacklist, mysql_select_language, mysql_select_accounts_list_extra


# Common functions
from common import push_simple


# Translation
with open('language.json') as lang_file:    
	language = json.load(lang_file)
def lang(user_id, text_id):
	lang_id = mysql_select_language(user_id)
	try:
		return language[lang_id][text_id]
	except KeyError:
		return language['en'][text_id]

# Faucet
def faucet():
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	url = 'https://faucet.raiblockscommunity.net/paylist.php?json=1'
	response = http.request('GET', url)
	json_paylist = json.loads(response.data)
	#save it
	with open('paylist.json', 'w') as outfile:  
		json.dump(json_paylist, outfile)
	json_array = json_paylist['pending']
	
	bot = Bot(api_key)
	# list from MySQL
	accounts_list_orig = mysql_select_accounts_list()
	accounts_list_extra = mysql_select_accounts_list_extra()
	accounts_list = accounts_list_orig + accounts_list_extra
	# blacklist
	BLACK_LIST = mysql_select_blacklist()
	for account in accounts_list:
		for paylist in json_array:
			if ((paylist['account'] == account[1]) and (account[0] not in BLACK_LIST)):
				claims = int(paylist['pending'])
				text = lang(account[0], 'faucet_claims').format("{:,}".format(claims))
				try:
					push_simple(bot, account[0], text)
				except Exception as e:
					logging.warn('Push failed for {0}\n{1}'.format(account[0], text))
				#print(text)
				logging.info('{0}\n{1}'.format(account[0], text))
				time.sleep(1.25)
	
	
faucet()