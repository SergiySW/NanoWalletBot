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

import hashlib, binascii

# MySQL requests
from common_mysql import mysql_select_seed

def seed_data():
	user_id = input('Enter user ID: ')
	seed = mysql_select_seed (user_id)
	print(seed)
	# Seed checksum
	blake2b_checksum = hashlib.blake2b(digest_size=2)
	blake2b_checksum.update(binascii.unhexlify(seed))
	print('Checksum: ' + blake2b_checksum.hexdigest().upper())

seed_data()
