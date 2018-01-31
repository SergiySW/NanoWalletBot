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

import ConfigParser
import math
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
salt = config.get('password', 'salt')

import sys
import hashlib, binascii
def hash():
	password = raw_input('Enter a password: ')
	dk = hashlib.pbkdf2_hmac('sha256', password, salt, 112000)
	hex = binascii.hexlify(dk)
	print(hex)

hash()