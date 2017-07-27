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
"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram import Bot, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from telegram.error import BadRequest, RetryAfter, TimedOut, NetworkError
import logging
import urllib3, certifi, socket, json, re
import hashlib, binascii, string, math
from mysql.connector import ProgrammingError
from time import sleep
import os, sys

# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
api_key = config.get('main', 'api_key')
url = config.get('main', 'url')
log_file = config.get('main', 'log_file')
log_file_messages = config.get('main', 'log_file_messages')
domain = config.get('main', 'domain')
listen_port = config.get('main', 'listen_port')
qr_folder_path = config.get('main', 'qr_folder_path')
wallet = config.get('main', 'wallet')
wallet_password = config.get('main', 'password')
fee_account = config.get('main', 'fee_account')
fee_amount = int(config.get('main', 'fee_amount'))
raw_fee_amount = fee_amount * (10 ** 24)
welcome_account = config.get('main', 'welcome_account')
welcome_amount = int(config.get('main', 'welcome_amount'))
raw_welcome_amount = welcome_amount * (10 ** 24)
incoming_fee_text = '\n'
min_send = int(config.get('main', 'min_send'))
ddos_protect_seconds = config.get('main', 'ddos_protect_seconds')
admin_list = json.loads(config.get('main', 'admin_list'))
extra_limit = int(config.get('main', 'extra_limit'))
LIST_OF_FEELESS = json.loads(config.get('main', 'feeless_list'))
salt = config.get('password', 'salt')
block_count_difference_threshold = int(config.get('monitoring', 'block_count_difference_threshold'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)

logger = logging.getLogger(__name__)

account_url = 'https://raiblockscommunity.net/account/index.php?acc='
hash_url = 'https://raiblockscommunity.net/block/index.php?h='
faucet_url = 'https://faucet.raiblockscommunity.net/form.php'
summary_url = 'https://raiblockscommunity.net/page/summary.php?json=1'

# MySQL requests
from common_mysql import *

# QR code handler
from common_qr import *

# Request to node
from common_rpc import *

# Common functions
from common import *


unlock(wallet, wallet_password)

# Restrict access to admins only
from functools import wraps
def restricted(func):
	@wraps(func)
	def wrapped(bot, update, *args, **kwargs):
		# extract user_id from arbitrary update
		try:
			user_id = update.message.from_user.id
		except (NameError, AttributeError):
			try:
				user_id = update.inline_query.from_user.id
			except (NameError, AttributeError):
				try:
					user_id = update.chosen_inline_result.from_user.id
				except (NameError, AttributeError):
					try:
						user_id = update.callback_query.from_user.id
					except (NameError, AttributeError):
						print("No user_id available in update.")
						return
		if user_id not in admin_list:
			print("Unauthorized access denied for {0}.".format(user_id))
			return
		return func(bot, update, *args, **kwargs)
	return wrapped


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.

with open('language.json') as lang_file:    
	language = json.load(lang_file)
def lang(user_id, text_id):
	lang_id = mysql_select_language(user_id)
	try:
		return language[lang_id][text_id]
	except KeyError:
		return language['en'][text_id]

def lang_text(text_id, lang_id):
	try:
		return language[lang_id][text_id]
	except KeyError:
		return language['en'][text_id]

@run_async
def custom_keyboard(bot, chat_id, buttons, text):
	reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard = True)
	try:
		bot.sendMessage(chat_id=chat_id, 
					 text=text, 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True,
					 reply_markup=reply_markup)
	except BadRequest:
		bot.sendMessage(chat_id=chat_id, 
					 text=replace_unsafe(text), 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True,
					 reply_markup=reply_markup)
	except RetryAfter:
		sleep(240)
		bot.sendMessage(chat_id=chat_id, 
					 text=text, 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True,
					 reply_markup=reply_markup)
	except:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, 
					 text=text, 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True,
					 reply_markup=reply_markup)

@run_async
def default_keyboard(bot, chat_id, text):
	custom_keyboard(bot, chat_id, lang(chat_id, 'menu'), text)

@run_async
def lang_keyboard(lang_id, bot, chat_id, text):
	custom_keyboard(bot, chat_id, lang_text('menu', lang_id), text)

@run_async
def hide_keyboard(bot, chat_id, text):
	reply_markup = ReplyKeyboardRemove()
	try:
		bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)
	except:
		sleep(1)
		bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)

@run_async
def typing_illusion(bot, chat_id):
	try:
		bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING) # typing illusion
	except:
		sleep(1)
		bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING) # typing illusion


@run_async
def ddos_protection(bot, update, callback):
	user_id = update.message.from_user.id
	message_id = int(update.message.message_id)
	ddos = mysql_ddos_protector(user_id, message_id)
	if (ddos == True):
		logging.warn('DDoS or double message by user {0} message {1}'.format(user_id, message_id))
	elif (ddos == False):
		text_reply(update, lang(user_id, 'ddos_error').format(ddos_protect_seconds))
		logging.warn('Too fast request by user {0}'.format(user_id))
	else:
		callback(bot, update)

@run_async
def ddos_protection_args(bot, update, args, callback):
	user_id = update.message.from_user.id
	message_id = int(update.message.message_id)
	ddos = mysql_ddos_protector(user_id, message_id)
	if (ddos == True):
		logging.warn('DDoS or double message by user {0} message {1}'.format(user_id, message_id))
	elif (ddos == False):
		text_reply(update, lang(user_id, 'ddos_error').format(ddos_protect_seconds))
		logging.warn('Too fast request by user {0}'.format(user_id))
	else:
		callback(bot, update, args)


@run_async
def info_log(update):
	result = {}
	result['text'] = update.message.text
	result['user_id'] = update.message.from_user.id
	result['username'] = update.message.from_user.username
	result['first_name'] = update.message.from_user.first_name
	result['last_name'] = update.message.from_user.last_name
	result['timestamp'] = int(time.mktime(update.message.date.timetuple()))
	result['message_id'] = update.message.message_id
	logging.info(result)

@run_async
def language_select(bot, update, args):
	info_log(update)
	ddos_protection_args(bot, update, args, language_select_callback)

@run_async
def language_select_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	if (len(args) > 0):
		lang_id = args[0].lower()
		if (lang_id in language['common']['language_list']):
			try:
				mysql_set_language(user_id, lang_id)
				start_text(bot, update)
			except:
				text_reply(update, lang(user_id, 'language_error'))
		else:
			text_reply(update, lang(user_id, 'language_error'))
			logging.info('Language change failed for user {0}'.format(user_id))
	else:
		text_reply(update, lang(user_id, 'language_command'))


@run_async
def start(bot, update):
	info_log(update)
	ddos_protection(bot, update, start_text)


@run_async
def start_text(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_exist_language(user_id)
	if (lang_id is False):
		try:
			lang_id = update.message.from_user.language_code
			if (lang_id in language['common']['language_list']):
				mysql_set_language(user_id, lang_id)
			else:
				lang_id = mysql_select_language(user_id)
		except Exception as e:
			lang_id = mysql_select_language(user_id)
	text_reply(update, lang_text('start_introduce', lang_id))
	sleep(1)
	lang_keyboard(lang_id, bot, chat_id, lang_text('start_basic_commands', lang_id).format(mrai_text(fee_amount), mrai_text(min_send), incoming_fee_text))
	sleep(1)
	message_markdown(bot, chat_id, lang_text('start_learn_more', lang_id))
	# Check user existance in database
	exist = mysql_user_existance(user_id)
	# Select language if 1st time
	if (exist is False):
		sleep(1)
		custom_keyboard(bot, chat_id, lang_text('language_keyboard', 'common'), lang_text('language_selection', 'common'))


@run_async
def help(bot, update):
	info_log(update)
	ddos_protection(bot, update, help_callback)

@run_async
def help_callback(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	lang_keyboard(lang_id, bot, chat_id, lang_text('help_advanced_usage', lang_id).format(mrai_text(fee_amount), mrai_text(min_send), incoming_fee_text))
	sleep(1)
	message_markdown(bot, chat_id, lang_text('help_learn_more', lang_id))


@run_async
def help_text(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	lang_keyboard(lang_id, bot, chat_id, lang_text('start_basic_commands', lang_id).format(mrai_text(fee_amount), mrai_text(min_send), incoming_fee_text))
	sleep(1)
	message_markdown(bot, chat_id, lang_text('help_learn_more', lang_id))



def user_id(bot, update):
	user_id = update.message.from_user.id
	text_reply(update, user_id)


@run_async
def block_count(bot, update):
	info_log(update)
	ddos_protection(bot, update, block_count_callback)

@run_async
def block_count_callback(bot, update):
	user_id = update.message.from_user.id
	count = rpc({"action": "block_count"}, 'count')
	text_reply(update, "{:,}".format(int(count)))
#	default_keyboard(bot, update.message.chat_id, r)
	# Admin block count check from raiblockscommunity.net
	if (user_id in admin_list):
		http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
		response = http.request('GET', summary_url)
		json_data = json.loads(response.data)
		community_count = json_data['blocks']
		if (math.fabs(int(community_count) - int(count)) > block_count_difference_threshold):
			text_reply(update, 'Community: {0}'.format("{:,}".format(int(community_count))))
			reference_count = int(reference_block_count())
			sleep(1)
			text_reply(update, 'Reference: {0}'.format("{:,}".format(reference_count)))
			response = http.request('GET', 'https://raiwallet.info/api/block_count.php')
			raiwallet_count = int(response.data)
			sleep(1)
			text_reply(update, 'raiwallet.info: {0}'.format("{:,}".format(raiwallet_count)))


# broadcast
@restricted
def broadcast(bot, update):
	info_log(update)
	bot = Bot(api_key)
	# list users from MySQL
	accounts_list = mysql_select_accounts_balances()
	# some users are bugged & stop broadcast - they deleted chat with bot. So we blacklist them
	BLACK_LIST = mysql_select_blacklist()
	for account in accounts_list:
		# if not in blacklist and has balance
		if ((account[0] not in BLACK_LIST) and (int(account[1]) > 0)):
			mysql_set_blacklist(account[0])
			print(account[0])
			push_simple(bot, account[0], update.message.text.replace('/broadcast ', ''))
			sleep(0.2)
			mysql_delete_blacklist(account[0]) # if someone deleted chat, broadcast will fail and he will remain in blacklist


# bootstrap
@restricted
def bootstrap(bot, update):
	info_log(update)
	bootstrap_multi()
	bot.sendMessage(update.message.chat_id, "Bootstraping...")



@restricted
def restart(bot, update):
	bot.sendMessage(update.message.chat_id, "Bot is restarting...")
	sleep(0.2)
	os.execl(sys.executable, sys.executable, *sys.argv)
	

#@restricted
@run_async
def account(bot, update):
	info_log(update)
	ddos_protection(bot, update, account_text)

@run_async
def account_list(bot, update):
	info_log(update)
	ddos_protection(bot, update, account_text_list)

@run_async
def account_text_list(bot, update):
	account_text(bot, update, True)

@run_async
def accounts_hide(bot, update):
	info_log(update)
	ddos_protection(bot, update, accounts_hide_callback)

@run_async
def accounts_hide_callback(bot, update):
	user_id = update.message.from_user.id
	hide = mysql_select_hide(user_id)
	if (hide == 0):
		extra_accounts = mysql_select_user_extra(user_id)
		if (len(extra_accounts) > 0):
			mysql_set_hide(user_id, 1)
	else:
		mysql_set_hide(user_id, 0)
	account_text(bot, update)

@run_async
def account_text(bot, update, list = False):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	username=update.message.from_user.username
	if (username is None):
		username = ''
	#print(username)
	m = mysql_select_user(user_id)
	try:
		r = m[2]
		qr_by_account(r)
		balance = account_balance(r)
		total_balance = balance
		# FEELESS
		if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
			final_fee_amount = 0
		else:
			final_fee_amount = fee_amount
		# FEELESS
		max_send = balance - final_fee_amount
		extra_accounts = mysql_select_user_extra(user_id)
		extra_array = []
		for extra_account in extra_accounts:
			extra_array.append(extra_account[3])
		if (len(extra_accounts) > 0):
			balances = accounts_balances(extra_array)
		hide = mysql_select_hide(user_id)
		num = 0
		for extra_account in extra_accounts:
			num = num + 1
			total_balance = total_balance + balances[extra_account[3]]
		# price
		price = mysql_select_price()
		if (int(price[0][0]) > 0):
			last_price = ((float(price[0][0]) * float(price[0][6])) + (float(price[1][0]) * float(price[1][6]))) / (float(price[0][6]) + float(price[1][6]))
		else:
			last_price = int(price[1][0])
		btc_price = last_price / (10 ** 14)
		btc_balance = ('%.8f' % (btc_price * total_balance))
		# price
		if (list is not False):
			text = 'Total: *{0} XRB (Mrai)*\n~ {1} BTC\n/{3}\n{4}'.format(mrai_text(total_balance), btc_balance, '', lang_text('account_add', lang_id).encode("utf8").replace("_", "\_"), lang_text('send_all', lang_id).encode("utf8"))
			message_markdown(bot, chat_id, text)
			sleep(1)
			message_markdown(bot, chat_id, '*0.* {0} XRB (Mrai)'.format(mrai_text(balance)))
			sleep(1)
			message_markdown(bot, chat_id, '*{0}*'.format(r))
			sleep(1)
			for extra_account in extra_accounts:
				message_markdown(bot, chat_id, '*{0}.* {1} XRB (Mrai)  /{2} {0}'.format(extra_account[2], mrai_text(balances[extra_account[3]]), lang_text('send_from_command', lang_id).encode("utf8").replace("_", "\_")))
				sleep(1)
				text_reply(update, extra_account[3])
				sleep(1)
		else:
			if ((balance == 0) and (list is False)):
				text = lang_text('account_balance_zero', lang_id).format(faucet_url, r)
			elif ((max_send < min_send) and (list is False)):
				text = lang_text('account_balance_low', lang_id).format(faucet_url, r, mrai_text(balance), mrai_text(final_fee_amount), mrai_text(min_send))
			else:
				if (balance == total_balance):
					text = lang_text('account_balance', lang_id).format(mrai_text(balance), btc_balance, mrai_text(max_send))
				else:
					text = lang_text('account_balance_total', lang_id).format(mrai_text(balance), btc_balance, mrai_text(max_send), mrai_text(total_balance))
			text = '{0}\n\n{1}'.format(text.encode("utf8"), lang_text('account_your', lang_id).encode("utf8"))
			message_markdown(bot, chat_id, text)
			sleep(1)
			message_markdown(bot, chat_id, '*{0}*'.format(r))
			sleep(1)
			if ((num > 3) and (hide == 0)):
				message_markdown(bot, chat_id, lang_text('account_history', lang_id).encode("utf8").format(r, account_url, faucet_url, '').replace(lang_text('account_add', lang_id).encode("utf8").replace("_", "\_"), lang_text('account_list', lang_id).encode("utf8").replace("_", "\_"))) # full accounts list
			elif (hide == 1):
				message_markdown(bot, chat_id, lang_text('account_history', lang_id).encode("utf8").format(r, account_url, faucet_url, '').replace(lang_text('account_add', lang_id).encode("utf8").replace("_", "\_"), lang_text('account_list', lang_id).encode("utf8").replace("_", "\_")).replace(lang_text('accounts_hide', lang_id).encode("utf8").replace("_", "\_"), lang_text('accounts_expand', lang_id).encode("utf8").replace("_", "\_"))) # hide-expand
			else:
				message_markdown(bot, chat_id, lang_text('account_history', lang_id).encode("utf8").format(r, account_url, faucet_url, ''))
			sleep(1)
			# list
			if (hide == 0):
				n = 0
				for extra_account in extra_accounts:
					n = n + 1
					if (n <= 3):
						message_markdown(bot, chat_id, '*{0}.* {1} XRB (Mrai)  /{2} {0}'.format(extra_account[2], mrai_text(balances[extra_account[3]]), lang_text('send_from_command', lang_id).encode("utf8").replace("_", "\_")))
						sleep(1)
						text_reply(update, extra_account[3])
						sleep(1)
			# list
			#bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'), caption=r)
			try:
				bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'))
			except (urllib3.exceptions.ProtocolError) as e:
				sleep(3)
				bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'))
			except TimedOut as e:
				sleep(10)
				bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'))
			except NetworkError as e:
				sleep(20)
				bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'))
			seed = mysql_select_seed(user_id)
			check = mysql_check_password(user_id)
			if ((seed is False) and (check is False)):
				sleep(1)
				seed_callback(bot, update, [0])
			elif (check is not False):
				sleep(1)
				text_reply(update, lang_text('seed_protected', lang_id))
	
	except (TypeError):
		r = rpc({"action": "account_create", "wallet": wallet}, 'account')
		qr_by_account(r)
		if ('xrb_' in r): # check for errors
			insert_data = {
			  'user_id': user_id,
			  'account': r,
			  'chat_id': chat_id,
			  'username': username,
			}
			mysql_insert(insert_data)
			text_reply(update, lang_text('account_created', lang_id))
			sleep(1)
			message_markdown(bot, chat_id, '*{0}*'.format(r))
			sleep(1)
			message_markdown(bot, chat_id, lang_text('account_explorer', lang_id).format(r, account_url))
			sleep(1)
			message_markdown(bot, chat_id, lang_text('account_balance_start', lang_id).format(faucet_url, r))
			sleep(1)
			custom_keyboard(bot, chat_id, lang_text('language_keyboard', 'common'), lang_text('language_selection', 'common'))
			try:
				welcome = rpc_send(wallet, welcome_account, r, raw_welcome_amount)
				new_balance = account_balance(welcome_account)
				mysql_update_balance(welcome_account, new_balance)
				mysql_update_frontier(welcome_account, welcome)
			except Exception as e:
				logging.exception("message")
			logging.info('New user registered {0} {1}'.format(user_id, r))
			sleep(2)
			seed_callback(bot, update, [0])
		else:
			text_reply(update, lang_text('account_error', lang_id))


#@restricted
@run_async
def account_add(bot, update):
	info_log(update)
	ddos_protection(bot, update, account_add_callback)


def account_add_callback(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	extra_accounts = mysql_select_user_extra(user_id)
	if (len(extra_accounts) >= extra_limit):
		text_reply(update, lang_text('account_extra_limit', lang_id).format(extra_limit))
	else:
		r = rpc({"action": "account_create", "wallet": wallet}, 'account')
		extra_id = len(mysql_select_user_extra(user_id)) + 1
		if ('xrb_' in r): # check for errors
			insert_data = {
			  'user_id': user_id,
			  'account': r,
			  'extra_id': extra_id,
			}
			mysql_insert_extra(insert_data)
			text_reply(update, lang_text('account_created', lang_id))
			sleep(1)
			message_markdown(bot, chat_id, '[{0}]({1}{0})'.format(r, account_url))
			logging.info('New account registered {0} {1}'.format(user_id, r))
		else:
			text_reply(update, lang_text('account_error', lang_id))


@run_async
def send(bot, update, args):
	info_log(update)
	ddos_protection_args(bot, update, args, send_callback)


@run_async
def send_from(bot, update, args):
	info_log(update)
	ddos_protection_args(bot, update, args, send_from_callback)


@run_async
def send_from_callback(bot, update, args):
	user_id = update.message.from_user.id
	if (len(args) > 0):
		if ('xrb_' in args[0]):
			from_account = mysql_select_by_account_extra(args[0])
		else:
			try:
				extra_id = int(args[0].replace('.',''))
				from_account = mysql_select_by_id_extra(user_id, extra_id)
			except (ValueError, ProgrammingError) as e:
				from_account = False
				text_reply(update, lang(user_id, 'value_error'))
		try:
			if (from_account is not False):
				if (int(user_id) == int(from_account[0])):
					args = args[1:]
					send_callback(bot, update, args, from_account)
				else:
					text_reply(update, lang(user_id, 'send_from_id_error').format(args[0]))
					logging.warn('User {0} trying to steal funds from {1}'.format(user_id, args[0]))
			elif ((int(args[0]) == 0) or (args[0] == 'default')):
				args = args[1:]
				send_callback(bot, update, args)
			else:
				text_reply(update, lang(user_id, 'send_from_id_error').format(args[0]))
		except ValueError as e:
			text_reply(update, lang(user_id, 'value_error'))
	else:
		m = mysql_select_user(user_id)
		chat_id = update.message.chat_id
		lang_id = mysql_select_language(user_id)
		lang_keyboard(lang_id, bot, chat_id, lang_text('send_wrong_command', lang_id).format(mrai_text(min_send), m[2]))


# Instant receiving
@run_async
def receive(destination, send_hash):
	destination_local = mysql_select_by_account(destination)
	if (destination_local is False):
		destination_local = mysql_select_by_account_extra(destination)
	if (destination_local is not False):
		receive = rpc({"action": "receive", "wallet": wallet, "account": destination, "block": send_hash}, 'block')


@run_async
def send_callback(bot, update, args, from_account = 0):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	try:
		# Check user existance in database
		m = mysql_select_user(user_id)
		if (from_account == 0):
			account = m[2]
		else:
			account = from_account[1]
		# Check balance to send
		try:
			balance = account_balance(account)
			# FEELESS
			if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
				final_fee_amount = 0
			else:
				final_fee_amount = fee_amount
			# FEELESS
			max_send = balance - final_fee_amount
			if ((args[0].lower() == 'all') or (args[0].lower() == 'everything')):
				send_amount = max_send
			else:
				send_amount = int(float(args[0]) * (10 ** 6))
			raw_send_amount = send_amount * (10 ** 24)
			if (max_send < min_send):
				text_reply(update, lang_text('send_low_balance', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
			elif (send_amount > max_send):
				text_reply(update, lang_text('send_limit_max', lang_id).format(mrai_text(final_fee_amount), mrai_text(max_send)))
			elif (send_amount < min_send):
				text_reply(update, lang_text('send_limit_min', lang_id).format(mrai_text(min_send)))
				
			else:
				# Check destination address
				destination = args[1]
				if ((len(args) > 2) and ((args[1].lower() == 'mrai') or (args[1].lower() == 'xrb'))):
					destination = args[2]
				# if destination is username
				if (destination.startswith('@') and (len(destination) > 3 )):
					username = destination.replace('@', '')
					try:
						dest_account = mysql_account_by_username(username)
						if (dest_account is not False):
							destination = dest_account
						else:
							text_reply(update, lang_text('send_user_not_found', lang_id).format(destination))
					except UnicodeEncodeError as e:
						text_reply(update, lang_text('send_user_not_found', lang_id).format(destination))
				destination = destination.encode("utf8").replace('­','').replace('\r','').replace('\n','');
				destination = destination.replace(r'[^[13456789abcdefghijkmnopqrstuwxyz_]+', '')
				destination_check = rpc({"action": "validate_account_number", "account": destination}, 'valid')
				# Check password protection
				check = mysql_check_password(user_id)
				if ((len(args) > 3) and ((args[1].lower() == 'mrai') or (args[1].lower() == 'xrb'))):
					password = args[3]
					dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
					hex = binascii.hexlify(dk)
				elif (len(args) > 2):
					password = args[2]
					dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
					hex = binascii.hexlify(dk)
				else:
					hex = False
				# typing_illusion(bot, update.message.chat_id) # typing illusion
				# Check password protection and frontier existance
				if (from_account == 0):
					frontier = m[3]
				else:
					frontier = from_account[2]
				check_frontier = check_block(frontier)
				if ((destination_check == '1') and (check == hex) and (check_frontier)):
					# Sending
					try:
						try:
							send_hash = rpc_send(wallet, account, destination, raw_send_amount)
						except Exception as e:
							send_hash = '00000000000000000000000000000000000000000000000000000000000000'
							logging.exception("message")
						if (('000000000000000000000000000000000000000000000000000000000000000' not in send_hash) and ('locked' not in send_hash)):
							receive(destination, send_hash)
							# FEELESS
							if (final_fee_amount > 0):
								try:
									fee = rpc_send(wallet, account, fee_account, raw_fee_amount)
								except Exception as e:
									fee = '00000000000000000000000000000000000000000000000000000000000000'
									logging.exception("message")
							else:
								fee = send_hash
							# FEELESS
							new_balance = account_balance(account)
							if (from_account == 0):
								mysql_update_balance(account, new_balance)
								mysql_update_frontier(account, fee)
							else:
								mysql_update_balance_extra(account, new_balance)
								mysql_update_frontier_extra(account, fee)
							lang_keyboard(lang_id, bot, chat_id, lang_text('send_completed', lang_id).format(mrai_text(final_fee_amount), mrai_text(new_balance)))
							mysql_update_send_time(user_id)
							sleep(1)
							message_markdown(bot, chat_id, '[{0}]({1}{0})'.format(send_hash, hash_url))
							logging.info('Send from {0} to {1}  amount {2}  hash {3}'.format(account, destination, mrai_text(send_amount), send_hash))
							# update username
							if (from_account == 0):
								old_username = m[8]
								username=update.message.from_user.username
								if (username is None):
									username = ''
								if (not (username == old_username)):
									username_text = 'Username updated: @{0} --> @{1}'.format(old_username, username)
									mysql_update_username(user_id, username)
									print(username_text)
									logging.info(username_text)
							# update username
						else:
							logging.warn('Transaction FAILURE! Account {0}'.format(account))
							new_balance = account_balance(account)
							lang_keyboard(lang_id, bot, chat_id, lang_text('send_tx_error', lang_id).format(mrai_text(new_balance)))
							unlock(wallet, wallet_password) # try to unlock wallet
					except (GeneratorExit, ValueError):
						lang_keyboard(lang_id, bot, chat_id, lang_text('send_error', lang_id))
				elif (not (check == hex)):
					text_reply(update, lang_text('password_error', lang_id))
					logging.info('Send failure for user {0}. Reason: Wrong password'.format(user_id))
				elif (not (check_frontier)):
					text_reply(update, lang_text('send_frontier', lang_id))
					logging.info('Send failure for user {0}. Reason: Frontier not found'.format(user_id))
				elif (not (destination.startswith('@'))):
					message_markdown(bot, chat_id, lang_text('send_invalid', lang_id))
		except (ValueError):
			text_reply(update, lang_text('send_digits', lang_id))
	except (TypeError):
		message_markdown(bot, chat_id, lang_text('send_no_account', lang_id))
	except (IndexError):
		lang_keyboard(lang_id, bot, chat_id, lang_text('send_wrong_command', lang_id).format(mrai_text(min_send), m[2]))


@run_async
def send_all(bot, update):
	info_log(update)
	ddos_protection(bot, update, send_all_callback)


@run_async
def send_all_callback(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	m = mysql_select_user(user_id)
	destination = m[2]
	final_fee_amount = 0 # 0 fee to accumulate
	extra_accounts = mysql_select_user_extra(user_id)
	extra_array = []
	for extra_account in extra_accounts:
		extra_array.append(extra_account[3])
	reply = 0
	active = mysql_select_send_all(user_id)
	if ((len(extra_accounts) > 0) and (active is False)):
		balances = accounts_balances(extra_array)
		mysql_set_send_all(user_id)
		for account, balance in balances.items():
			max_send = balance - final_fee_amount
			if (max_send >= min_send):
				if (reply == 0):
					lang_keyboard(lang_id, bot, chat_id, lang_text('send_mass', lang_id))
					reply = 1
				try:
					send_amount = max_send
					raw_send_amount = send_amount * (10 ** 24)
					send_hash = rpc_send(wallet, account, destination, raw_send_amount)
				except Exception as e:
					send_hash = '00000000000000000000000000000000000000000000000000000000000000'
					logging.exception("message")
				if (('000000000000000000000000000000000000000000000000000000000000000' not in send_hash) and ('locked' not in send_hash)):
					receive(destination, send_hash)
					new_balance = account_balance(account)
					mysql_update_balance_extra(account, new_balance)
					mysql_update_frontier_extra(account, send_hash)
					mysql_update_send_time(user_id)
					logging.info('Send from {0} to {1}  amount {2}  hash {3} /send_all'.format(account, destination, mrai_text(send_amount), send_hash))
					sleep(6)
				else:
					logging.warn('Transaction FAILURE! Account {0}'.format(account))
					new_balance = account_balance(account)
					lang_keyboard(lang_id, bot, chat_id, lang_text('send_tx_error', lang_id).format(mrai_text(new_balance)))
		mysql_delete_send_all(user_id)
	if (reply == 0):
		lang_keyboard(lang_id, bot, chat_id, lang_text('error', lang_id))


@run_async
def send_text(bot, update, default = False):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	# FEELESS
	if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	m = mysql_select_user(user_id)
	try:
		account = m[2]
		balance = account_balance(account)
		# extra
		extra_accounts = mysql_select_user_extra(user_id)
		hide = mysql_select_hide(user_id)
		extra_keyboard = [['Default - {0} XRB'.format(mrai_text(balance))]]
		if ((len(extra_accounts) > 0) and (default is False) and (hide == 0)):
			extra_array = []
			for extra_account in extra_accounts:
				extra_array.append(extra_account[3])
			balances = accounts_balances(extra_array)
			for extra_account in extra_accounts:
				if (balances[extra_account[3]] >= (min_send + final_fee_amount)):
					extra_keyboard.append(['{0} - {1} XRB'.format(extra_account[3], mrai_text(balances[extra_account[3]]))])
		if (len(extra_keyboard) <= 1):
			default = True
		if ((default is False) and (hide == 0)):
			custom_keyboard(bot, chat_id, extra_keyboard, lang_text('send_from', lang_id).format(''))
		# extra
		elif (balance >= (final_fee_amount + min_send)):
			text_reply(update, lang_text('send_amount', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
		else:
			text_reply(update, lang_text('send_low_balance', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
	except (TypeError):
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_no_account_text', lang_id))


@run_async
def send_destination(bot, update, text, qr = False):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	# FEELESS
	if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	# Check user existance in database
	m = mysql_select_user(user_id)
	try:
		account = m[2]
		destination = text.encode("utf8").replace('­','').replace('\r','').replace('\n','');
		destination = destination.replace(r'[^[13456789abcdefghijkmnopqrstuwxyz_]+', '')
		destination_check = rpc({"action": "validate_account_number", "account": destination}, 'valid')
		if (destination_check == '1'):
			mysql_update_send_destination(account, destination)
			if (m[6] != 0):
				custom_keyboard(bot, chat_id, lang_text('yes_no', lang_id), lang_text('send_confirm', lang_id).format(mrai_text(m[6]), mrai_text(m[6]+final_fee_amount), destination))
			elif (qr is False):
				text_reply(update, lang_text('send_amount', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
		else:
			message_markdown(bot, chat_id, lang_text('send_invalid', lang_id))
	except (TypeError):
		lang_keyboard(lang_id, bot, chat_id, lang_text('send_no_account_text', lang_id))


@run_async
def send_destination_username(bot, update, text):
	user_id = update.message.from_user.id
	username = text.replace('@', '')
	try:
		account = mysql_account_by_username(username)
		if (account is not False):
			text_reply(update, lang(user_id, 'send_user').format(text, account))
			send_destination(bot, update, account)
		else:
			text_reply(update, lang(user_id, 'send_user_not_found').format(text))
	except UnicodeEncodeError as e:
		text_reply(update, lang(user_id, 'send_user_not_found').format(text))


@run_async
def send_amount(bot, update, text):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	# FEELESS
	if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	# Check user existance in database
	m = mysql_select_user(user_id)
	try:
		account = m[2]
		try:
			extra_account = mysql_select_user_extra(user_id, True)
			if (len(extra_account) > 0):
				balance = account_balance(extra_account[0][3])
			else:
				balance = account_balance(account)
			max_send = balance - final_fee_amount
			send_amount = int(float(text) * (10 ** 6))
			# if less, set 0
			if (max_send < min_send):
				mysql_update_send_clean_extra_user(user_id)
				text_reply(update, lang_text('send_low_balance', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
			elif (send_amount > max_send):
				mysql_update_send_clean_extra_user(user_id)
				text_reply(update, lang_text('send_limit_max', lang_id).format(mrai_text(final_fee_amount), mrai_text(max_send)))
			elif (send_amount < min_send):
				mysql_update_send_clean_extra_user(user_id)
				text_reply(update, lang_text('send_limit_min', lang_id).format(mrai_text(min_send)))
			else:
				mysql_update_send_amount(account, send_amount)
				if (m[5] is not None):
					custom_keyboard(bot, update.message.chat_id, lang_text('yes_no', lang_id), lang_text('send_confirm', lang_id).format(mrai_text(send_amount), mrai_text(send_amount+final_fee_amount), m[5]))
				else:
					lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_destination', lang_id))
		except (ValueError):
			text_reply(update, lang_text('send_digits', lang_id))
	except (TypeError):
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_no_account_text', lang_id))


@run_async
def send_extra(bot, update, text):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	# Check user extra accounts in database
	xrb_account = text.split()[0].encode("utf8").replace('­','').replace('\r','').replace('\n','')
	account = mysql_select_by_account_extra(xrb_account)
	if ((account is not False) and (account[0] == user_id)):
		m = mysql_select_user(user_id)
		if (m[6] != 0):
			mysql_update_send_amount(m[2], 0)
		mysql_update_send_from(xrb_account)
		text_reply(update, lang_text('send_from', lang_id).format(xrb_account))
		sleep(1)
		# FEELESS
		if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
			final_fee_amount = 0
		else:
			final_fee_amount = fee_amount
		# FEELESS
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_amount', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
	else:
		send_destination(bot, update, text)


@run_async
def send_finish(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	m = mysql_select_user(user_id)
	account = m[2]
	send_amount = int(m[6])
	raw_send_amount = send_amount * (10 ** 24)
	destination = m[5]
	mysql_update_send_clean(account)
	extra_account = mysql_select_user_extra(user_id, True)
	if (len(extra_account) > 0):
		account = extra_account[0][3]
		mysql_update_send_clean_extra(account)
	# FEELESS
	if ((user_id in LIST_OF_FEELESS) or (mysql_select_send_time(user_id) is not False)):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	try:
		hide_keyboard(bot, chat_id, lang_text('send_working', lang_id))
		# typing_illusion(bot, chat_id)  # typing illusion
		# Check frontier existance
		frontier = m[3]
		check_frontier = check_block(frontier)
		if (check_frontier):
			try:
				send_hash = rpc_send(wallet, account, destination, raw_send_amount)
			except Exception as e:
				send_hash = '00000000000000000000000000000000000000000000000000000000000000'
				logging.exception("message")
			if (('000000000000000000000000000000000000000000000000000000000000000' not in send_hash) and ('locked' not in send_hash)):
				receive(destination, send_hash)
				# FEELESS
				if (final_fee_amount > 0):
					try:
						fee = rpc_send(wallet, account, fee_account, raw_fee_amount)
					except Exception as e:
						fee = '00000000000000000000000000000000000000000000000000000000000000'
						logging.exception("message")
				else:
					fee = send_hash
				# FEELESS
				new_balance = account_balance(account)
				if (len(extra_account) > 0):
					mysql_update_balance_extra(account, new_balance)
					mysql_update_frontier_extra(account, fee)
				else:
					mysql_update_balance(account, new_balance)
					mysql_update_frontier(account, fee)
				sleep(1)
				lang_keyboard(lang_id, bot, chat_id, lang_text('send_completed', lang_id).format(mrai_text(final_fee_amount), mrai_text(new_balance)))
				mysql_update_send_time(user_id)
				sleep(1)
				message_markdown(bot, chat_id, '[{0}]({1}{0})'.format(send_hash, hash_url))
				logging.info('Send from {0} to {1}  amount {2}  hash {3}'.format(account, destination, mrai_text(send_amount), send_hash))
				# update username
				old_username = m[8]
				username=update.message.from_user.username
				if (username is None):
					username = ''
				if (not (username == old_username)):
					username_text = 'Username updated: @{0} --> @{1}'.format(old_username, username)
					mysql_update_username(user_id, username)
					print(username_text)
					logging.info(username_text)
				# update username
			else:
				logging.warn('Transaction FAILURE! Account {0}'.format(account))
				new_balance = account_balance(account)
				lang_keyboard(lang_id, bot, chat_id, lang_text('send_tx_error', lang_id).format(mrai_text(new_balance)))
				unlock(wallet, wallet_password) # try to unlock wallet
		else:
			text_reply(update, lang_text('send_frontier', lang_id))
			logging.info('Send failure for user {0}. Reason: Frontier not found'.format(user_id))
	except (GeneratorExit, ValueError) as e:
		logging.error(e)
		lang_keyboard(lang_id, bot, chat_id, lang_text('send_error', lang_id))



@run_async
def price(bot, update):
	info_log(update)
	ddos_protection(bot, update, price_text)

@run_async
def price_text(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	price = mysql_select_price()
	last_price_merc = ('%.8f' % (float(price[0][0]) / (10 ** 8)))
	ask_price_merc = ('%.8f' % (float(price[0][3]) / (10 ** 8)))
	bid_price_merc = ('%.8f' % (float(price[0][4]) / (10 ** 8)))
	last_price_grail = ('%.8f' % (float(price[1][0]) / (10 ** 8)))
	ask_price_grail = ('%.8f' % (float(price[1][3]) / (10 ** 8)))
	bid_price_grail = ('%.8f' % (float(price[1][4]) / (10 ** 8)))
	
	high_price = ('%.8f' % (max(float(price[0][1]), float(price[1][1]), float(price[0][0])) / (10 ** 8)))
	low_price = ('%.8f' % (min(float(price[0][2]), float(price[1][2])) / (10 ** 8)))
	volume = int(price[0][5]) + int(price[1][5])
	volume_btc = ('%.2f' % ((float(price[0][6]) + float(price[1][6])) / (10 ** 8)))
	text = lang_text('price', lang_id).format(last_price_merc, ask_price_merc, bid_price_merc, last_price_grail, ask_price_grail, bid_price_grail, high_price, low_price, "{:,}".format(volume), volume_btc)
	lang_keyboard(lang_id, bot, chat_id, text)
	sleep(1)
	message_markdown(bot, chat_id, lang_text('price_options', lang_id))


@run_async
def price_above(bot, update, args):
	info_log(update)
	ddos_protection_args(bot, update, args, price_above_callback)

@run_async
def price_above_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	if (len(args) > 0):
		value = 0
		try:
			value = int(args[0])
		except ValueError as e:
			try:
				value = int(float(args[0]) * (10 ** 8))
			except ValueError as e:
				lang_keyboard(lang_id, bot, chat_id, lang_text('prices_digits', lang_id))
				sleep(1)
				message_markdown(bot, chat_id, '/{0} 10000\n/{0} 0.001'.format(lang_text('price_above', lang_id).encode("utf8").replace("_", "\_")))
		price = mysql_select_price()
		price_high_bitgrail =  max(int(price[1][0]), int(price[1][4]))
		price_high_mercatox =  max(int(price[0][0]), int(price[0][4]))
		price_high = max(price_high_bitgrail, price_high_mercatox)
		exchange = 0
		if (len(args) > 1):
			if (args[1].lower().startswith('bitgrail')):
				price_high = price_high_bitgrail
				exchange = 1
			elif (args[1].lower().startswith('mercatox')):
				price_high = price_high_mercatox
				exchange = 2
		if (value <= price_high):
			btc_price = ('%.8f' % (float(price_high) / (10 ** 8)))
			message_markdown(bot, chat_id, lang_text('prices_above', lang_id).format('exchanges', btc_price))
		elif ((value > 0) and (value < 4294967295)):
			btc_value = ('%.8f' % (float(value) / (10 ** 8)))
			mysql_set_price_high(user_id, value, exchange)
			message_markdown(bot, chat_id, lang_text('prices_success', lang_id).format(btc_value))
		else:
			lang_keyboard(lang_id, bot, chat_id, lang_text('error', lang_id))
	else:
		lang_keyboard(lang_id, bot, chat_id, lang_text('prices_digits', lang_id))
		sleep(1)
		message_markdown(bot, chat_id, '/{0} 10000\n/{0} 0.001'.format(lang_text('price_above', lang_id).encode("utf8").replace("_", "\_")))


@run_async
def price_below(bot, update, args):
	info_log(update)
	ddos_protection_args(bot, update, args, price_below_callback)

@run_async
def price_below_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	if (len(args) > 0):
		value = 0
		try:
			value = int(args[0])
		except ValueError as e:
			try:
				value = int(float(args[0]) * (10 ** 8))
			except ValueError as e:
				lang_keyboard(lang_id, bot, chat_id, lang_text('prices_digits', lang_id))
				sleep(1)
				message_markdown(bot, chat_id, '/{0} 10000\n/{0} 0.001'.format(lang_text('price_below', lang_id).encode("utf8").replace("_", "\_")))
		price = mysql_select_price()
		price_low_bitgrail =  min(int(price[1][0]), int(price[1][3]))
		price_low_mercatox =  min(int(price[0][0]), int(price[0][3]))
		price_low = min(price_low_bitgrail, price_low_mercatox)
		exchange = 0
		if (len(args) > 1):
			if (args[1].lower().startswith('bitgrail')):
				price_low = price_low_bitgrail
				exchange = 1
			elif (args[1].lower().startswith('mercatox')):
				price_low = price_low_mercatox
				exchange = 2
		if (value >= price_low):
			btc_price = ('%.8f' % (float(price_low) / (10 ** 8)))
			message_markdown(bot, chat_id, lang_text('prices_below', lang_id).format('exchanges', btc_price))
		elif ((value > 0) and (value < 4294967295)):
			btc_value = ('%.8f' % (float(value) / (10 ** 8)))
			mysql_set_price_low(user_id, value, exchange)
			message_markdown(bot, chat_id, lang_text('prices_success', lang_id).format(btc_value))
		else:
			lang_keyboard(lang_id, bot, chat_id, lang_text('error', lang_id))
	else:
		lang_keyboard(lang_id, bot, chat_id, lang_text('prices_digits', lang_id))
		sleep(1)
		message_markdown(bot, chat_id, '/{0} 10000\n/{0} 0.001'.format(lang_text('price_below', lang_id).encode("utf8").replace("_", "\_")))

		
@run_async
def price_flush(bot, update):
	info_log(update)
	ddos_protection(bot, update, price_flush_callback)

@run_async
def price_flush_callback(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	mysql_delete_price_high(user_id)
	mysql_delete_price_low(user_id)
	message_markdown(bot, chat_id, lang_text('prices_flushed', lang_id))


@run_async
def version(bot, update):
	info_log(update)
	ddos_protection(bot, update, version_text)

@run_async
def version_text(bot, update):
	user_id = update.message.from_user.id
	version = rpc({"action": "version"}, 'node_vendor')
	text_reply(update, version)


@run_async
def text_result(text, bot, update):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	# Check user existance in database
	exist = mysql_user_existance(user_id)
	# Check if ready to pay
	if (exist is not False):
		# Check password protection
		check = mysql_check_password(user_id)
		if (check is not False):
			#print(text)
			password = text
			try:
				dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
				hex = binascii.hexlify(dk)
			except UnicodeEncodeError:
				hex = False
		else:
			hex = False
		# Check password protection
		m = mysql_select_user(user_id)
		if ((m[5] is not None) and (m[6] != 0) and (check == hex) and (check is not False)):
			send_finish(bot, update)
			#print(check)
			#print(hex)
		elif ((m[5] is not None) and (m[6] != 0) and (not (check == hex)) and (check is not False)):
			text_reply(update, lang_text('send_password', lang_id))
			#print(check)
			#print(hex)
			logging.info('Send failure for user {0}. Reason: Wrong password'.format(user_id))
		elif ((m[5] is not None) and (m[6] != 0) and (check is False) and (text.lower() in language['commands']['yes'])):
			send_finish(bot, update)
		elif ((m[5] is not None) and (m[6] != 0)):
			mysql_update_send_clean(m[2])
			mysql_update_send_clean_extra_user(user_id)
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_cancelled', lang_id))
	# Get the text the user sent
	text = text.lower()
	if (text in language['commands']['help']):
		help_text(bot, update)
	elif (text in language['commands']['account']):
		account_text(bot, update)
	elif (text in language['commands']['send']):
		send_text(bot, update)
	elif ('default' in text):
		send_text(bot, update, True)
	elif (text.replace(',', '').replace('.', '').replace(' ', '').replace('mrai', '').replace('xrb', '').replace('()', '').isdigit()):
		# check if digit is correct
		digit_split = text.replace(' ', '').replace('mrai', '').replace('xrb', '').replace('()', '').split(',')
		if (text.startswith('0,') or (any(len(d) > 3 for d in digit_split) and (len(digit_split) > 1)) or any(d is None for d in digit_split) or ((len(digit_split[-1]) < 3) and (len(digit_split) > 1))):
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_digits', lang_id))
		else:
			send_amount(bot, update, text.replace(',', '').replace(' ', '').replace('mrai', '').replace('xrb', '').replace('()', ''))
	elif ('xrb_' in text):
		extra_accounts = mysql_select_user_extra(user_id)
		if ((len(extra_accounts) > 0) and (len(text.split()) > 1)):
			send_extra(bot, update, text)
		else:
			send_destination(bot, update, text)
	elif (text.startswith('@') and (len(text) > 3 )):
		send_destination_username(bot, update, text)
	elif (text in language['commands']['block_count']):
		block_count_callback(bot, update)
	elif (text in language['commands']['start']):
		start_text(bot, update)
	elif (text in language['commands']['price']):
		price_text(bot, update)
	elif ('version' in text):
		version_text(bot, update)
	# back
	elif ('back' in text):
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('ping', lang_id))
	# language selection
	elif (text.split(' ')[0] in language['common']['language_list']):
		language_select_callback(bot, update, text.split(' '))
	# language selection
	elif (text.split(' ')[0] in language['common']['lang']):
		custom_keyboard(bot, update.message.chat_id, lang_text('language_keyboard', 'common'), lang_text('language_selection', 'common'))
	elif ((text not in language['commands']['yes']) and (text not in language['commands']['not'])):
		#default_keyboard(bot, update.message.chat_id, 'Command not found')
		unknown(bot, update)


@run_async
def text_filter(bot, update):
	info_log(update)
	ddos_protection(bot, update, text_filter_callback)

@run_async
def text_filter_callback(bot, update):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	try:
		# Run result function
		text = update.message.text
		text_result(text, bot, update)
	except UnicodeEncodeError:
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('text_decode_error', lang_id))


@run_async
def photo_filter(bot, update):
	info_log(update)
	ddos_protection(bot, update, photo_filter_callback)

@run_async
def photo_filter_callback(bot, update):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	try:
		image = update.message.photo[-1]
		path = '{1}download/{0}.jpg'.format(image.file_id, qr_folder_path)
		#print(image)
		newFile = bot.getFile(image.file_id)
		newFile.download(path)
		qr = account_by_qr(path)
		account = qr[0]
		print(account)
		if ('xrb_' in account):
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('qr_send', lang_id).format(account))
			sleep(1)
			if (len(qr) > 1):
				send_destination(bot, update, account, True)
				print(qr[1])
				send_amount(bot, update, qr[1])
			else:
				send_destination(bot, update, account)
		elif (('NULL' in account) or (account is None) or (account is False)):
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('qr_recognize_error', lang_id))
		else:
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('qr_account_error', lang_id))
		#print(account)
		logging.info('QR by file: {0}'.format(account))
	except UnicodeEncodeError:
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('text_decode_error', lang_id))


@run_async
def password(bot, update, args):
	ddos_protection_args(bot, update, args, password_callback)

@run_async
def password_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	if (len(args) > 0):
		check = mysql_check_password(user_id)
		if (check is False):
			if (len(args[0]) >= 8):
				password = args[0]
				if ((len(set(string.digits).intersection(password)) > 0) and (len(set(string.ascii_uppercase).intersection(password))> 0) and (len(set(string.ascii_lowercase).intersection(password)) > 0)):
					dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
					hex = binascii.hexlify(dk)
					print(hex)
					mysql_set_password(user_id, hex)
					message_markdown(bot, chat_id, lang(user_id, 'password_success'))
					logging.info('Password added for user {0}'.format(user_id))
				else:
					text_reply(update, lang(user_id, 'password_uppercase'))
					logging.info('Password set failed for user {0}. Reason: uppercase-lowercase-digits'.format(user_id))
			else:
				text_reply(update, lang(user_id, 'password_short'))
				logging.info('Password set failed for user {0}. Reason: Too short'.format(user_id))
		else:
			text_reply(update, lang(user_id, 'password_not_empty'))
			logging.info('Password set failed for user {0}. Reason: Already protected'.format(user_id))
	else:
		text_reply(update, lang(user_id, 'password_command'))

@run_async
def password_delete(bot, update, args):
	ddos_protection_args(bot, update, args, password_delete_callback)

@run_async
def password_delete_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	if (len(args) > 0):
		check = mysql_check_password(user_id)
		password = args[0]
		dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
		hex = binascii.hexlify(dk)
		#print(hex)
		#print(check)
		if (check == hex):
			mysql_delete_password(user_id)
			text_reply(update, lang(user_id, 'password_delete_success'))
			logging.info('Password deletion for user {0}'.format(user_id))
		else:
			text_reply(update, lang(user_id, 'password_error'))
			logging.info('Password deletion failed for user {0}. Reason: Wrong password'.format(user_id))
	else:
		text_reply(update, lang(user_id, 'password_delete_command'))


@run_async
def seed(bot, update, args):
	ddos_protection_args(bot, update, args, seed_callback)

@run_async
def seed_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	seed = mysql_select_seed(user_id)
	if (seed is False):
		seed = binascii.b2a_hex(os.urandom(8)).upper()
		mysql_set_seed(user_id, seed)
	seed_split = [seed[i:i+4] for i in range(0, len(seed), 4)]
	seed_text = seed_split[0] + '-' + seed_split[1] + '-' + seed_split[2] + '-' + seed_split[3]
	check = mysql_check_password(user_id)
	if ((len(args) > 0) and (check is not False)):
		password = args[0]
		dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
		hex = binascii.hexlify(dk)
		if (check == hex):
			message_markdown(bot, chat_id, lang_text('seed_creation', lang_id).format(seed_text))
		else:
			text_reply(update, lang_text('password_error', lang_id))
	elif (check is not False):
		text_reply(update, lang_text('password_error', lang_id))
	else:
		message_markdown(bot, chat_id, lang_text('seed_creation', lang_id).format(seed_text))


@run_async
def echo(bot, update):
	info_log(update)
	text_reply(update, update.message.text)


@run_async
def ping(bot, update):
	info_log(update)
	typing_illusion(bot, update.message.chat_id) # typing illusion
	sleep(2)
	default_keyboard(bot, update.message.chat_id, lang(update.message.from_user.id, 'ping'))

@restricted
def stats(bot, update):
	info_log(update)
	typing_illusion(bot, update.message.chat_id) # typing illusion
	fee_balance = account_balance(fee_account) / (10 ** 6)
	stats = '{0}\nFees balance: {1} Mrai (XRB)'.format(mysql_stats(), "{:,}".format(fee_balance))
	fee_pending = account_pending(fee_account) / (10 ** 6)
	if (fee_pending > 0):
		stats = '{0}\nPending fees: {1} Mrai (XRB)'.format(stats, "{:,}".format(fee_pending))
	welcome_balance = account_balance(welcome_account) / (10 ** 6)
	stats = '{0}\nWelcome balance: {1} Mrai (XRB)'.format(stats, "{:,}".format(welcome_balance))
	default_keyboard(bot, update.message.chat_id, stats)

@restricted
def unlock_command(bot, update):
	info_log(update)
	unlock(wallet, wallet_password)
	default_keyboard(bot, update.message.chat_id, 'Wallet unlocked')


@run_async
def unknown(bot, update):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('command_not_found', lang_id))

@run_async
def unknown_ddos(bot, update):
	info_log(update)
	user_id = update.message.from_user.id
	message_id = int(update.message.message_id)
	ddos = mysql_ddos_protector(user_id, message_id)
	if (ddos == True):
		logging.warn('DDoS or double message by user {0} message {1}'.format(user_id, message_id))
	elif (ddos == False):
		logging.warn('Too fast request by user {0}'.format(user_id))
	lang_id = mysql_select_language(user_id)
	lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('command_not_found', lang_id))

def error(bot, update, error):
	logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
	# Create the EventHandler and pass it your bot's token.
	updater = Updater(api_key, workers=64)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	for command in language['commands']['start']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), start))
	for command in language['commands']['help']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), help))
	dp.add_handler(CommandHandler("info", start))

	# my custom commands
	dp.add_handler(CommandHandler("user_id", user_id))
	for command in language['commands']['block_count']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), block_count))
	dp.add_handler(CommandHandler("ping", ping))
	for command in language['commands']['account']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), account))
	for command in language['commands']['account_add']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), account_add))
	for command in language['commands']['account_list']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), account_list))
	for command in (language['commands']['accounts_hide'] + language['commands']['accounts_expand']):
		dp.add_handler(CommandHandler(command.replace(" ", "_"), accounts_hide))
	for command in language['commands']['send']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), send, pass_args=True))
	for command in language['commands']['send_from']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), send_from, pass_args=True))
	for command in language['commands']['send_all']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), send_all))
	dp.add_handler(CommandHandler("password", password, pass_args=True))
	dp.add_handler(CommandHandler("Password", password, pass_args=True)) # symlink
	dp.add_handler(CommandHandler("secret", password, pass_args=True)) # symlink
	dp.add_handler(CommandHandler("password_delete", password_delete, pass_args=True))
	dp.add_handler(CommandHandler("secret_delete", password_delete, pass_args=True)) # symlink
	for command in language['commands']['price']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), price))
	for command in language['commands']['price_above']:
		dp.add_handler(CommandHandler(command, price_above, pass_args=True))
	for command in language['commands']['price_below']:
		dp.add_handler(CommandHandler(command, price_below, pass_args=True))
	for command in language['commands']['price_flush']:
		dp.add_handler(CommandHandler(command, price_flush))
	dp.add_handler(CommandHandler("version", version))
	for command in language['common']['lang']:
		dp.add_handler(CommandHandler(command.replace(" ", "_"), language_select, pass_args=True))
	dp.add_handler(CommandHandler("seed", seed, pass_args=True))

	
	# admin commands
	dp.add_handler(CommandHandler("broadcast", broadcast))
	dp.add_handler(CommandHandler("bootstrap", bootstrap))
	dp.add_handler(CommandHandler("restart", restart))
	dp.add_handler(CommandHandler("stats", stats))
	dp.add_handler(CommandHandler("unlock", unlock_command))

	# on noncommand i.e message - return not found
	dp.add_handler(MessageHandler(Filters.text, text_filter))
	dp.add_handler(MessageHandler(Filters.photo, photo_filter))
	dp.add_handler(MessageHandler(Filters.command, unknown_ddos))

	# log all errors
	dp.add_error_handler(error)

	# Start the Bot
	#updater.start_polling()
	updater.start_webhook(listen='127.0.0.1', port=int(listen_port), url_path=api_key)
	updater.bot.setWebhook('https://{0}/{1}'.format(domain, api_key))
	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
	try:
		print('Starting bot server')
		main()
	except(urllib3.exceptions.ReadTimeoutError):
		logging.info('urllib3.exceptions.ReadTimeoutError')
		print('urllib3.exceptions.ReadTimeoutError')
	except(urllib3.exceptions.HTTPError):
		logging.info('urllib3.exceptions.HTTPError')
		print('urllib3.exceptions.HTTPError')
	except(socket.timeout):
		logging.info('socket.timeout')
		print('socket.timeout')
