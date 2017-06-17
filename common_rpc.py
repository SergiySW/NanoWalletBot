#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Request to node
import requests, json, urllib3, certifi
import math
import ConfigParser
from time import sleep

config = ConfigParser.ConfigParser()
config.read('bot.cfg')
url = config.get('main', 'url')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')
reference_url = config.get('main', 'reference_url')

hash_url = 'https://raiblockscommunity.net/block/index.php?h='

def rpc(json, key):
	try:
		r = requests.post(url, json=json).json()
		if 'error' not in r:
			return(r[key])
		else:
			print(r['error'])
			return(r['error'])
	except Exception as e:
		sleep(0.5)
		r = requests.post(url, json=json).json()
		if 'error' not in r:
			return(r[key])
		else:
			print(r['error'])
			return(r['error'])


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
	balance = int(r)
	return(balance)


def account_balance(account):
	raw_balance = raw_account_balance(account)
	balance = int(math.floor(raw_balance / (10 ** 24)))
	return(balance)


def accounts_balances(accounts):
	req = requests.post(url, json={"action": "accounts_balances", "accounts": accounts})
	r = req.json()
	if 'error' not in r:
		rpc_balances = r['balances']
		balances = {}
		for account in accounts:
			balances[account] = int(math.floor(int(rpc_balances[account]['balance']) / (10 ** 24)))
		return(balances)
	else:
		print(r['error'])
		return(r['error'])


def raw_account_pending(account):
	r = rpc({"action": "account_balance", "account": account}, 'pending')
	pending = int(r)
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
	for (i, item) in enumerate(peers):
		peers[i] = item.split("]:")[0].replace("[", "").replace("::ffff:", "")
	return peers

# Check frontier existance at remote node or website
def check_block_community(block):
	try:
		http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
		response = http.request('GET', '{0}{1}&json=1'.format(hash_url, block))
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

def bootstrap_multi():
	rpc({"action": "bootstrap_any"}, 'success')
