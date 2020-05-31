# NanoWalletBot
[@NanoWalletBot](https://t.me/NanoWalletBot) — Open source Telegram bot for [Nano](https://github.com/nanocurrency/nano-node) cryptocurrency   

# Python requirements
**Required non-default Python3 libraries**   
python3-urllib3   
python3-requests   
python3-mysql.connector   
python3-pil   
python3-qrtools   
python3-socks   
**Installed with pip (pip3 install)**   
pycryptodomex   
pypng   
PyQRCode   
python-telegram-bot   
six   
websockets   

# Other software configurations
nano_node config sample in config-node.toml   
RPC config sample in config-rpc.toml   
MySQL database structure in mysql.sql   
Nginx config sample in nginx_site.conf   

# RPC config tuning
If you use docker node, set `address = "::0.0.0.0"`   

# nano_node config tuning
0.1 Nano incoming limit:   
```   
[node]   
receive_minimum = "100000000000000000000000000000"   
```   
https://docs.nano.org/protocol-design/distribution-and-units/#unit-dividers   

# Start bot
Create wallet with `curl -g -d '{ "action": "wallet_create" }' http://localhost:7076`   
Set password with `curl -g -d '{ "action": "password_change", "wallet": "WALLETID", "password": "WalletPassword123" }' http://localhost:7076`   
Edit `sample.bot.cfg` with your preferences and save as `bot.cfg` (don't forget to change `salt`, `aes_password`, `private_key` & other passwords)   
Start bot `python3 raiwalletbot.py`   
Start websockets incoming transactions server `python3 frontiers_websockets.py`   
Set cron job for `python3 frontiers.py` and other scripts if required   

# Thanks
* [clemahieu](https://github.com/clemahieu) for RaiBlocks creation and development
* [Mike Row](https://github.com/mikerow), [HostFat](https://github.com/hostfat),  [James Coxon](https://github.com/jamescoxon) for alpha testing and great advices
* gotowerdown for Indonesian translation
* reee for Italian translation
* [Freddy Morán Jr.](https://github.com/Freddynic159) for Spanish translation
* zzSunShinezz for Vietnamese translation
* [George Mamar](https://github.com/georgem3) for German translation
