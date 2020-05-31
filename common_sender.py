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

import logging
import math

# Parse config
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
log_file_frontiers = config.get('main', 'log_file_frontiers')
fee_account = config.get('main', 'fee_account')
welcome_account = config.get('main', 'welcome_account')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file_frontiers)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

faucet_account = 'nano_13ezf4od79h1tgj9aiu4djzcmmguendtjfuhwfukhuucboua8cpoihmh8byo'

# MySQL requests
from common_mysql import *

def find_sender(item, account, sender_account, balance, lang_text):
	sender = sender_account
	if (item['type'] == 'receive'):
		lang_id = mysql_select_language(account[0]) # language by user ID
		sender = lang_text('frontiers_sender_account', lang_id).format(sender_account)
		# Sender info
		if (sender_account == faucet_account):
			sender = lang_text('frontiers_sender_faucet', lang_id)
		elif ((sender_account == fee_account) or (sender_account == welcome_account)):
			sender = lang_text('frontiers_sender_bot', lang_id)
		elif (sender_account == account[1]):
			sender = lang_text('frontiers_sender_self', lang_id)
		else:
			# Sender from bot
			account_mysql = mysql_select_by_account_extra(sender_account)
			if (account_mysql is False):
				# sender from users accounts
				account_mysql = mysql_select_by_account(sender_account)
				if (account_mysql is not False):
					if ((account_mysql[4] is not None) and (account_mysql[4])):
						sender = lang_text('frontiers_sender_username', lang_id).format(account_mysql[4])
					elif (sender_account != account[1]):
						sender = lang_text('frontiers_sender_users', lang_id).format(sender_account)
			else:
				# sender from extra accounts
				user_sender = mysql_select_user(account_mysql[0])
				if ((user_sender[8] is not None) and (user_sender[8]) and (account[0] != account_mysql[0])):
					sender = lang_text('frontiers_sender_username', lang_id).format(user_sender[8])
				elif (sender_account != account[1]):
					sender = lang_text('frontiers_sender_users', lang_id).format(sender_account)
		try:
			z = account[5]
			sender = lang_text('frontiers_sender_by', lang_id).format(sender, account[1].replace("_", "\_"))
			mysql_update_balance_extra(account[1], balance)
		except IndexError as e:
			mysql_update_balance(account[1], balance)
		logging.info(sender)
		logging.info(sender_account)
	return sender
