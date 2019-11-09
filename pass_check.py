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

import sys
import hashlib, binascii
def hash():
	password = input('Enter a password: ')
	dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode(), 112000)
	hex = binascii.hexlify(dk).decode()
	print(hex)

hash()