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

import math
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
salt = config.get('password', 'salt')
pbkdf2_iterations = int(config.get('password', 'pbkdf2_iterations'))

import sys
import hashlib, binascii
def hash():
	password = input('Enter a password: ')
	user_id = int(input('Enter user ID: '))
	dk = hashlib.scrypt(password.encode('utf-8'), salt=(hashlib.sha3_224(user_id.to_bytes(6, byteorder='little')).hexdigest()+salt).encode('utf-8'), n=2**15, r=8, p=1, maxmem=2**26, dklen=64)
	hex = binascii.hexlify(dk).decode()
	print('Password hash: ' + hex)
	dk_old = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode(), pbkdf2_iterations)
	hex_old = binascii.hexlify(dk_old).decode()
	print('Password hash old type: ' + hex_old)

hash()