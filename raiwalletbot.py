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
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram import Bot, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from telegram.error import BadRequest, RetryAfter
import logging
import urllib3, certifi, socket, json
import hashlib, binascii, string, math
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
password = config.get('main', 'password')
fee_account = config.get('main', 'fee_account')
fee_amount = int(config.get('main', 'fee_amount'))
raw_fee_amount = fee_amount * (10 ** 24)
incoming_fee = int(config.get('main', 'incoming_fee'))
raw_incoming_fee = incoming_fee * (10 ** 24)
incoming_fee_text = '\n'
if (incoming_fee >= 1):
	incoming_fee_text = '\nCurrent fee for INCOMING transaction (DDoS protection): *{0} Mrai (XRB)*\n'.format(incoming_fee)
min_send = int(config.get('main', 'min_send'))
ddos_protect_seconds = config.get('main', 'ddos_protect_seconds')
admin_list = json.loads(config.get('main', 'admin_list'))
LIST_OF_FEELESS = json.loads(config.get('main', 'feeless_list'))
salt = config.get('password', 'salt')
block_count_difference_threshold = int(config.get('monitoring', 'block_count_difference_threshold'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename=log_file)

logger = logging.getLogger(__name__)

account_url = 'https://raiblockscommunity.net/account/index.php?acc='
hash_url = 'https://raiblockscommunity.net/block/index.php?h='
faucet_url = 'https://faucet.raiblockscommunity.net/form.php?a='
summary_url = 'https://raiblockscommunity.net/page/summary.php?json=1'

# MySQL requests
from common_mysql import *

# QR code handler
from common_qr import *

# Request to node
from common_rpc import *

# Common functions
from common import *


unlock(wallet, password)

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
	lang_id = mysql_select_language(user_id)
#	hide_keyboard(bot, update.message.chat_id, text)
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
			mysql_delete_blacklist(account[0]) # if someone deleted chat, broadcast will fail and he wilk remain be blacklisted


# bootstrap
@restricted
def bootstrap(bot, update):
	info_log(update)
	rpc({"action": "bootstrap", "address": "::ffff:138.201.94.249", "port": "7075"}, 'success')
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
def account_text(bot, update):
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
		max_send = balance - fee_amount
		if (balance == 0):
			text = lang_text('account_balance_zero', lang_id).format(faucet_url, r)
		elif (max_send < min_send):
			text = lang_text('account_balance_low', lang_id).format(faucet_url, r, mrai_text(balance), mrai_text(fee_amount), mrai_text(min_send))
		else:
			price = mysql_select_price()
			if (int(price[0][0]) > 0):
				last_price = ((float(price[0][0]) * float(price[0][6])) + (float(price[1][0]) * float(price[1][6]))) / (float(price[0][6]) + float(price[1][6]))
			else:
				last_price = int(price[1][0])
			btc_price = last_price / (10 ** 14)
			btc_balance = ('%.8f' % (btc_price * balance))
			text = lang_text('account_balance', lang_id).format(mrai_text(balance), btc_balance, mrai_text(max_send))
		text = '{0}\n\n{1}'.format(text.encode("utf8"), lang_text('account_your', lang_id).encode("utf8"))
		message_markdown(bot, chat_id, text)
		sleep(1)
		message_markdown(bot, chat_id, '*{0}*'.format(r))
		sleep(1)
		message_markdown(bot, chat_id, lang_text('account_history', lang_id).format(r, account_url, faucet_url))
		sleep(1)
		#bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'), caption=r)
		bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'))
		
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
		else:
			text_reply(update, lang_text('account_error', lang_id))



@run_async
def send(bot, update, args):
	info_log(update)
	ddos_protection_args(bot, update, args, send_callback)

@run_async
def send_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	
	# Check user existance in database
	m = mysql_select_user(user_id)
	
	try:
		account = m[2]
		#print(account)
		# Check balance to send
		try:
			balance = account_balance(account)
			# FEELESS
			if (user_id in LIST_OF_FEELESS):
				final_fee_amount = 0
			else:
				final_fee_amount = fee_amount
			# FEELESS
			max_send = balance - final_fee_amount
			#if ((args[0] == 'all') or (args[0] == 'everything')):
			#	send_amount = int(balance - fee_amount)
			#else:
			send_amount = int(float(args[0]) * (10 ** 6))
			raw_send_amount = send_amount * (10 ** 24)
			#print(send_amount)
			#print(balance)
			if (max_send < min_send):
				text_reply(update, lang_text('send_low_balance', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
			elif (send_amount > max_send):
				text_reply(update, lang_text('send_limit_max', lang_id).format(mrai_text(final_fee_amount), mrai_text(max_send)))
			elif (send_amount < min_send):
				text_reply(update, lang_text('send_limit_min', lang_id).format(mrai_text(min_send)))
				
			else:
				# Check destination address
				destination = args[1]
				if ((len(args) > 2) and (args[1].lower() == 'mrai')):
					destination = args[2]
				# if destination is username
				if (destination.startswith('@') and (len(destination) > 3 )):
					username = destination.replace('@', '')
					dest_account = mysql_account_by_username(username)
					if (dest_account is not False):
						#text_reply(update, 'User {0} found. His account: {1}'.format(text, account))
						#send_destination(bot, update, account)
						destination = dest_account
					else:
						text_reply(update, lang_text('send_user_not_found', lang_id).format(destination))
				destination_check = rpc({"action": "validate_account_number", "account": destination}, 'valid')
				#print(destination)
				# Check password protection
				check = mysql_check_password(user_id)
				if ((len(args) > 3) and (args[1].lower() == 'mrai')):
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
				frontier = m[3]
				check_frontier = check_block(frontier)
				if ((destination_check == '1') and (check == hex) and (check_frontier)):
					# Sending
					try:
						send_hash = rpc({"action": "send", "wallet": wallet, "source": account, "destination": destination, "amount": raw_send_amount}, 'block')
						if ('000000000000000000000000000000000000000000000000000000000000000' not in send_hash):
							# FEELESS
							if (final_fee_amount > 0):
								fee = rpc({"action": "send", "wallet": wallet, "source": account, "destination": fee_account, "amount": raw_fee_amount}, 'block')
							else:
								fee = send_hash
							# FEELESS
							new_balance = account_balance(account)
							mysql_update_balance(account, new_balance)
							mysql_update_frontier(account, fee)
							lang_keyboard(lang_id, bot, chat_id, lang_text('send_completed', lang_id).format(mrai_text(final_fee_amount), mrai_text(new_balance)))
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
							logging.info('Transaction FAILURE! Account {0}'.format(account))
							new_balance = account_balance(account)
							lang_keyboard(lang_id, bot, chat_id, lang_text('send_tx_error', lang_id).format(mrai_text(new_balance)))
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
def send_text(bot, update):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	# FEELESS
	if (user_id in LIST_OF_FEELESS):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	m = mysql_select_user(user_id)
	try:
		account = m[2]
		balance = account_balance(account)
		if (balance >= (final_fee_amount + min_send)):
			text_reply(update, lang_text('send_amount', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
		else:
			text_reply(update, lang_text('send_low_balance', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
	except (TypeError):
		lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_no_account_text', lang_id))


@run_async
def send_destination(bot, update, text):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	lang_id = mysql_select_language(user_id)
	# FEELESS
	if (user_id in LIST_OF_FEELESS):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	# Check user existance in database
	m = mysql_select_user(user_id)
	try:
		account = m[2]
		destination = text
		destination_check = rpc({"action": "validate_account_number", "account": destination}, 'valid')
		if (destination_check == '1'):
			mysql_update_send_destination(account, destination)
			if (m[6] != 0):
				custom_keyboard(bot, chat_id, lang_text('yes_no', lang_id), lang_text('send_confirm', lang_id).format(mrai_text(m[6]), mrai_text(m[6]+final_fee_amount), destination))
			else:
				text_reply(update, lang_text('send_amount', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
		else:
			message_markdown(bot, chat_id, lang_text('send_invalid', lang_id))
	except (TypeError):
		lang_keyboard(lang_id, bot, chat_id, lang_text('send_no_account_text', lang_id))


@run_async
def send_destination_username(bot, update, text):
	user_id = update.message.from_user.id
	username = text.replace('@', '')
	#print(username)
	account = mysql_account_by_username(username)
	#print(account)
	if (account is not False):
		text_reply(update, lang(user_id, 'send_user').format(text, account))
		send_destination(bot, update, account)
	else:
		text_reply(update, lang(user_id, 'send_user_not_found').format(text))


@run_async
def send_amount(bot, update, text):
	user_id = update.message.from_user.id
	lang_id = mysql_select_language(user_id)
	# FEELESS
	if (user_id in LIST_OF_FEELESS):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	# Check user existance in database
	m = mysql_select_user(user_id)
	try:
		account = m[2]
		try:
			balance = account_balance(account)
			max_send = balance - final_fee_amount
			send_amount = int(float(text) * (10 ** 6))
			# if less, set 0
			if (max_send < min_send):
				text_reply(update, lang_text('send_low_balance', lang_id).format(mrai_text(final_fee_amount), mrai_text(min_send)))
			elif (send_amount > max_send):
				text_reply(update, lang_text('send_limit_max', lang_id).format(mrai_text(final_fee_amount), mrai_text(max_send)))
			elif (send_amount < min_send):
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
	# FEELESS
	if (user_id in LIST_OF_FEELESS):
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
			send_hash = rpc({"action": "send", "wallet": wallet, "source": account, "destination": destination, "amount": raw_send_amount}, 'block')
			if ('00000000000000000000000000000000000000000000000000000000000000' not in send_hash):
				# FEELESS
				if (final_fee_amount > 0):
					fee = rpc({"action": "send", "wallet": wallet, "source": account, "destination": fee_account, "amount": raw_fee_amount}, 'block')
				else:
					fee = send_hash
				# FEELESS
				new_balance = account_balance(account)
				mysql_update_balance(account, new_balance)
				mysql_update_frontier(account, fee)
				sleep(1)
				lang_keyboard(lang_id, bot, chat_id, lang_text('send_completed', lang_id).format(mrai_text(final_fee_amount), mrai_text(new_balance)))
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
				logging.info('Transaction FAILURE! Account {0}'.format(account))
				new_balance = account_balance(account)
				lang_keyboard(lang_id, bot, chat_id, lang_text('send_tx_error', lang_id).format(mrai_text(new_balance)))
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
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_cancelled', lang_id))
	# Get the text the user sent
	text = text.lower()
	if (text in language['commands']['help']):
		help_text(bot, update)
	elif (text in language['commands']['account']):
		account_text(bot, update)
	elif (text in language['commands']['send']):
		send_text(bot, update)
	elif (text.replace(',', '').replace('.', '').replace(' ', '').replace('mrai', '').isdigit()):
		# check if digit is correct
		digit_split = text.replace(' ', '').replace('mrai', '').split(',')
		if (text.startswith('0,') or (any(len(d) > 3 for d in digit_split) and (len(digit_split) > 1)) or any(d is None for d in digit_split) or ((len(digit_split[-1]) < 3) and (len(digit_split) > 1))):
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('send_digits', lang_id))
		else:
			send_amount(bot, update, text.replace(',', '').replace(' ', '').replace('mrai', ''))
	elif ('xrb_' in text):
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
		account = account_by_qr(path)
		print(account)
		if ('xrb_' in account):
			lang_keyboard(lang_id, bot, update.message.chat_id, lang_text('qr_send', lang_id).format(account))
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
		text_reply(update, 'Use command\n/password HereYourPass')

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
	default_keyboard(bot, update.message.chat_id, stats)


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
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("Start", start)) # symlink
	dp.add_handler(CommandHandler("help", help))
	dp.add_handler(CommandHandler("Help", help)) # symlink
	dp.add_handler(CommandHandler("support", help)) # symlink
	dp.add_handler(CommandHandler("info", start))

	# my custom commands
	dp.add_handler(CommandHandler("user_id", user_id))
	dp.add_handler(CommandHandler("block_count", block_count))
	dp.add_handler(CommandHandler("ping", ping))
	dp.add_handler(CommandHandler("account", account))
	dp.add_handler(CommandHandler("Account", account)) # symlink
	dp.add_handler(CommandHandler("balance", account)) # symlink
	dp.add_handler(CommandHandler("register", account)) # symlink
	dp.add_handler(CommandHandler("send", send, pass_args=True))
	dp.add_handler(CommandHandler("password", password, pass_args=True))
	dp.add_handler(CommandHandler("Password", password, pass_args=True)) # symlink
	dp.add_handler(CommandHandler("secret", password, pass_args=True)) # symlink
	dp.add_handler(CommandHandler("password_delete", password_delete, pass_args=True))
	dp.add_handler(CommandHandler("secret_delete", password_delete, pass_args=True)) # symlink
	dp.add_handler(CommandHandler("price", price))
	dp.add_handler(CommandHandler("market", price)) # symlink
	dp.add_handler(CommandHandler("version", version))
	dp.add_handler(CommandHandler("language", language_select, pass_args=True))

	
	# admin commands
	dp.add_handler(CommandHandler("broadcast", broadcast))
	dp.add_handler(CommandHandler("bootstrap", bootstrap))
	dp.add_handler(CommandHandler("restart", restart))
	dp.add_handler(CommandHandler("stats", stats))

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
