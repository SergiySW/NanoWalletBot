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

import ConfigParser
import mysql.connector

config = ConfigParser.ConfigParser()
config.read('bot.cfg')
mysql_server = config.get('mysql', 'mysql_server')
mysql_database = config.get('mysql', 'mysql_database')
mysql_user = config.get('mysql', 'mysql_user')
mysql_pass = config.get('mysql', 'mysql_pass')
ddos_protect_seconds = config.get('main', 'ddos_protect_seconds')
feeless_seconds = int(config.get('main', 'feeless_seconds'))

# MySQL requests

mysql_config = {
  'user': mysql_user,
  'password': mysql_pass,
  'host': mysql_server,
  'database': mysql_database,
  'raise_on_warnings': True,
  'use_unicode': True,
  'charset': 'utf8',
}

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
	query = "SELECT * FROM rai_bot WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	account = cursor.fetchone()
	cursor.close()
	cnx.close()
	return(account)


def mysql_select_user_extra(user_id, active = False):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	if (active is not False):
		query = "SELECT * FROM rai_bot_extra WHERE user_id = {0} AND send_from = 1".format(user_id)
	else:
		query = "SELECT * FROM rai_bot_extra WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	account = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(account)


def mysql_select_accounts_list():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT user_id, account, frontier, balance, username FROM rai_bot"
	cursor.execute(query)
	accounts_list = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_list)


def mysql_select_by_account(xrb_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT user_id, account, frontier, balance, username FROM rai_bot WHERE account LIKE '{0}'".format(xrb_account)
	cursor.execute(query)
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
	query = "SELECT user_id, account, frontier, balance, extra_id, '1' as extra FROM rai_bot_extra WHERE account LIKE '{0}'".format(xrb_account)
	cursor.execute(query)
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
	query = "SELECT user_id, account, frontier, balance, extra_id FROM rai_bot_extra WHERE user_id = {0} AND extra_id = {1}".format(user_id, extra_id)
	cursor.execute(query)
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
	query = "SELECT user_id, balance FROM rai_bot"
	cursor.execute(query)
	accounts_balances = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_balances)


def mysql_select_accounts_list_extra():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT user_id, account, frontier, balance, extra_id, '1' as extra FROM rai_bot_extra"
	cursor.execute(query)
	accounts_list = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_list)


def mysql_user_existance(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT * FROM rai_bot WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
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
	query = "UPDATE rai_bot SET frontier = '{0}' WHERE account LIKE '{1}'".format(frontier, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_frontier_extra(account, frontier):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot_extra SET frontier = '{0}' WHERE account LIKE '{1}'".format(frontier, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_balance(account, balance):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET balance = '{0}' WHERE account LIKE '{1}'".format(balance, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_balance_extra(account, balance):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot_extra SET balance = '{0}' WHERE account LIKE '{1}'".format(balance, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_username(user_id, username):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET username = '{0}' WHERE user_id = {1}".format(username, user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_amount(account, amount):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_amount = '{0}' WHERE account LIKE '{1}'".format(amount, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_destination(account, send_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_destination = '{0}' WHERE account LIKE '{1}'".format(send_account, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_from(from_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot_extra SET send_from = 1 WHERE account LIKE '{0}'".format(from_account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean(account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_destination = NULL, send_amount = 0 WHERE account LIKE '{0}'".format(account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean_extra(from_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot_extra SET send_from = 0 WHERE account LIKE '{0}'".format(from_account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean_extra_user(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot_extra SET send_from = 0 WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_update_send_clean_all():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_destination = NULL, send_amount = 0"
	cursor.execute(query)
	cnx.commit()
	query = "UPDATE rai_bot_extra SET send_from = 0"
	cursor.execute(query)
	cnx.commit()
	query = "TRUNCATE rai_bot_send_all"
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_account_by_username(username):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT account FROM rai_bot WHERE username LIKE '{0}'".format(username)
	cursor.execute(query)
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
	query = "SELECT COUNT(*) FROM rai_bot"
	cursor.execute(query)
	users = cursor.fetchone()[0]
	query = "SELECT COUNT(*) FROM rai_bot_extra"
	cursor.execute(query)
	accounts = users + cursor.fetchone()[0]
	query = "SELECT SUM(balance) FROM rai_bot"
	cursor.execute(query)
	balance = int(cursor.fetchone()[0] / (10 ** 6))
	query = "SELECT SUM(balance) FROM rai_bot_extra"
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
	query = "SELECT balance FROM rai_bot WHERE account LIKE '{0}'".format(account)
	cursor.execute(query)
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
	query = "INSERT INTO rai_bot_passwords SET user_id = {0}, password = '{1}'".format(user_id, hex)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_check_password(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT password FROM rai_bot_passwords WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
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
	query = "DELETE FROM rai_bot_passwords WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_price():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume FROM rai_price"
	cursor.execute(query)
	price = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(price)

def mysql_set_price(id, last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_price = "REPLACE INTO rai_price SET id = '{0}', last_price = '{1}', high_price = '{2}', low_price = '{3}', ask_price = '{4}', bid_price = '{5}', volume = '{6}', btc_volume = '{7}'".format(id, last_price, high_price, low_price, ask_price, bid_price, volume, btc_volume)
	cursor.execute(add_price)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_blacklist():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT user_id FROM rai_black_list"
	cursor.execute(query)
	#black_list = cursor.fetchall()
	black_list = [item[0] for item in cursor.fetchall()]
	cursor.close()
	cnx.close()
	return(black_list)

def mysql_set_blacklist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "INSERT INTO rai_black_list SET user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_blacklist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "DELETE FROM rai_black_list WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_set_language(user_id, language):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "REPLACE INTO rai_bot_language SET user_id = {0}, language = '{1}'".format(user_id, language)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_select_language(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT language FROM rai_bot_language WHERE user_id = {0}".format(user_id)
	try:
		cursor.execute(query)
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
	query = "SELECT language FROM rai_bot_language WHERE user_id = {0}".format(user_id)
	try:
		cursor.execute(query)
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
	query = "REPLACE INTO rai_bot_hide_list SET user_id = {0}, hide = {1}".format(user_id, hide)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()
	mysql_update_send_clean_extra_user(user_id)

def mysql_select_hide(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT hide FROM rai_bot_hide_list WHERE user_id = {0}".format(user_id)
	try:
		cursor.execute(query)
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
	query = "INSERT INTO rai_send_list SET user_id = {0}, text = '{1}'".format(user_id, text)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_sendlist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "DELETE FROM rai_send_list WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_select_sendlist():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT user_id, text FROM rai_send_list "
	cursor.execute(query)
	price = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(price)


def mysql_select_frontiers():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT json FROM rai_frontiers"
	cursor.execute(query)
	price = cursor.fetchone()[0]
	cursor.close()
	cnx.close()
	return(price)

def mysql_set_frontiers(json):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_frontiers = "REPLACE INTO rai_frontiers SET id = 1, json = '{0}'".format(json)
	cursor.execute(add_frontiers)
	cnx.commit()
	cursor.close()
	cnx.close()


from datetime import datetime
import time
def mysql_ddos_protector(user_id, message_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	
	returned = None
	timestamp = int(time.time())

	query = "SELECT datetime, message_id FROM rai_bot_access WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
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
	add_user = "REPLACE INTO rai_bot_access SET user_id = {0}, datetime = {1}, message_id = {2}".format(user_id, timestamp, message_id)
	cursor.execute(add_user)
	cnx.commit()
	cursor.close()
	cnx.close()
	return returned

def mysql_select_send_time(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT datetime FROM rai_bot_send_time WHERE user_id = {0}".format(user_id)
	timestamp = int(time.time())
	try:
		cursor.execute(query)
		old_timestamp = int(cursor.fetchone()[0])
		if ((timestamp - old_timestamp) >= feeless_seconds):
			returned = True
		else:
			returned = False
	except TypeError:
		add_timestamp = "REPLACE INTO rai_bot_send_time SET user_id = {0}, datetime = 0".format(user_id)
		cursor.execute(add_timestamp)
		cnx.commit()
		returned = True
	cursor.close()
	cnx.close()
	return returned

def mysql_update_send_time(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	timestamp = int(time.time())
	add_timestamp = "REPLACE INTO rai_bot_send_time SET user_id = {0}, datetime = {1}".format(user_id, timestamp)
	cursor.execute(add_timestamp)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_price_high():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT * FROM rai_price_high"
	cursor.execute(query)
	array = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(array)

def mysql_set_price_high(user_id, price, exchange = 0):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "REPLACE INTO rai_price_high SET user_id = {0}, price = {1}, exchange = {2}".format(user_id, price, exchange)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_price_high(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "DELETE FROM rai_price_high WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_price_low():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT * FROM rai_price_low"
	cursor.execute(query)
	array = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(array)

def mysql_set_price_low(user_id, price, exchange = 0):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "REPLACE INTO rai_price_low SET user_id = {0}, price = {1}, exchange = {2}".format(user_id, price, exchange)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_price_low(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "DELETE FROM rai_price_low WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_seed(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT seed FROM rai_bot_seeds WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	seed = cursor.fetchone()
	cursor.close()
	cnx.close()
	try:
		seed = seed[0]
	except Exception as e:
		seed = False
	return(seed)

def mysql_set_seed(user_id, seed):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "INSERT INTO rai_bot_seeds SET user_id = {0}, seed = '{1}'".format(user_id, seed)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()


def mysql_select_send_all(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT active FROM rai_bot_send_all WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
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
	query = "REPLACE INTO rai_bot_send_all SET user_id = {0}, active = 1".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

def mysql_delete_send_all(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "DELETE FROM rai_bot_send_all WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

