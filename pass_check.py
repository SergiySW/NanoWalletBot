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