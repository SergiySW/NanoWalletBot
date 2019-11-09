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


# Parse config
from six.moves import configparser
config = configparser.ConfigParser()
config.read('bot.cfg')
url = config.get('main', 'url')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')


# Request to node
from common_rpc import *


result = unlock(wallet, password)
print(result)
