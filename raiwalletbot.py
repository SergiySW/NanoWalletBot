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
import logging
import urllib3, socket, json
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
raw_fee_amount = fee_amount * (10 ** 30)
incoming_fee = int(config.get('main', 'incoming_fee'))
raw_incoming_fee = incoming_fee * (10 ** 30)
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
faucet_url = 'https://raiblockscommunity.net/faucet/form.php?a='
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
			print("Unauthorized access denied for {}.".format(chat_id))
			return
		return func(bot, update, *args, **kwargs)
	return wrapped


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.

@run_async
def custom_keyboard(bot, chat_id, buttons, text):
	try:
		reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard = True)
		bot.sendMessage(chat_id=chat_id, 
					 text=text, 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True,
					 reply_markup=reply_markup)
	except ProtocolError:
		sleep(0.3)
		bot.sendMessage(chat_id=chat_id, 
					 text=text, 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True,
					 reply_markup=reply_markup)

@run_async
def default_keyboard(bot, chat_id, text):
	custom_keyboard(bot, chat_id, [['Account', 'Send'], ['Help']], text)

@run_async
def hide_keyboard(bot, chat_id, text):
	reply_markup = ReplyKeyboardRemove()
	try:
		bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)
	except ProtocolError:
		sleep(0.3)
		bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)

@run_async
def typing_illusion(bot, chat_id):
	try:
		bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING) # typing illusion
	except ProtocolError:
		sleep(0.3)
		bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING) # typing illusion


@run_async
def ddos_protection(bot, update, callback):
	user_id = update.message.from_user.id
	message_id = int(update.message.message_id)
	ddos = mysql_ddos_protector(user_id, message_id)
	if (ddos == True):
		logging.warn('DDoS or double message by user {0} message {1}'.format(user_id, message_id))
	elif (ddos == False):
		update.message.reply_text('You cannot send commands faster than once in {0} seconds'.format(ddos_protect_seconds))
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
		update.message.reply_text('You cannot send commands faster than once in {0} seconds'.format(ddos_protect_seconds))
		logging.warn('Too fast request by user {0}'.format(user_id))
	else:
		callback(bot, update, args)


@run_async
def start(bot, update):
	logging.info(update.message)
	ddos_protection(bot, update, start_text)


@run_async
def start_text(bot, update):
	user_id = update.message.from_user.id
#	hide_keyboard(bot, update.message.chat_id, text)
	update.message.reply_text('Hello!'
		'\nI am @RaiWalletBot – your Telegram bot to manage RaiBlocks cryptocurrency')
	sleep(0.1)
	text = ('Here are some basic commands to control your wallet '
		'\nPress "Account" to show account & check balance'
		'\nPress "Send" to start sending'
		'\n\nCurrent fee for outcoming transaction: *{0} Mrai (XRB)*'
		'{2}Current minimum to receive: *1 Mrai (XRB)*'
		'\nCurrent minimum to send: *{1} Mrai (XRB) + fee*'
		'\n\nfor advanced commands type /help'.format(fee_amount, min_send, incoming_fee_text))
	default_keyboard(bot, update.message.chat_id, text)
	sleep(0.1)
	bot.sendMessage(chat_id=update.message.chat_id, 
				text='Learn more about RaiBlocks cryptocurrency & earn some free Mrai (XRB) at [raiblockscommunity.net](https://raiblockscommunity.net)!'
				'\nTrading: [Mercatox](https://mercatox.com/exchange), @RaiBlocksTradeBot, @RaiBlocksTrade, more options coming soon!..'
				'\n\n1 user = 1 xrb\_account'
				'\nTHE BOT IS PROVIDED \"AS IS\" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS BOT. YOU ASSUME THE RESPONSIBILITY FOR YOUR ACTIONS, AND NO REFUNDS WILL BE ISSUED', 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)


@run_async
def help(bot, update):
	logging.info(update.message)
	ddos_protection(bot, update, help_callback)

@run_async
def help_callback(bot, update):
	user_id = update.message.from_user.id
	text = ('For basic commands press \"Help\" button'
		'\nHere are some advanced commands to control your wallet '
		'\n /help — receive list of available commands'
		'\n /account — create account, show account & check balance'
		'\n /block\_count — check our wallet is up-to-date!'
		'\n /send amount xrb\_account optional\_pass — send Mrai (XRB) to other xrb\_account'
		'\n /password HereYourPass  — protect account with password'
		'\n /password\_delete HereYourPass — delete existing password'
		'\n /price — show Mrai (XRB) market price'
		'\n\nCurrent fee for outcoming transaction: *{0} Mrai (XRB)*'
		'{2}Current minimum to receive: *1 Mrai (XRB)*'
		'\nCurrent minimum to send: *{1} Mrai (XRB) + fee*'.format(fee_amount, min_send, incoming_fee_text))
	default_keyboard(bot, update.message.chat_id, text)
	sleep(0.1)
	bot.sendMessage(chat_id=update.message.chat_id, 
				text='Learn more about RaiBlocks cryptocurrency & earn some free Mrai (XRB) at [raiblockscommunity.net](https://raiblockscommunity.net)!'
				'\nTrading: [Mercatox](https://mercatox.com/exchange), @RaiBlocksTradeBot, @RaiBlocksTrade, more options coming soon!..'
				'\n\nAny suggestions or bugs? Contact me @SergSW'
				'\nTHE BOT IS PROVIDED \"AS IS\". 1 user = 1 xrb\_account', 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)


@run_async
def help_text(bot, update):
	user_id = update.message.from_user.id
	text = ('Press \"Account\" to show account & check balance'
		'\nPress \"Send\" to start sending'
		'\n\nCurrent fee for outcoming transaction: *{0} Mrai (XRB)*'
		'{2}Current minimum to receive: *1 Mrai (XRB)*'
		'\nCurrent minimum to send: *{1} Mrai (XRB) + fee*'
		'\n\nfor advanced commands type /help'.format(fee_amount, min_send, incoming_fee_text))
	default_keyboard(bot, update.message.chat_id, text)
	sleep(0.1)
	bot.sendMessage(chat_id=update.message.chat_id, 
				text='Learn more about RaiBlocks cryptocurrency & earn some free Mrai (XRB) at [raiblockscommunity.net](https://raiblockscommunity.net)!'
				'\nTrading: [Mercatox](https://mercatox.com/exchange), @RaiBlocksTradeBot, @RaiBlocksTrade, more options coming soon!..'
				'\n\nAny suggestions or bugs? Contact me @SergSW'
				'\nTHE BOT IS PROVIDED \"AS IS\". 1 user = 1 xrb\_account', 
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True)



def user_id(bot, update):
	user_id = update.message.from_user.id
	update.message.reply_text(user_id)


@run_async
def block_count(bot, update):
	logging.info(update.message)
	ddos_protection(bot, update, block_count_callback)

@run_async
def block_count_callback(bot, update):
	user_id = update.message.from_user.id
	count = rpc({"action": "block_count"}, 'count')
	update.message.reply_text("{:,}".format(int(count)))
#	default_keyboard(bot, update.message.chat_id, r)
	# Admin block count check from raiblockscommunity.net
	if (user_id in admin_list):
		http = urllib3.PoolManager()
		response = http.request('GET', summary_url)
		json_data = json.loads(response.data)
		community_count = json_data['blocks']
		if (math.fabs(int(community_count) - int(count)) > block_count_difference_threshold):
			update.message.reply_text('Community: {0}'.format("{:,}".format(int(community_count))))



# broadcast
@restricted
def broadcast(bot, update):
	logging.info(update.message)
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
	logging.info(update.message)
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
	logging.info(update.message)
	ddos_protection(bot, update, account_text)


@run_async
def account_text(bot, update):
	user_id = update.message.from_user.id
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
			bot.sendMessage(chat_id=update.message.chat_id, 
					 text='Your balance is *0 Mrai (XRB)*. Send some Mrai (XRB) to your account or claim with hourly [RaiBlocks faucet]({0}{1})'.format(faucet_url, r), 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True)
		elif (max_send < min_send):
			bot.sendMessage(chat_id=update.message.chat_id, 
					 text='Your balance: *{2} Mrai (XRB)*. It is less than current fee {3} Mrai (XRB) + minimal send {4} Mrai (XRB). Send some Mrai (XRB) to your account or claim with hourly [RaiBlocks faucet]({0}{1})'.format(faucet_url, r, "{:,}".format(balance), fee_amount, min_send), 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True)
		else:
			#update.message.reply_text('Your balance: {0} Mrai (XRB). Send limit (Mrai):'.format("{:,}".format(balance)))
			#update.message.reply_text("{:,}".format(max_send))
			last_price = float(mysql_select_price()[0])
			btc_price = last_price / (10 ** 8)
			btc_balance = ('%.8f' % (btc_price * balance))
			bot.sendMessage(chat_id=update.message.chat_id, 
					 text=('Your balance: *{0} Mrai (XRB)*'
							'\n~ {1} BTC'
							'\nSend limit: {2} Mrai (XRB)'.format("{:,}".format(balance), btc_balance, "{:,}".format(max_send))), 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True)
		sleep(0.1)
		update.message.reply_text('Your RaiBlocks account')
		sleep(0.1)
		bot.sendMessage(chat_id=update.message.chat_id, 
					 text='*{0}*'.format(r), 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True)
		sleep(0.1)
		bot.sendMessage(chat_id=update.message.chat_id, 
					 text=('[account in explorer — history]({1}{0})'
							'\n[distribution — earn with hourly faucet]({2}{0})'.format(r, account_url, faucet_url)), 
					 parse_mode=ParseMode.MARKDOWN,
					 disable_web_page_preview=True)
		#bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'), caption=r)
		bot.sendPhoto(chat_id=update.message.chat_id, photo=open('{1}{0}.png'.format(r, qr_folder_path), 'rb'))
		
	except (TypeError):
		r = rpc({"action": "account_create", "wallet": wallet}, 'account')
		qr_by_account(r)
		chat_id=update.message.chat_id
		if ('xrb_' in r): # check for errors
			insert_data = {
			  'user_id': user_id,
			  'account': r,
			  'chat_id': chat_id,
			  'username': username,
			}
			mysql_insert(insert_data)
			update.message.reply_text('We create new RaiBlocks account for you! Your account')
			sleep(0.1)
			bot.sendMessage(chat_id=update.message.chat_id, 
						 text='*{0}*'.format(r), 
						 parse_mode=ParseMode.MARKDOWN,
						 disable_web_page_preview=True)
			sleep(0.1)
			bot.sendMessage(chat_id=chat_id, 
						 text='[account in explorer]({1}{0})'.format(r, account_url), 
						 parse_mode=ParseMode.MARKDOWN,
						 disable_web_page_preview=True)
			sleep(0.1)
			bot.sendMessage(chat_id=chat_id, 
						 text='Your start balance is 0 Mrai (XRB). "This account doesn\'t exist on the blockchain yet" means that you didn\'t receive any Mrai (XRB) yet.\nSend some Mrai (XRB) to your account or claim with hourly [RaiBlocks faucet]({0}{1})'.format(faucet_url, r), 
						 parse_mode=ParseMode.MARKDOWN,
						 disable_web_page_preview=True)
		else:
			update.message.reply_text('Error creating account. Try again later')



@run_async
def send(bot, update, args):
	logging.info(update.message)
	ddos_protection_args(bot, update, args, send_callback)

@run_async
def send_callback(bot, update, args):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id

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
			send_amount = int(args[0])
			raw_send_amount = send_amount * (10 ** 30)
			#print(send_amount)
			#print(balance)
			if (max_send < min_send):
				update.message.reply_text('Your balance is too small to send. Current fee: {0} Mrai (XRB). Minimal send: {1} Mrai (XRB)'.format(final_fee_amount, min_send))
			elif (send_amount > max_send):
				update.message.reply_text('You cannot send more than your balance – {0} Mrai (XRB) fee. Your current limit: {1} Mrai (XRB)'.format(final_fee_amount, "{:,}".format(max_send)))
			elif (send_amount < min_send):
				update.message.reply_text('You cannot send less than minimum {0} Mrai (XRB)'.format(min_send))
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
						#update.message.reply_text('User {0} found. His account: {1}'.format(text, account))
						#send_destination(bot, update, account)
						destination = dest_account
					else:
						update.message.reply_text('User {0} not found. Perhaps he doesn\'t have account in @RaiWalletBot. Invite him!'.format(destination))
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
				typing_illusion(bot, update.message.chat_id) # typing illusion
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
							#update.message.reply_text('Transaction completed. Fee: {0} Mrai (XRB). Your current balance: {1} Mrai (XRB). Transaction hash'.format(final_fee_amount, "{:,}".format(new_balance)))
							default_keyboard(bot, chat_id, 'Transaction completed. Fee: {0} Mrai (XRB). Your current balance: *{1} Mrai (XRB)*. Transaction hash'.format(final_fee_amount, "{:,}".format(new_balance)))
							sleep(0.1)
							update.message.reply_text(send_hash)
							sleep(0.1)
							bot.sendMessage(chat_id=chat_id, 
										 text='[hash in block explorer]({1}{0})'.format(send_hash, hash_url), 
										 parse_mode=ParseMode.MARKDOWN,
										 disable_web_page_preview=True)
							logging.info('Send from {0} to {1}  amount {2}  hash {3}'.format(account, destination, send_amount, send_hash))
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
							default_keyboard(bot, update.message.chat_id, 'Transaction failed. Try again later. Your current balance: *{0} Mrai (XRB)*'.format("{:,}".format(new_balance)))
					except (GeneratorExit):
						update.message.reply_text('Failed to send. Try again later')
					except (ValueError):
						default_keyboard(bot, chat_id, 'Failed to send. Try again later')
				elif (not (check == hex)):
					update.message.reply_text('Password you entered is incorrent. Try again')
					logging.info('Send failure for user {0}. Reason: Wrong password'.format(user_id))
				elif (not (check_frontier)):
					update.message.reply_text('As additional level of protection we check your last transaction hash at raiblockscommunity.net. Your last block wasn\'t found at website yet. Try send later')
					logging.info('Send failure for user {0}. Reason: Frontier not found'.format(user_id))
				else:
					update.message.reply_text('Destination xrb_address in invalid')
		except (ValueError):
			update.message.reply_text('Send amount must contain digits ONLY')
		
	except (TypeError):
		update.message.reply_text('You don\'t have RaiBlocks account yet. Type /account to begin')
	except (IndexError):
		update.message.reply_text('Use command /send [amount] [xrb_account]'
								  '\nExample: /send {0} {1}'
								  '\n\nor simple press "Send" button'.format(min_send, m[2]))


@run_async
def send_text(bot, update):
	user_id = update.message.from_user.id
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
			update.message.reply_text('Please specify amount of Mrai (XRB) you want to send. Current fee: {0} Mrai (XRB). Minimal send: {1} Mrai (XRB)'.format(final_fee_amount, min_send))
		else:
			update.message.reply_text('Your balance is too small to send. Current fee: {0} Mrai (XRB). Minimal send: {1} Mrai (XRB)'.format(final_fee_amount, min_send))
	except (TypeError):
		default_keyboard(bot, update.message.chat_id, 'You don\'t have RaiBlocks account yet. Press Account to begin')


@run_async
def send_destination(bot, update, text):
	user_id = update.message.from_user.id
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
				custom_keyboard(bot, update.message.chat_id, [['Yes', 'No']], 'Confirm you want to send *{0} Mrai (XRB)* to *{2}*\nIt will cost you *{1} Mrai (XRB)* with fees'.format("{:,}".format(m[6]), "{:,}".format(m[6]+final_fee_amount), destination))
			else:
				update.message.reply_text('Please specify amount of Mrai (XRB) you want to send. Current fee: {0} Mrai (XRB). Minimal send: {1} Mrai (XRB)'.format(final_fee_amount, min_send))
		else:
			update.message.reply_text('Destination address in invalid')
	except (TypeError):
		default_keyboard(bot, update.message.chat_id, 'You don\'t have RaiBlocks account yet. Press Account to begin')


@run_async
def send_destination_username(bot, update, text):
	username = text.replace('@', '')
	#print(username)
	account = mysql_account_by_username(username)
	#print(account)
	if (account is not False):
		update.message.reply_text('User {0} found. His account: {1}'.format(text, account))
		send_destination(bot, update, account)
	else:
		update.message.reply_text('User {0} not found. Perhaps he doesn\'t have account in @RaiWalletBot. Invite him!'.format(text))


@run_async
def send_amount(bot, update, text):
	user_id = update.message.from_user.id
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
			send_amount = int(text)
			# if less, set 0
			if (max_send < min_send):
				update.message.reply_text('Your balance is too small to send. Current fee: {0} Mrai (XRB). Minimal send: {1} Mrai (XRB)'.format(final_fee_amount, min_send))
			elif (send_amount > max_send):
				update.message.reply_text('You cannot send more than your balance – {0} Mrai (XRB) fee. Your current limit: {1} Mrai (XRB)'.format(final_fee_amount, "{:,}".format(max_send)))
			elif (send_amount < min_send):
				update.message.reply_text('You cannot send less than minimum {0} Mrai (XRB)'.format(min_send))
			else:
				mysql_update_send_amount(account, send_amount)
				if (m[5] is not None):
					custom_keyboard(bot, update.message.chat_id, [['Yes', 'No']], 'Confirm you want to send *{0} Mrai (XRB)* to *{2}*\nIt will cost you *{1} Mrai (XRB)* with fees'.format("{:,}".format(send_amount), "{:,}".format(send_amount+final_fee_amount), m[5]))
				else:
					update.message.reply_text('Please specify destitation xrb_account or @UserName (starts with @ sign) or upload QR code (clean, best quality image)')
		except (ValueError):
			update.message.reply_text('Send amount must contain Integer ONLY')
	except (TypeError):
		default_keyboard(bot, update.message.chat_id, 'You don\'t have RaiBlocks account yet. Press Account to begin')


@run_async
def send_finish(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	m = mysql_select_user(user_id)
	account = m[2]
	send_amount = int(m[6])
	raw_send_amount = send_amount * (10 ** 30)
	destination = m[5]
	mysql_update_send_clean(account)
	# FEELESS
	if (user_id in LIST_OF_FEELESS):
		final_fee_amount = 0
	else:
		final_fee_amount = fee_amount
	# FEELESS
	try:
		hide_keyboard(bot, chat_id, 'Working on your transaction...')
		typing_illusion(bot, chat_id)  # typing illusion
		# Check frontier existance
		frontier = m[3]
		check_frontier = check_block(frontier)
		if (check_frontier):
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
				sleep(0.4)
				default_keyboard(bot, chat_id, 'Transaction completed. Fee: {0} Mrai (XRB). Your current balance: *{1} Mrai (XRB)*. Transaction hash'.format(final_fee_amount, "{:,}".format(new_balance)))
				sleep(0.2)
				update.message.reply_text(send_hash)
				sleep(0.2)
				bot.sendMessage(chat_id=chat_id, 
						text='[hash in block explorer]({1}{0})'.format(send_hash, hash_url), 
						parse_mode=ParseMode.MARKDOWN,
						disable_web_page_preview=True)
				logging.info('Send from {0} to {1}  amount {2}  hash {3}'.format(account, destination, send_amount, send_hash))
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
				default_keyboard(bot, chat_id, 'Transaction failed. Try again later. Your current balance: *{0} Mrai (XRB)*'.format("{:,}".format(new_balance)))
		else:
			update.message.reply_text('As additional level of protection we check your last transaction hash at raiblockscommunity.net. Your last block wasn\'t found at website yet. Try send later')
			logging.info('Send failure for user {0}. Reason: Frontier not found'.format(user_id))
	except (GeneratorExit):
		default_keyboard(bot, chat_id, 'Failed to send. Try again later')
	except (ValueError):
		default_keyboard(bot, chat_id, 'Failed to send. Try again later')



@run_async
def price(bot, update):
	logging.info(update.message)
	ddos_protection(bot, update, price_text)

@run_async
def price_text(bot, update):
	user_id = update.message.from_user.id
	chat_id = update.message.chat_id
	price = mysql_select_price()
	last_price = ('%.8f' % (float(price[0]) / (10 ** 8)))
	ask_price = ('%.8f' % (float(price[3]) / (10 ** 8)))
	bid_price = ('%.8f' % (float(price[4]) / (10 ** 8)))
	high_price = ('%.8f' % (float(price[1]) / (10 ** 8)))
	low_price = ('%.8f' % (float(price[2]) / (10 ** 8)))
	volume = int(price[5])
	#volume_btc = ('%.8f' % (volume * float(price[0]) / (10 ** 8))).rstrip('0').rstrip('.')
	text = ('Last RaiBlocks (XRB) price: *{0} BTC*'
		'\nAsk price: *{1} BTC*'
		'\nBid price: *{2} BTC*'
		'\n\n24 hours Volume: *{5} Mrai (XRB)*'
		#'\nVolume BTC: *{6}*'
		'\n24 hours High: *{3} BTC*'
		'\n24 hours Low: *{4} BTC*'.format(last_price, ask_price, bid_price, high_price, low_price, "{:,}".format(volume)))
	default_keyboard(bot, update.message.chat_id, text)



@run_async
def text_result(text, bot, update):
	user_id = update.message.from_user.id
	# Check user existance in database
	exist = mysql_user_existance(user_id)
	# Check if ready to pay
	if (exist is not False):
		# Check password protection
		check = mysql_check_password(user_id)
		if (check is not False):
			#print(text)
			password = text
			dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
			hex = binascii.hexlify(dk)
		else:
			hex = False
		# Check password protection
		m = mysql_select_user(user_id)
		if ((m[5] is not None) and (m[6] != 0) and (check == hex) and (check is not False)):
			send_finish(bot, update)
			#print(check)
			#print(hex)
		elif ((m[5] is not None) and (m[6] != 0) and (not (check == hex)) and (check is not False)):
			update.message.reply_text('Password you entered is incorrent. Type your password to confirm transaction')
			#print(check)
			#print(hex)
			logging.info('Send failure for user {0}. Reason: Wrong password'.format(user_id))
		elif ((m[5] is not None) and (m[6] != 0) and (check is False) and (('yes' in text.lower()) or ('confirm' in text.lower()))):
			send_finish(bot, update)
		elif ((m[5] is not None) and (m[6] != 0)):
			mysql_update_send_clean(m[2])
			default_keyboard(bot, update.message.chat_id, 'Payment cancelled')
	# Get the text the user sent
	text = text.lower()
	if (('help' in text) or ('support' in text)):
		help_text(bot, update)
	elif (('account' in text) or ('balance' in text) or ('register' in text)):
		account_text(bot, update)
	elif ('send' in text):
		send_text(bot, update)
	elif (text.replace(',', '').replace('.', '').replace(' ', '').replace('mrai', '').isdigit()):
		# check if digit is correct
		digit_split = text.replace(' ', '').replace('mrai', '').split(',')
		if (text.startswith('0,') or ('.' in text) or (any(len(d) > 3 for d in digit_split) and (len(digit_split) > 1)) or any(d is None for d in digit_split) or ((len(digit_split[-1]) < 3) and (len(digit_split) > 1))):
			default_keyboard(bot, update.message.chat_id, 'For numbers we support only integer input')
		else:
			send_amount(bot, update, text.replace(',', '').replace(' ', '').replace('mrai', ''))
	elif ('xrb_' in text):
		send_destination(bot, update, text)
	elif (text.startswith('@') and (len(text) > 3 )):
		send_destination_username(bot, update, text)
	elif (('block count' in text) or ('block_count' in text)):
		block_count_callback(bot, update)
	elif (('hello' in text) or ('start' in text)):
		start_text(bot, update)
	elif ('price' in text):
		price_text(bot, update)
	elif ('yes' not in text):
		#default_keyboard(bot, update.message.chat_id, 'Command not found')
		unknown(bot, update)


@run_async
def text_filter(bot, update):
	logging.info(update.message)
	ddos_protection(bot, update, text_filter_callback)

@run_async
def text_filter_callback(bot, update):
	user_id = update.message.from_user.id
	try:
		# Run result function
		text = update.message.text
		text_result(text, bot, update)
	except UnicodeEncodeError:
		default_keyboard(bot, update.message.chat_id, 'Sorry, but I can\'t read your text')


@run_async
def photo_filter(bot, update):
	logging.info(update.message)
	ddos_protection(bot, update, photo_filter_callback)

@run_async
def photo_filter_callback(bot, update):
	user_id = update.message.from_user.id
	try:
		image = update.message.photo[-1]
		path = '{1}download/{0}.jpg'.format(image.file_id, qr_folder_path)
		#print(image)
		newFile = bot.getFile(image.file_id)
		newFile.download(path)
		account = account_by_qr(path)
		print(account)
		if ('xrb_' in account):
			default_keyboard(bot, update.message.chat_id, 'Send to account *{0}*'.format(account))
			send_destination(bot, update, account)
		elif (('NULL' in account) or (account is None) or (account is False)):
			default_keyboard(bot, update.message.chat_id, 'Sorry, but I can\'t recognize your QR code')
		else:
			default_keyboard(bot, update.message.chat_id, 'Sorry, but I can\'t find xrb\_account in your QR code')
		#print(account)
		logging.info('QR by file: {0}'.format(account))
	except UnicodeEncodeError:
		default_keyboard(bot, update.message.chat_id, 'Sorry, but I can\'t read your text')


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
					bot.sendMessage(chat_id=chat_id, 
						text='Now your account is protected with password!\n*Dont\'t forget password, we cannot help you, if you lose it!\nDelete all messages with password so no one can retrieve pass from history!*', 
						parse_mode=ParseMode.MARKDOWN,
						disable_web_page_preview=True)
				else:
					update.message.reply_text('Password must include uppercase letters, lowercase letters and digits')
					logging.info('Password set failed for user {0}. Reason: uppercase-lowercase-digits'.format(user_id))
			else:
				update.message.reply_text('Your password is too short, please enter a longer password and try again. Password must be at least 8 characters including uppercase letters, lowercase letters and digits')
				logging.info('Password set failed for user {0}. Reason: Too short'.format(user_id))
		else:
			update.message.reply_text('You should delete old password before set new. Use command:\n/password_delete HereYourPass')
			logging.info('Password set failed for user {0}. Reason: Already protected'.format(user_id))
	else:
		update.message.reply_text('Use command\n/password HereYourPass')

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
			update.message.reply_text('Your old password was successfully deleted. Use this command to set new password:\n/password HereYourPass')
			logging.info('Password deletion for user {0}'.format(user_id))
		else:
			update.message.reply_text('Password you entered is incorrent. Try again')
			logging.info('Password deletion failed for user {0}. Reason: Wrong password'.format(user_id))
	else:
		update.message.reply_text('Use command\n/password_delete HereYourPass')


@run_async
def echo(bot, update):
	logging.info(update.message)
	update.message.reply_text(update.message.text)


@run_async
def ping(bot, update):
	logging.info(update.message)
	typing_illusion(bot, update.message.chat_id) # typing illusion
	sleep(2)
	default_keyboard(bot, update.message.chat_id, '@RaiWalletBot reporting')

@restricted
def stats(bot, update):
	logging.info(update.message)
	typing_illusion(bot, update.message.chat_id) # typing illusion
	fee_balance = account_balance(fee_account)
	stats = '{0}\nFees balance: {1} Mrai (XRB)'.format(mysql_stats(), "{:,}".format(int(fee_balance)))
	default_keyboard(bot, update.message.chat_id, stats)


@run_async
def unknown(bot, update):
	logging.info(update.message)
	user_id = update.message.from_user.id
	default_keyboard(bot, update.message.chat_id, 'Command not found'
						'\nPress \"Help\" to show available commands'
						'\nType /help for advanced usage')

@run_async
def unknown_ddos(bot, update):
	logging.info(update.message)
	user_id = update.message.from_user.id
	message_id = int(update.message.message_id)
	## DDoS ##
	ddos = mysql_ddos_protector(user_id, message_id)
	if (ddos == True):
		raise Exception('DDoS by user {0}'.format(user_id))
	elif (ddos == False):
		update.message.reply_text('You cannot send commands faster than once in {0} seconds'.format(ddos_protect_seconds))
		raise Exception('Too fast request by user {0}'.format(user_id))
	## DDoS ##
	default_keyboard(bot, update.message.chat_id, 'Command not found'
						'\nPress \"Help\" to show available commands'
						'\nType /help for advanced usage')

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
