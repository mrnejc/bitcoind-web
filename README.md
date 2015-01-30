bitcoind-web v0.0.1
===================

html monitor for bitcoind

![ScreenShot](/screenshots/bitcoind-web.png)

produced by Amphibian (azeteki, Atelopus_zeteki)

dependencies
------------

* tested with python 2.7.3, bitcoind 0.9.4
* jgarzik's bitcoinrpc library (https://github.com/jgarzik/python-bitcoinrpc)

features
--------

* updating ticker showing bitcoind's status (via RPC)

usage
-----

copy your bitcoin.conf to bitcoind-web's folder

alternatively, create a file with the following details:
```
rpcuser=xxx
rpcpassword=yyy
testnet=0
```

this is an early development release. expect (safe) breakage

launch
------

replace 'python' with 'python2' if you also have python3 installed.
```
$ python main.py
$ python main.py -c some_other_config_file.conf
```

the file www/index.html will begin to auto-update - open it in your web browser.
JavaScript auto-refresh is enabled - otherwise, press F5 to manually refresh

frog food
---------

found bitcoind-web useful? donations are your way of showing that!

![ScreenShot](/screenshots/donation-qr.png)

**1FrogqMmKWtp1AQSyHNbPUm53NnoGBHaBo**
