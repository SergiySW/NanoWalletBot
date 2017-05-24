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
# Run by cron sometimes or manually
# 

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Bot, ParseMode
import logging
import urllib3, socket, json
import time, math
from requests.utils import quote

# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
wallet = config.get('main', 'wallet')
log_file = config.get('main', 'log_file')
admin_list = json.loads(config.get('main', 'admin_list'))
peer_list = json.loads(config.get('monitoring', 'peer_list'))
block_count_difference_threshold = int(config.get('monitoring', 'block_count_difference_threshold'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)

logger = logging.getLogger(__name__)

peers_url = 'https://raiblockscommunity.net/page/peers.php?json=1'
summary_url = 'https://raiblockscommunity.net/page/summary.php?json=1'
known_ips_url = 'https://raiblockscommunity.net/page/knownips.php?json=1'


# Request to node
from common_rpc import *


# Common functions
from common import push


# Check peers
def monitoring_peers():
	# set bot
	bot = Bot(api_key)
	# list of available peers
	rpc_peers = peers_ip()
	# check in the list of available peers
	for peer in peer_list:
		if (peer not in rpc_peers):
			# check peers from raiblockscommunity.net
			http = urllib3.PoolManager()
			response = http.request('GET', peers_url)
			json_data = json.loads(response.data)
			json_peers = json_data['peers']
			for (i, item) in enumerate(json_peers):
				json_peers[i] = item['ip'].replace("::ffff:", "")
			if (peer not in json_peers):
				# possible peer names
				response = http.request('GET', known_ips_url)
				json_data = json.loads(response.data)
				try:
					peer_name = json_data['::ffff:{0}'.format(peer)][0]
					# Warning to admins
					for user_id in admin_list:
						push(bot, user_id, 'Peer *{0}* ({1}) is offline'.format(peer, peer_name))
				except KeyError:
					# Warning to admins
					for user_id in admin_list:
						push(bot, user_id, 'Peer *{0}* is offline'.format(peer))

# Check block count
def monitoring_block_count():
	# set bot
	bot = Bot(api_key)
	count = rpc({"action": "block_count"}, 'count')
	http = urllib3.PoolManager()
	response = http.request('GET', summary_url)
	json_data = json.loads(response.data)
	community_count = json_data['blocks']
	difference = int(math.fabs(int(community_count) - int(count)))
	reference_count = reference_block_count()
	if (difference > block_count_difference_threshold):
		# Warning to admins
		for user_id in admin_list:
			push(bot, user_id, 'Block count: {0}\nCommunity: {1}\nDifference: *{2}*\nReference: {3}'.format(count, community_count, difference, reference_count))
			rpc({"action": "bootstrap", "address": "::ffff:51.255.160.144", "port": "7075"}, 'success')
			time.sleep(180)
			bootstrap_multi()

monitoring_peers()
monitoring_block_count()