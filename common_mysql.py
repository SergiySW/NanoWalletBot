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

import mysql.connector
import hashlib, binascii
from Cryptodome.Cipher import AES

from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
mysql_server = config.has_option('mysql', 'mysql_server') and config.get('mysql', 'mysql_server') or 'localhost'
mysql_socket = config.has_option('mysql', 'mysql_socket') and config.get('mysql', 'mysql_socket') or None
mysql_database = config.get('mysql', 'mysql_database')
mysql_user = config.get('mysql', 'mysql_user')
mysql_pass = config.get('mysql', 'mysql_pass')
ddos_protect_seconds = config.get('main', 'ddos_protect_seconds')
feeless_seconds = int(config.get('main', 'feeless_seconds'))

salt = config.get('password', 'salt')
aes_password = config.get('password', 'aes_password')

# MySQL requests

mysql_config = {
  'user': mysql_user,
  'password': mysql_pass,
  'database': mysql_database,
  'raise_on_warnings': True,
  'use_unicode': True,
  'charset': 'utf8',
}

if (mysql_socket is not None):
	mysql_config['unix_socket'] = mysql_socket
else:
	mysql_config['host'] = mysql_server


def mysql_insert(data):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	
	add_user = ("INSERT INTO rai_bot "
			  "(user_id, account, chat_id, username) "
			  "VALUES (%(user_id)s, %(account)s, %(chat_id)s, %(username)s)")
	
	cursor.execute(add_user, data)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_insert_extra(data):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_data = ("INSERT INTO rai_bot_extra "
			  "(user_id, account, extra_id) "
			  "VALUES (%(user_id)s, %(account)s, %(extra_id)s)")
	cursor.execute(add_data, data)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_user(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT * FROM rai_bot WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	return(account)


def mysql_select_user_extra(user_id, active = False):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	if (active is not False):
		query = ("SELECT * FROM rai_bot_extra WHERE user_id = %s AND send_from = 1")
	else:
		query = ("SELECT * FROM rai_bot_extra WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	account = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(account)


def mysql_select_accounts_list():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, account, frontier, balance, username FROM rai_bot")
	cursor.execute(query)
	accounts_list = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_list)


def mysql_select_by_account(xrb_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, account, frontier, balance, username FROM rai_bot WHERE account LIKE %s")
	cursor.execute(query, (xrb_account,))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	if (account is not None):
		return(account)
	else:
		return False


def mysql_select_by_account_extra(xrb_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, account, frontier, balance, extra_id, '1' as extra FROM rai_bot_extra WHERE account LIKE %s")
	cursor.execute(query, (xrb_account,))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	if (account is not None):
		return(account)
	else:
		return False


def mysql_select_by_id_extra(user_id, extra_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, account, frontier, balance, extra_id FROM rai_bot_extra WHERE user_id = %s AND extra_id = %s")
	cursor.execute(query, (int(user_id), int(extra_id),))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	if (account is not None):
		return(account)
	else:
		return False


def mysql_select_accounts_balances():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, balance FROM rai_bot")
	cursor.execute(query)
	accounts_balances = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_balances)


def mysql_select_accounts_list_extra():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, account, frontier, balance, extra_id, '1' as extra FROM rai_bot_extra")
	cursor.execute(query)
	accounts_list = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_list)

def mysql_user_id_from_account(xrb_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id FROM rai_bot WHERE account LIKE %s")
	cursor.execute(query, (xrb_account,))
	user_id = cursor.fetchone()
	if (user_id is None):
		query = ("SELECT user_id FROM rai_bot_extra WHERE account LIKE %s")
		cursor.execute(query, (xrb_account,))
		user_id = cursor.fetchone()
	if (user_id is not None):
		user_id = user_id[0]
	cursor.close()
	cnx.close()
	return(user_id)


def mysql_user_existance(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT * FROM rai_bot WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	if (account is not None):
		return True
	else:
		return False


def mysql_update_frontier(account, frontier):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET frontier = %s WHERE account LIKE %s")
	cursor.execute(query, (frontier, account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_frontier_extra(account, frontier):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot_extra SET frontier = %s WHERE account LIKE %s")
	cursor.execute(query, (frontier, account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_balance(account, balance):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET balance = %s WHERE account LIKE %s")
	cursor.execute(query, (int(balance), account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_balance_extra(account, balance):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot_extra SET balance = %s WHERE account LIKE %s")
	cursor.execute(query, (int(balance), account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_username(user_id, username):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET username = %s WHERE user_id = %s")
	cursor.execute(query, (username, int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_amount(account, amount):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET send_amount = %s WHERE account LIKE %s")
	cursor.execute(query, (int(amount), account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_destination(account, send_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET send_destination = %s WHERE account LIKE %s")
	cursor.execute(query, (send_account, account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_from(from_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot_extra SET send_from = 1 WHERE account LIKE %s")
	cursor.execute(query, (from_account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean(account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET send_destination = NULL, send_amount = 0 WHERE account LIKE %s")
	cursor.execute(query, (account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean_extra(from_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot_extra SET send_from = 0 WHERE account LIKE %s")
	cursor.execute(query, (from_account,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean_extra_user(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot_extra SET send_from = 0 WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean_all():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("UPDATE rai_bot SET send_destination = NULL, send_amount = 0")
	cursor.execute(query)
	cnx.commit()
	query = ("UPDATE rai_bot_extra SET send_from = 0")
	cursor.execute(query)
	cnx.commit()
	query = ("TRUNCATE rai_bot_send_all")
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_account_by_username(username):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT account FROM rai_bot WHERE username LIKE %s")
	cursor.execute(query, (username,))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	#print(account)
	if (account is not None):
		return account[0]
	else:
		return False


def mysql_stats():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT COUNT(*) FROM rai_bot")
	cursor.execute(query)
	users = cursor.fetchone()[0]
	query = ("SELECT COUNT(*) FROM rai_bot_extra")
	cursor.execute(query)
	accounts = users + cursor.fetchone()[0]
	query = ("SELECT SUM(balance) FROM rai_bot")
	cursor.execute(query)
	balance = int(cursor.fetchone()[0] / (10 ** 6))
	query = ("SELECT SUM(balance) FROM rai_bot_extra")
	cursor.execute(query)
	balance = balance + int(cursor.fetchone()[0] / (10 ** 6))
	#price = mysql_select_price()[0]
	cursor.close()
	cnx.close()
	stats = "Total users: {0}\nTotal accounts: {2}\nTotal balance: {1} Mrai (XRB)".format("{:,}".format(users), "{:,}".format(balance), "{:,}".format(accounts))
	return stats


def mysql_account_balance(account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT balance FROM rai_bot WHERE account LIKE %s")
	cursor.execute(query, (account,))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	if (account is not None):
		return int(account[0])
	else:
		return False

#@run_async
def mysql_set_password(user_id, hex):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("INSERT INTO rai_bot_passwords SET user_id = %s, password = %s")
	cursor.execute(query, (int(user_id), hex,))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_check_password(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT password FROM rai_bot_passwords WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	if (account is not None):
		return account[0]
	else:
		return False

#@run_async
def mysql_delete_password(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("DELETE FROM rai_bot_passwords WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_price():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume FROM rai_price")
	cursor.execute(query)
	price = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(price)

def mysql_set_price(id, last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_price = ("REPLACE INTO rai_price SET id = %s, last_price = %s, high_price = %s, low_price = %s, ask_price = %s, bid_price = %s, volume = %s, btc_volume = %s")
	cursor.execute(add_price, (int(id), int(last_price), int(high_price), int(low_price), int(ask_price), int(bid_price), int(volume), int(btc_volume),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_blacklist():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id FROM rai_black_list")
	cursor.execute(query)
	#black_list = cursor.fetchall()
	black_list = [item[0] for item in cursor.fetchall()]
	cursor.close()
	cnx.close()
	return(black_list)

def mysql_set_blacklist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("INSERT INTO rai_black_list SET user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_blacklist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("DELETE FROM rai_black_list WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_set_language(user_id, language):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("REPLACE INTO rai_bot_language SET user_id = %s, language = %s")
	cursor.execute(query, (int(user_id), language,))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_select_language(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT language FROM rai_bot_language WHERE user_id = %s")
	try:
		cursor.execute(query, (int(user_id),))
		language = cursor.fetchone()[0]
	except TypeError:
		mysql_set_language(user_id, 'en')
		language = 'en'
	cursor.close()
	cnx.close()
	return(language)

def mysql_exist_language(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT language FROM rai_bot_language WHERE user_id = %s")
	try:
		cursor.execute(query, (int(user_id),))
		language = cursor.fetchone()[0]
		returned = language
	except TypeError:
		returned = False
	cursor.close()
	cnx.close()
	return(returned)


def mysql_set_hide(user_id, hide):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("REPLACE INTO rai_bot_hide_list SET user_id = %s, hide = %s")
	cursor.execute(query, (int(user_id), hide, ))
	cnx.commit()
	cursor.close()
	cnx.close()
	mysql_update_send_clean_extra_user(user_id)

def mysql_select_hide(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT hide FROM rai_bot_hide_list WHERE user_id = %s")
	try:
		cursor.execute(query, (int(user_id),))
		select = cursor.fetchone()[0]
		hide = int(select)
	except TypeError:
		mysql_set_hide(user_id, 0)
		hide = 0
	cursor.close()
	cnx.close()
	return(hide)


def mysql_set_sendlist(user_id, text):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("INSERT INTO rai_send_list SET user_id = %s, text = %s")
	cursor.execute(query, (int(user_id), text,))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_sendlist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("DELETE FROM rai_send_list WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_select_sendlist():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT user_id, text FROM rai_send_list")
	cursor.execute(query)
	price = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(price)


def mysql_select_frontiers():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT json FROM rai_frontiers")
	cursor.execute(query)
	frontiers = cursor.fetchone()[0]
	cursor.close()
	cnx.close()
	return(frontiers)

def mysql_set_frontiers(json):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_frontiers = ("REPLACE INTO rai_frontiers SET id = 1, json = '{0}'".format(json))
	cursor.execute(add_frontiers)
	cnx.commit()
	cursor.close()
	cnx.close()


import time
def mysql_ddos_protector(user_id, message_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	
	returned = None
	timestamp = int(time.time())

	query = ("SELECT datetime, message_id FROM rai_bot_access WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	date_time = cursor.fetchone()
	if (date_time is not None):
		ddos_protect = 1 + int(date_time[0])
		date_protect = int(ddos_protect_seconds) + int(date_time[0])
		double_message_protect = int(date_time[1])
		if ((ddos_protect > timestamp) or (message_id == double_message_protect)):
			returned = True
		elif (date_protect > timestamp):
			returned = False
		else:
			returned = None
	add_user = ("REPLACE INTO rai_bot_access SET user_id = %s, datetime = %s, message_id = %s")
	cursor.execute(add_user, (int(user_id), timestamp, int(message_id),))
	cnx.commit()
	cursor.close()
	cnx.close()
	return returned

def mysql_select_send_time(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT datetime FROM rai_bot_send_time WHERE user_id = %s"
	timestamp = int(time.time())
	try:
		cursor.execute(query, (int(user_id),))
		old_timestamp = int(cursor.fetchone()[0])
		if ((timestamp - old_timestamp) >= feeless_seconds):
			returned = True
		else:
			time.sleep (feeless_seconds - timestamp + old_timestamp)
			returned = True
	except TypeError:
		add_timestamp = ("REPLACE INTO rai_bot_send_time SET user_id = %s, datetime = 0")
		cursor.execute(add_timestamp, (int(user_id),))
		cnx.commit()
		returned = True
	cursor.close()
	cnx.close()
	return returned

def mysql_update_send_time(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	timestamp = int(time.time())
	add_timestamp = "REPLACE INTO rai_bot_send_time SET user_id = %s, datetime = %s"
	cursor.execute(add_timestamp, (int(user_id), timestamp,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_price_high():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT * FROM rai_price_high")
	cursor.execute(query)
	array = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(array)

def mysql_set_price_high(user_id, price, exchange = 0):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("REPLACE INTO rai_price_high SET user_id = %s, price = %s, exchange = %s")
	cursor.execute(query, (int(user_id), int(price), int(exchange),))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_price_high(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("DELETE FROM rai_price_high WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_price_low():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT * FROM rai_price_low")
	cursor.execute(query)
	array = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(array)

def mysql_set_price_low(user_id, price, exchange = 0):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("REPLACE INTO rai_price_low SET user_id = %s, price = %s, exchange = %s")
	cursor.execute(query, (int(user_id), int(price), int(exchange),))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_price_low(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("DELETE FROM rai_price_low WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_seed(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT seed FROM rai_bot_seeds WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	select_seed = cursor.fetchone()
	cursor.close()
	cnx.close()
	seed = False
	try:
		# Decryption
		encrypted_seed = select_seed[0]
		bin = binascii.unhexlify(encrypted_seed)
		nonce = bin[:16]
		tag = bin[16:32]
		ciphertext = bin[32:]
		private_key = hashlib.scrypt(aes_password.encode('utf-8'), salt=(str(user_id)+salt).encode('utf-8'), n=2**16, r=16, p=1, maxmem=2**28, dklen=32)
		cipher = AES.new(private_key, AES.MODE_EAX, nonce)
		data = cipher.decrypt_and_verify(ciphertext, tag)
		seed = binascii.hexlify(data).decode().upper()
	except Exception as e:
		seed = False
	return(seed)

def mysql_set_seed(user_id, seed):
	# Encryption
	private_key = hashlib.scrypt(aes_password.encode('utf-8'), salt=(str(user_id)+salt).encode('utf-8'), n=2**16, r=16, p=1, maxmem=2**28, dklen=32)
	cipher = AES.new(private_key, AES.MODE_EAX)
	ciphertext, tag = cipher.encrypt_and_digest(binascii.unhexlify(seed))
	hex_data = binascii.hexlify(cipher.nonce+tag+ciphertext).decode()
	# MySQL record
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("INSERT INTO rai_bot_seeds SET user_id = %s, seed = %s")
	cursor.execute(query, (int(user_id), hex_data,))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_send_all(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT active FROM rai_bot_send_all WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	send = cursor.fetchone()
	cursor.close()
	cnx.close()
	try:
		send = send[0]
	except Exception as e:
		send = False
	return(send)

def mysql_set_send_all(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("REPLACE INTO rai_bot_send_all SET user_id = %s, active = 1")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_send_all(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = ("DELETE FROM rai_bot_send_all WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_faucet():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT threshold, reward, claimers FROM rai_faucet WHERE id = 1")
	cursor.execute(query)
	faucet = cursor.fetchone()
	cursor.close()
	cnx.close()
	return(faucet)

def mysql_set_faucet(threshold, reward, claimers):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_faucet = "REPLACE INTO rai_faucet SET id = 1, threshold = %s, reward = %s, claimers = %s"
	cursor.execute(add_faucet, (int(threshold), int(reward), int(claimers),))
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_select_nonce(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = ("SELECT nonce FROM rai_bot_nonces WHERE user_id = %s")
	cursor.execute(query, (int(user_id),))
	nonce = cursor.fetchone()
	cursor.close()
	cnx.close()
	try:
		nonce = nonce[0]
	except Exception as e:
		nonce = False
	return(nonce)

def mysql_query(query):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	for result in cursor.execute(query, multi=True):
		pass
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_query_select(query):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	cursor.execute(query)
	array = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(array)
