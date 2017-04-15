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
# Run by cron every hour, 1-2 minutes before distribution
# With new rules it can't be accurate. Disabled in production
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
log_file_faucet = config.get('main', 'log_file_faucet')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_faucet)

logger = logging.getLogger(__name__)




# MySQL requests
from common_mysql import mysql_select_accounts_list, mysql_select_blacklist


# Common functions
from common import push_simple



# Faucet
def faucet():
	http = urllib3.PoolManager()
	url = 'https://raiblockscommunity.net/faucet/paylist.php?json=1'
	response = http.request('GET', url)
	json_paylist = json.loads(response.data)
	#save it
	with open('paylist.json', 'w') as outfile:  
		json.dump(json_paylist, outfile)
	json_array = json_paylist['pending']
	# Top list = 800 Mrai
	#top_tier = 800
	
	bot = Bot(api_key)
	# list from MySQL
	accounts_list = mysql_select_accounts_list()
	# blacklist
	BLACK_LIST = mysql_select_blacklist()
	for account in accounts_list:
		for paylist in json_array:
			if ((paylist['account'] == account[1]) and (account[0] not in BLACK_LIST)):
				estimated_rai = int(paylist['estimated-pay'])
				estimated_mrai = int(math.floor(estimated_rai / (10 ** 6)))
				claims = int(paylist['pending'])
				#
				#if (estimated_mrai > top_tier):
				#	text = 'Faucet claiming period is almost over. You made ~{1} claims this hour. Estimated reward: {2} Mrai (XRB)\nCongratulations, you are one of the Top claimers! You will receive your Mrai (XRB) in 1 hour or less'.format(paylist['account'], "{:,}".format(claims), "{:,}".format(estimated_mrai))
				if (estimated_mrai > 0):
					text = 'Faucet claiming period is almost over. You made ~{1} claims this hour. Estimated reward: {2} Mrai (XRB)\nYou will receive your Mrai (XRB) in the next few minutes'.format(paylist['account'], "{:,}".format(claims), "{:,}".format(estimated_mrai))
				else:
					text = 'Faucet claiming period is almost over. You made ~{1} claims this hour. Estimated reward less than 1 Mrai (XRB)\nYou have to send or claim more Mrai (XRB) to your account {0}'.format(paylist['account'], "{:,}".format(claims), "{:,}".format(estimated_mrai))
				#print(paylist['account'])
				push_simple(bot, account[0], text)
				#print(text)
				logging.info('{0}\n{1}'.format(account[0], text))
				time.sleep(0.1)
	
	
faucet()