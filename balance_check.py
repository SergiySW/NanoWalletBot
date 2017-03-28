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

import logging
import urllib3, socket, json
import time, math

# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
wallet = config.get('main', 'wallet')


# MySQL requests
from common_mysql import mysql_select_accounts_list


# Request to node
from common_rpc import *


# balances check
def balance_check():
	time_start = int(time.time())
	# list from MySQL
	accounts_list = mysql_select_accounts_list()
	
	for account in accounts_list:
		balance = int(account_balance(account[1]))
		mysql_balance = int(account[3])
		if (balance != mysql_balance):
			print(account[1])
			print('{0} {1}'.format(mysql_balance, balance))
	time_end = int(time.time())
	total_time = time_end - time_start
	print (total_time)

balance_check()