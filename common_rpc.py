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
# Request to node
import requests, json, urllib3, certifi
import math
from time import sleep

from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
url = config.get('main', 'url')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')
reference_url = config.get('main', 'reference_url')

rpc_socket_path = config.has_option('main', 'rpc_socket_path') and config.get('main', 'rpc_socket_path') or None
rpc_socket_timeout = config.has_option('main', 'rpc_socket_timeout') and int(config.get('main', 'rpc_socket_timeout')) or 15
if (rpc_socket_path is not None):
	try:
		import nano_ipc
	except ModuleNotFoundError as e:
		print("Error loading nano_ipc")
		rpc_socket_path = None

hash_url = 'https://nanocrawler.cc/explorer/block/'
header = {'user-agent': 'RaiWalletBot/1.0'}

def rpc_http (json):
	try:
		r = requests.post(url, json=json).json()
		return(r)
	except requests.exceptions.ConnectionError as e:
		sleep(7.5)
		r = requests.post(url, json=json).json()
		return(r)
	except Exception as e:
		sleep(0.5)
		r = requests.post(url, json=json).json()
		return(r)

def rpc_ipc (json):
	try:
		client = nano_ipc.Client(rpc_socket_path, timeout=rpc_socket_timeout)
	except nano_ipc.ConnecionFailure as e:
		# Fallback to HTTP
		return rpc_http (json)
	else:
		try:
			response = client.request(json)
			client.close()
			return(response)
		except nano_ipc.BadResponse as e:
			client.close()
			# print(e.response_raw)
			print(e)
			# Fallback to HTTP
			return rpc_http (json)
		except nano_ipc.IPCError as e:
			sleep(7.5)
			response = client.request(json)
			client.close()
			return(response)

def rpc_data (json, force_http = False):
	if (rpc_socket_path is not None and force_http is False):
		return rpc_ipc (json)
	else:
		return rpc_http (json)

def rpc(json, key, force_http = False):
	try:
		r = rpc_data (json, force_http)
		if 'error' not in r:
			return(r[key])
		else:
			print(r)
			print(r['error'])
			return(r['error'])
	except (ValueError, KeyError) as e:
		print(e)
		return("RPC error")


def rpc_send(wallet, source, destination, raw_amount):
	try:
		req = requests.post(url, json={"action": "send", "wallet": wallet, "source": source, "destination": destination, "amount": raw_amount})
		r = req.json()
	except ValueError as e:
		print(req)
		print(req.text)
		r = json.loads(req.text[:84])
	if 'error' not in r:
		return(r['block'])
	else:
		print(r['error'])
		return(r['error'])


def raw_account_balance(account):
	r = rpc({"action": "account_balance", "account": account}, 'balance')
	try:
		balance = int(r)
	except ValueError as e:
		balance = 0
	return(balance)

def account_balance(account):
	raw_balance = raw_account_balance(account)
	balance = int(math.floor(raw_balance / (10 ** 24)))
	return(balance)


def raw_block_balance(hash):
	r = rpc({"action": "block_info", "hash": hash}, 'balance')
	try:
		balance = int(r)
	except ValueError as e:
		balance = 0
	return(balance)

def block_balance(hash):
	raw_balance = raw_block_balance(hash)
	balance = int(math.floor(raw_balance / (10 ** 24)))
	return(balance)


def accounts_balances(accounts):
	r = rpc_data ({"action": "accounts_balances", "accounts": accounts})
	if 'error' not in r:
		rpc_balances = r['balances']
		balances = {}
		for account in accounts:
			try:
				balances[account] = int(math.floor(int(rpc_balances[account]['balance']) / (10 ** 24)))
			except KeyError as e:
				account_text = account
				if (account_text.startswith('nano_')):
					account_text = account_text.replace('nano_', 'xrb_')
				elif (account_text.startswith('xrb_')):
					account_text = account_text.replace('xrb_', 'nano_')
				balances[account] = int(math.floor(int(rpc_balances[account_text]['balance']) / (10 ** 24)))
		return(balances)
	else:
		print(r['error'])
		return(r['error'])


def raw_account_pending(account):
	r = rpc({"action": "account_balance", "account": account}, 'pending')
	try:
		pending = int(r)
	except ValueError as e:
		pending = 0
	return(pending)


def account_pending(account):
	raw_pending = raw_account_pending(account)
	pending = int(math.floor(raw_pending / (10 ** 24)))
	return(pending)


def unlock(wallet, password):
	r = rpc({"action": "password_enter", "wallet": wallet, "password": password}, 'valid')
	search = rpc({"action": "search_pending", "wallet": wallet}, 'started')

def peers_ip():
	peers = rpc({"action":"peers"}, 'peers')
	# only IP of peers
	peers_list = []
	for item, version in peers.items():
		peers_list.append(item.split("]:")[0].replace("[", "").replace("::ffff:", ""))
	return peers_list

# Check frontier existance at remote node or website
def check_block_community(block):
	try:
		http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
		response = http.request('GET', '{0}{1}&json=1'.format(hash_url, block), headers=header, timeout=15.0)
		json_data = json.loads(response.data)
		if ('error' not in json_data):
			return True
		else:
			return False
	except Exception as e:
		return True

def check_block(block):
	# check ip in list
	peers = peers_ip()
	peer = reference_url.replace("http://", "").split(":")[0]
	if (peer in peers):
		try:
			r = requests.post(reference_url, json = {"action": "block", "hash": block}).json()
			if 'error' not in r:
				return True
			else:
				return check_block_community(block)
		except:
			return check_block_community(block)
	else:
		return check_block_community(block)

def reference_block_count():
	# check ip in list
	peers = peers_ip()
	peer = reference_url.replace("http://", "").split(":")[0]
	if (peer in peers):
		try:
			r = requests.post(reference_url, json = {"action": "block_count"}).json()
			if 'error' not in r:
				return r['count']
			else:
				return 0
		except:
			return 0
	else:
		return 0

def reference_peers():
	peers = rpc_remote({"action":"peers"}, 'peers')
	# only IP of peers
	peers_list = []
	for item, version in peers.items():
		peers_list.append(item.split("]:")[0].replace("[", "").replace("::ffff:", ""))
	return peers_list

def rpc_remote(json, key):
	try:
		req = requests.post(reference_url, json=json, timeout=30.0).json()
		if 'error' not in req:
			return(req[key])
		else:
			print(req['error'])
			return(req['error'])
	except KeyError as e:
		return False
	except requests.exceptions.Timeout as e:
		print("Timeout remote RPC")
		return False

def bootstrap_multi():
	rpc({"action": "bootstrap_any"}, 'success')

def validate_account_number(text):
	xrb_account = text.replace('­','').replace(' ','').replace('\r','').replace('\n','')
	xrb_account = xrb_account.replace(r'[^[13456789abcdefghijkmnopqrstuwxyz_]+', '')
	if (len(xrb_account) == 64 or len(xrb_account) == 65):
		destination_check = rpc({"action": "validate_account_number", "account": xrb_account}, 'valid')
		if (destination_check == '1'):
			return xrb_account
		else:
			return False
	else:
		return False
