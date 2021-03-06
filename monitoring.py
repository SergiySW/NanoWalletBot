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
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')
log_file = config.get('main', 'log_file')
admin_list = json.loads(config.get('main', 'admin_list'))
peer_list = json.loads(config.get('monitoring', 'peer_list'))
block_count_difference_threshold = int(config.get('monitoring', 'block_count_difference_threshold'))
pending_threshold = int(config.get('monitoring', 'pending_action_threshold'))
min_receive = int(config.get('main', 'min_receive'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

peers_url = 'https://api.nanocrawler.cc/peers'
nanocrawler_url = 'https://api.nanocrawler.cc/block_count_by_type'
known_ips_url = 'https://www.raiblocks.net/page/knownips.php?json=1'
block_count_url = 'https://raiwallet.info/api/block_count.php'
header = {'user-agent': 'RaiWalletBot/1.0'}

# Request to node
from common_rpc import *


# Common functions
from common import push, bot_start


# Check peers
def monitoring_peers():
	# set bot
	bot = bot_start()
	try:
		# list of available peers
		rpc_peers = peers_ip()
		# remote peer peers list
		remote_peers = reference_peers()
		# check in the list of available peers
		for peer in peer_list:
			if (peer not in rpc_peers and peer not in remote_peers):
				# check peers from nanocrawler.cc
				http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
				response = http.request('GET', peers_url, headers=header, timeout=10.0)
				json_data = json.loads(response.data)
				json_peers = json_data['peers']
				if (peer not in json_peers and '::ffff:{0}'.format(peer) not in json_peers):
					# Warning to admins
					for user_id in admin_list:
						push(bot, user_id, 'Peer *{0}* is offline'.format(peer))
	except AttributeError as e:
		for user_id in admin_list:
			push(bot, user_id, 'Peers list is empty!')

# Check block count
def monitoring_block_count():
	# set bot
	bot = bot_start()
	count = int(rpc({"action": "block_count"}, 'count'))
	reference_count = int(reference_block_count())
	
	http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
	try:
		response = http.request('GET', nanocrawler_url, headers=header, timeout=20.0)
		json_data = json.loads(response.data)
		nanocrawler_count = int(json_data['send']) + int(json_data['receive']) + int(json_data['open']) + int(json_data['change']) + int(json_data['state'])
	except (ValueError, urllib3.exceptions.ReadTimeoutError, urllib3.exceptions.MaxRetryError) as e:
		nanocrawler_count = reference_count
	difference = int(math.fabs(nanocrawler_count - count))
	
	try:
		response = http.request('GET', block_count_url, headers=header, timeout=20.0)
		raiwallet_count = int(response.data)
	except (urllib3.exceptions.ReadTimeoutError, urllib3.exceptions.MaxRetryError) as e:
		raiwallet_count = reference_count
	
	if (difference > block_count_difference_threshold*3):
		# Warning admins
		for user_id in admin_list:
			push(bot, user_id, 'Block count: {0}\nnanocrawler.cc: {1}\nDifference: *{2}*\nReference: {3}\nraiwallet.info: {4}'.format(count, nanocrawler_count, difference, reference_count, raiwallet_count))
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
					rpc({"action": "search_pending", "wallet": wallet}, 'started')
					break

monitoring_peers()
monitoring_block_count()
monitoring_password()
time.sleep(5)
monitoring_pending()
