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

# QR code handler
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('bot.cfg')
qr_folder_path = config.get('main', 'qr_folder_path')


import pyqrcode
import os.path
#@run_async
def qr_by_account(account):
	path = '{1}{0}.png'.format(account, qr_folder_path)
	if (not os.path.isfile(path)):
		qr = pyqrcode.create(account, error='L', version=4, mode=None, encoding='iso-8859-1')
		qr.png('{1}{0}.png'.format(account, qr_folder_path), scale=8)

import qrtools
from PIL import Image, ImageEnhance
def account_by_qr(qr_file):
	qr = qrtools.QR()
	qr.decode(qr_file)
	# Try to increase contrast if not recognized
	if ('xrb_' not in qr.data):
		image = Image.open(qr_file)
		contrast = ImageEnhance.Contrast(image)
		image = contrast.enhance(7)
		image.save('{0}'.format(qr_file.replace('.jpg', '_.jpg')), 'JPEG')
		qr2 = qrtools.QR()
		qr2.decode('{0}'.format(qr_file.replace('.jpg', '_.jpg')))
		#print(qr2.data)
		qr = qr2
	returning = qr.data.replace('raiblocks://', '').replace('raiblocks:', '').split('?')
	# parsing amount
	if (len(returning) > 1):
		if 'amount=' in returning[1]:
			returning[1] = returning[1].replace('amount=', '')
			# don't use empty
			if (len(returning[1]) == 0):
				returning.pop()
		else:
			returning.pop()
	return returning

