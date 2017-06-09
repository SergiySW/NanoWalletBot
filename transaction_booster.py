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
# Run by cron sometimes during distribution period
# or manually in case of unsynchronization
# 

import urllib3, certifi, json
import time

# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
wallet = config.get('main', 'wallet')

frontiers_url = 'https://raiwallet.info/frontiers.json'

# Request to node
from common_rpc import *


# frontiers check to boost transactions
def checker():

	# accounts from node
	accounts_list = rpc({"action":"account_list","wallet":wallet}, 'accounts')
	# list from node
	frontiers = rpc({"action":"wallet_frontiers","wallet":wallet}, 'frontiers')
	
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	response = http.request('GET', frontiers_url)
	remote_frontiers = json.loads(response.data)['frontiers']
	
	for account in accounts_list:
		try:
			frontier = frontiers[account]
			remote_frontier = remote_frontiers[account]
			# if frontiers not same
			if (not (frontier == remote_frontier)):
				blocks = rpc({"action":"chain","block":frontier,"count":32}, 'blocks')
				hash = blocks[len(blocks) - 1]
				rpc({"action":"republish","hash":hash}, 'success')
				print("Hash {0} republished".format(hash))
				time.sleep(1)
		except KeyError, IndexError:
			# doesn't exist
			x = 0 # do something


time_start = int(time.time())
checker()
time_end = int(time.time())
total_time = time_end - time_start 
print('Total time: {0}'.format(total_time))