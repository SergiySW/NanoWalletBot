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
# Run by cron sometimes or manually
# 

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Bot, ParseMode
from telegram.utils.request import Request
import logging
import urllib3, certifi, socket, json
import time, math
from requests.utils import quote

# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')
log_file = config.get('main', 'log_file')
admin_list = json.loads(config.get('main', 'admin_list'))
peer_list = json.loads(config.get('monitoring', 'peer_list'))
block_count_difference_threshold = int(config.get('monitoring', 'block_count_difference_threshold'))
pending_threshold = int(config.get('monitoring', 'pending_action_threshold'))
min_receive = int(config.get('main', 'min_receive'))
proxy_url = config.get('proxy', 'url')
proxy_user = config.get('proxy', 'user')
proxy_pass = config.get('proxy', 'password')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

peers_url = 'https://raiblocks.net/page/peers.php?json=1'
summary_url = 'https://raiblocks.net/page/summary.php?json=1'
known_ips_url = 'https://raiblocks.net/page/knownips.php?json=1'
block_count_url = 'https://raiwallet.info/api/block_count.php'
header = {'user-agent': 'RaiWalletBot/1.0'}

# Request to node
from common_rpc import *


# Common functions
from common import push


# Check peers
def monitoring_peers():
	# set bot
	if (proxy_url is None):
		bot = Bot(api_key)
	else:
		proxy = Request(proxy_url = proxy_url, urllib3_proxy_kwargs = {'username': proxy_user, 'password': proxy_pass })
		bot = Bot(token=api_key, request = proxy)
	try:
		# list of available peers
		rpc_peers = peers_ip()
		# check in the list of available peers
		for peer in peer_list:
			if (peer not in rpc_peers):
				# check peers from raiblockscommunity.net
				http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
				response = http.request('GET', peers_url, headers=header, timeout=10.0)
				json_data = json.loads(response.data)
				json_peers = json_data['peers']
				for (i, item) in enumerate(json_peers):
					json_peers[i] = item['ip'].replace("::ffff:", "")
				if (peer not in json_peers):
					# possible peer names
					response = http.request('GET', known_ips_url, headers=header, timeout=10.0)
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
	except AttributeError as e:
		for user_id in admin_list:
			push(bot, user_id, 'Peers list is empty!')

# Check block count
def monitoring_block_count():
	# set bot
	if (proxy_url is None):
		bot = Bot(api_key)
	else:
		proxy = Request(proxy_url = proxy_url, urllib3_proxy_kwargs = {'username': proxy_user, 'password': proxy_pass })
		bot = Bot(token=api_key, request = proxy)
	count = int(rpc({"action": "block_count"}, 'count'))
	reference_count = int(reference_block_count())
	
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	response = http.request('GET', summary_url, headers=header, timeout=20.0)
	try:
		json_data = json.loads(response.data)
		community_count = int(json_data['blocks'])
	except ValueError as e:
		community_count = reference_count
	difference = int(math.fabs(community_count - count))
	
	response = http.request('GET', block_count_url, headers=header, timeout=20.0)
	raiwallet_count = int(response.data)
	
	if (difference > block_count_difference_threshold*3):
		# Warning admins
		for user_id in admin_list:
			push(bot, user_id, 'Block count: {0}\nCommunity: {1}\nDifference: *{2}*\nReference: {3}\nraiwallet.info: {4}'.format(count, community_count, difference, reference_count, raiwallet_count))
		# trying to fix
		bootstrap_multi()
	elif (difference > block_count_difference_threshold):
		# trying to fix
		bootstrap_multi()
		

def monitoring_password():
	valid = rpc({"action": "password_valid", "wallet": wallet}, 'valid')
	if (int(valid) == 0):
		unlock(wallet, password)
		print('Unlock: wallet was locked')

def monitoring_pending():
	pending_list = rpc({"action": "wallet_pending", "wallet": wallet, "threshold": (min_receive * (10 ** 24))}, 'blocks')
	if (len(pending_list) > 0):
		# list of pending hashes
		hash_list = []
		for account, pending in pending_list.items():
			for hash in pending:
				hash_list.append(hash)
		# recheck
		time.sleep(90)
		for hash in hash_list:
			exists = rpc({"action": "pending_exists", "hash": hash}, 'exists')
			if (int(exists) == 1):
				# confirm, wait & check again
				rpc({"action": "block_confirm", "hash": hash}, 'started')
				time.sleep(30)
				exists_2 = rpc({"action": "pending_exists", "hash": hash}, 'exists')
				if (int(exists_2) == 1):
					print('Pending hash {0}'.format(hash))
					unlock(wallet, password)
					time.sleep(10)
					rpc({"action": "search_pending", "wallet": wallet}, 'success')
					break

monitoring_peers()
monitoring_block_count()
monitoring_password()
time.sleep(5)
monitoring_pending()
