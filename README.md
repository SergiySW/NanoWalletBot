# RaiWalletBot
[@RaiWalletBot](https://t.me/RaiWalletBot) — Open source Telegram bot for [RaiBlocks](https://github.com/clemahieu/raiblocks) cryptocurrency   

# Python requirements
**Required non-default Python libraries**   
python-urllib3   
python-requests   
python-mysql.connector   
python-qrtools   
**Installed with pip (pip install)**   
pypng   
PyQRCode   
python-telegram-bot   

# Other software configurations
rai_node config sample in config.json   
MySQL database structure in mysql.sql   
Nginx config sample in nginx_site.conf   

# rai_node config.json tuning
If you use docker node, set "address": "::0.0.0.0"   

0.1 Mrai (XRB) incoming limit: "receive_minimum": "100000000000000000000000000000"   
https://github.com/clemahieu/raiblocks/wiki/Distribution-and-Mining#Divider   

# Start bot
Create wallet with `curl -g -d '{ "action": "wallet_create" }' http://localhost:7076`   
Set password with `curl -g -d '{ "action": "password_change", "wallet": "WALLETID", "password": "WalletPassword123" }' http://localhost:7076`   
Edit bot.cfg with your preferences   
Start bot `python raiwalletbot.py`   
Start callback incoming transactions server `python frontiers_callback.py`   
Set cron job for `python frontiers.py` and other scripts if required   

# Thanks
* [clemahieu](https://github.com/clemahieu) for RaiBlocks creation and development
* [Mike Row](https://github.com/mikerow), [HostFat](https://github.com/hostfat),  [James Coxon](https://github.com/jamescoxon) for alpha testing and great advices
* gotowerdown for Indonesian translation
* reee for Italian translation
* Freddynic159 for Spanish translation
* zzSunShinezz for Vietnamese translation
