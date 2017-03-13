#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Request to node
import requests, json
import math
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('bot.cfg')
url = config.get('main', 'url')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')

def rpc(json, key):
	r = requests.post(url, json=json).json()
	if 'error' not in r:
		return(r[key])
	else:
		print(r['error'])
		return(r['error'])


def raw_account_balance(account):
	r = rpc({"action": "account_balance", "account": account}, 'balance')
	balance = int(r)
	return(balance)


def account_balance(account):
	raw_balance = raw_account_balance(account)
	balance = int(math.floor(raw_balance / (10 ** 30)))
	return(balance)


def unlock(wallet, password):
	r = rpc({"action": "password_enter", "wallet": wallet, "password": password}, 'valid')
