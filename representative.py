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
import time

# Parse config
import ConfigParser
log_file = config.get('main', 'log_file')
wallet = config.get('main', 'wallet')
representative = config.get('main', 'representative')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)

logger = logging.getLogger(__name__)


# MySQL requests
from common_mysql import mysql_update_balance, mysql_update_frontier, mysql_select_accounts_list, mysql_set_price


# Request to node
from common_rpc import *



# Representative set
def change_representative():
	# list from node
	account_list = rpc({"action":"account_list","wallet":wallet}, 'accounts')
	
	for account in account_list:
		# current representative
		account_representative = rpc({"action":"account_representative","account":account}, 'representative')
		if ((len(account_representative)>63) and (account_representative not in representative)):
			print(account)
			block = rpc({"action":"account_representative_set","wallet":wallet,"account":account,"representative":representative}, 'block')
			mysql_update_frontier(account, block)
			print(block)
			time.sleep(5)
		
		time.sleep(0.1)
		#frontier = r.values()[0]

change_representative()
