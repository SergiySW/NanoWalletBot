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
# Run by cron sometimes during distribution period
# or manually in case of unsynchronization
# 

import urllib3, certifi, json
import time

frontiers_url = 'https://raiwallet.info/api/frontiers.json'

# Request to node
from common_rpc import *


# frontiers check to boost transactions
def checker():
	
	# list frontiers
	frontiers = rpc({"action":"frontiers","account":"xrb_1111111111111111111111111111111111111111111111111111hifc8npp","count":"1000000"}, 'frontiers')
	
	#http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	#response = http.request('GET', frontiers_url, timeout=20.0)
	#remote_frontiers = json.loads(response.data)['frontiers']
	# remote list frontiers
	remote_frontiers = rpc_remote({"action":"frontiers","account":"xrb_1111111111111111111111111111111111111111111111111111hifc8npp","count":"1000000"}, 'frontiers')
	
	for account in frontiers:
		frontier = frontiers[account]
		try:
			remote_frontier = remote_frontiers[account]
			# if frontiers not same
			if (not (frontier == remote_frontier)):
				rpc({"action":"republish","hash":remote_frontier}, 'success')
				print("Hash {0} republished".format(remote_frontier))
				time.sleep(0.3)
		except KeyError, IndexError:
			# doesn't exist
			blocks = rpc({"action":"chain","block":frontier,"count":32}, 'blocks')
			hash = blocks[len(blocks) - 1]
			rpc({"action":"republish","hash":hash}, 'success')
			time.sleep(0.3)

	for account in remote_frontiers:
		remote_frontier = remote_frontiers[account]
		try:
			frontier = frontiers[account]
			# if frontiers not same
			if (not (frontier == remote_frontier)):
				rpc_remote({"action":"republish","hash":frontier}, 'success')
				print("Hash {0} republished remotely".format(frontier))
				time.sleep(0.3)
				# insert blocks
				blocks = rpc_remote({"action":"successors","block":frontier,"count":128}, 'blocks')
				for block in blocks:
					if (not (frontier == block)):
						content = rpc_remote({"action":"block","hash":block}, 'contents')
						try:
							rpc({"action":"process","block":content}, '')
						except Exception as e:
							time.sleep(0.1)
						print("Block {0} processed".format(block))
		except KeyError, IndexError:
			# doesn't exist
			blocks = rpc_remote({"action":"chain","block":remote_frontier,"count":32}, 'blocks')
			hash = blocks[len(blocks) - 1]
			rpc_remote({"action":"republish","hash":hash}, 'success')
			time.sleep(0.3)


def starter():
	time_start = int(time.time())
	checker()
	time_end = int(time.time())
	total_time = time_end - time_start 
	print('Total time: {0}'.format(total_time))

checker()
