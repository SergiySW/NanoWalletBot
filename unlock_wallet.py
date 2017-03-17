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


# Parse config
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('bot.cfg')
url = config.get('main', 'url')
wallet = config.get('main', 'wallet')
password = config.get('main', 'password')


# Request to node
from common_rpc import *


result = unlock(wallet, password)
print(result)
