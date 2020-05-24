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

# MySQL requests
from common_mysql import mysql_select_seed

def seed_data():
	user_id = input('Enter user ID: ')
	seed = mysql_select_seed (user_id)
	print(seed)

seed_data()
