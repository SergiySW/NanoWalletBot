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

# MySQL requests

mysql_config = {
  'user': mysql_user,
  'password': mysql_pass,
  'host': mysql_server,
  'database': mysql_database,
  'raise_on_warnings': True,
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


def mysql_select_user(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT * FROM rai_bot WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	account = cursor.fetchone()
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


def mysql_select_accounts_balances():
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor(buffered=True)
	query = "SELECT user_id, balance FROM rai_bot"
	cursor.execute(query)
	accounts_balances = cursor.fetchall()
	cursor.close()
	cnx.close()
	return(accounts_balances)



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
#	print(query)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

#@run_async
def mysql_update_balance(account, balance):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET balance = '{0}' WHERE account LIKE '{1}'".format(balance, account)
#	print(query)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

#@run_async
def mysql_update_username(user_id, username):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET username = '{0}' WHERE user_id = {1}".format(username, user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

#@run_async
def mysql_update_send_amount(account, amount):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_amount = '{0}' WHERE account LIKE '{1}'".format(amount, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

#@run_async
def mysql_update_send_destination(account, send_account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_destination = '{0}' WHERE account LIKE '{1}'".format(send_account, account)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

#@run_async
def mysql_update_send_clean(account):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "UPDATE rai_bot SET send_destination = NULL, send_amount = 0 WHERE account LIKE '{0}'".format(account)
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
	query = "SELECT SUM(balance) FROM rai_bot"
	cursor.execute(query)
	balance = cursor.fetchone()[0]
	#price = mysql_select_price()[0]
	cursor.close()
	cnx.close()
	stats = "Total users: {0}\nTotal balance: {1} Mrai (XRB)".format("{:,}".format(users), "{:,}".format(balance))
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
	query = "SELECT last_price, high_price, low_price, ask_price, bid_price, volume FROM rai_price WHERE id = 1"
	cursor.execute(query)
	price = cursor.fetchone()
	cursor.close()
	cnx.close()
	return(price)

#@run_async
def mysql_set_price(last_price, high_price, low_price, ask_price, bid_price, volume):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	add_price = "REPLACE INTO rai_price SET id = 1, last_price = '{0}', high_price = '{1}', low_price = '{2}', ask_price = '{3}', bid_price = '{4}', volume = '{5}'".format(last_price, high_price, low_price, ask_price, bid_price, volume)
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

#@run_async
def mysql_set_blacklist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "INSERT INTO rai_black_list SET user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()

#@run_async
def mysql_delete_blacklist(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	query = "DELETE FROM rai_black_list WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	cnx.commit()
	cursor.close()
	cnx.close()



#@run_async
from datetime import datetime
import time
def mysql_ddos_protector(user_id):
	cnx = mysql.connector.connect(**mysql_config)
	cursor = cnx.cursor()
	
	returned = None
	timestamp = int(time.time())

	query = "SELECT datetime FROM rai_bot_access WHERE user_id = {0}".format(user_id)
	cursor.execute(query)
	date_time = cursor.fetchone()
	if (date_time is not None):
		ddos_protect = 1 + int(date_time[0])
		date_protect = int(ddos_protect_seconds) + int(date_time[0])
		if (ddos_protect > timestamp):
			returned = True
		elif (date_protect > timestamp):
			returned = False
		else:
			returned = None
	add_user = "REPLACE INTO rai_bot_access SET user_id = {0}, datetime = {1}".format(user_id, timestamp)
	cursor.execute(add_user)
	cnx.commit()
	cursor.close()
	cnx.close()
	return returned
