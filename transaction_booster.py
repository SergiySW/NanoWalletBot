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

import logging
import urllib3, socket, json
import time, math
from requests.utils import quote

# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
log_file_booster = config.get('main', 'log_file_booster')
wallet = config.get('main', 'wallet')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_booster)

logger = logging.getLogger(__name__)

account_url = 'https://raiblockscommunity.net/account/index.php?acc='
hash_url = 'https://raiblockscommunity.net/block/index.php?h='
post_url = 'https://raiblockscommunity.net/processblock/elaborate.php'


# Request to node
from common_rpc import *


# boost transactions
def booster(frontier, count):
	blocks = rpc({"action":"chain","block":frontier,"count":count}, 'blocks')
	for hash in blocks:
		block = quote(rpc({"action":"block","hash":hash}, 'contents'))
		if ('change' not in block):
			r = requests.post(post_url, params="processblock={0}&submit=Process".format(block))
			answer = r.url.replace('https://raiblockscommunity.net/processblock/index.php?m=','').replace('%20', ' ')
			logging.info('{0} boosted. Status: {1}'.format(hash, answer))
			time.sleep(0.1)


# frontiers check to boost transactions
def checker():
	time_start = int(time.time())
	# accounts from node
	accounts_list = rpc({"action":"account_list","wallet":wallet}, 'accounts')
	# list from node. Replace with wallet_frontiers once released
	frontiers = rpc({"action":"frontiers","account":"xrb_1111111111111111111111111111111111111111111111111117353trpda","count":65536}, 'frontiers')
	
	http = urllib3.PoolManager()
	
	for account in accounts_list:
		try:
			frontier = frontiers[account]
			url = '{0}{1}&json=1'.format(account_url, account)
			response = http.request('GET', url)
			json_data = json.loads(response.data)
			json_last_record = json_data['history'][0]
			json_frontier = json_last_record['hash']
			
			# if frontiers not same
			if (not (frontier == json_frontier)):
				# update frontier
				r = rpc({"action":"frontiers","account":account,"count":1}, 'frontiers')
				frontier = r.values()[0]
				# still not same
				if (not (frontier == json_frontier)):
					count = 0
					blocks = rpc({"action":"chain","block":frontier,"count":32}, 'blocks')
					for hash in blocks:
						# if found block with same hash
						if (hash == json_frontier):
							booster(frontier, count)
							break
						# if no common blocks at website history
						elif (count == (len(blocks) - 1)):
							booster(frontier, len(blocks))
						count = count + 1
			time.sleep(0.1)
		# account doesn't exist at website
		except IndexError:
			booster(frontier, 32)
		# no frontier. No transactions
		except KeyError:
			# doesn't exist
			x = 0 # do something
	time_end = int(time.time())
	total_time = time_end - time_start 
	logging.info('Total time: {0}'.format(total_time))
		
checker()