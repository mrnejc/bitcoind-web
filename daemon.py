#!/usr/bin/env python
from bitcoinrpc.authproxy import AuthServiceProxy
import time, os, math

def log(logfile, loglevel, string):
    if loglevel > 1: # hardcoded loglevel here
        return False

    from datetime import datetime
    now = datetime.utcnow()
    string_time = now.strftime('%Y-%m-%d %H:%M:%S.')
    millisecond = now.microsecond / 1000
    string_time += "%03d" % millisecond

    with open(logfile, 'a') as f:
        line = string_time + ' LL' + str(loglevel) + ' ' + string
        # uncomment here to write debug.log to disk; default is terminal
#        f.write(line + '\n')
        print(line)
    
def init(cfg):
    try:
        rpcuser = cfg.get('rpcuser')
        rpcpassword = cfg.get('rpcpassword')
        rpcip = cfg.get('rpcip', '127.0.0.1')

        if cfg.get('rpcport'):
            rpcport = cfg.get('rpcport')
        elif cfg.get('testnet') == "1":
            rpcport = '18332'
        else:
            rpcport = '8332'

        if cfg.get('rpcssl') == "1":
            protocol = "https"
        else:
            protocol = "http"

        rpcurl = protocol + "://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    except:
        return False

    try:
        rpchandle = AuthServiceProxy(rpcurl, None, 500)
        return rpchandle
    except:
        return False

def rpcrequest(rpchandle, request, *args):
    try:
        log('debug.log', 2, 'rpcrequest: ' + request)

        request_time = time.time()
        response = getattr(rpchandle, request)(*args)
        request_time_delta = time.time() - request_time

        log('debug.log', 3, request + ' done in ' + "%.3f" % request_time_delta + 's')

        return response
    except:
        log('debug.log', 2, request + ' failed')
        return False

def getblock(rpchandle, block_to_get):
    try:
        if (len(str(block_to_get)) < 7) and str(block_to_get).isdigit(): 
            blockhash = rpcrequest(rpchandle, 'getblockhash', block_to_get)
        elif len(block_to_get) == 64:
            blockhash = block_to_get

        block = rpcrequest(rpchandle, 'getblock', blockhash)

        return block

    except:
        return 0

def loop(cfg):
    # TODO: add error checking for broken config, improve exceptions
    rpchandle = init(cfg)
    if not rpchandle: # TODO: this doesn't appear to trigger, investigate
        log('debug.log', 0, 'failed to connect to bitcoind (handle not obtained)')
        return True

    last_update = 0
    
    networkinfo = rpcrequest(rpchandle, 'getnetworkinfo')
    if not networkinfo:
        log('debug.log', 0, 'failed to connect to bitcoind (getnetworkinfo failed)')
        return True

    log('debug.log', 1, 'CONNECTED')

    prev_blockcount = 0
    while True:
        update_time = time.time()
        log('debug.log', 1, 'updating (' + "%.3f" % (time.time() - last_update) + 's since last)')

        nettotals = rpcrequest(rpchandle, 'getnettotals')
        connectioncount = rpcrequest(rpchandle, 'getconnectioncount')
        mininginfo = rpcrequest(rpchandle, 'getmininginfo')
        balance = rpcrequest(rpchandle, 'getbalance')
        unconfirmedbalance = rpcrequest(rpchandle, 'getunconfirmedbalance')

        blockcount = mininginfo['blocks']
        if blockcount:
            if (prev_blockcount != blockcount): # minimise RPC calls
                if prev_blockcount == 0:
                    lastblocktime = 0
                else:
                    lastblocktime = time.time()

                log('debug.log', 1, '=== NEW BLOCK ' + str(blockcount) + ' ===')

                block = getblock(rpchandle, blockcount)
                if block:
                    prev_blockcount = blockcount

                    try:
                        decoded_tx = rpcrequest(rpchandle, 'getrawtransaction', block['tx'][0], 1)

                        coinbase_amount = 0
                        for output in decoded_tx['vout']:
                            if 'value' in output:
                                coinbase_amount += output['value']
                    except: pass 

        # generate HTML; not ideal, but works as a proof-of-concept
        with open('www/index.html.tmp', 'w') as f:
            f.write('<!DOCTYPE html>\n')
            f.write('<html lang="en">\n')
            f.write('   <head>\n')
            f.write('       <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n')
            f.write('       <script>\n')
            f.write('           setTimeout(function(){ location.reload() }, 1000);\n')
            f.write('       </script>\n')
            f.write('       <title>bitcoind-web test</title>\n')
            f.write('       <link rel="stylesheet" type="text/css" href="index.css">')
            f.write('   </head>\n')
            f.write('\n')
            f.write('   <body>\n')
            f.write('       <h1>bitcoind-web v0.0.1</h1>\n')
            f.write('\n')
        
            tmplt = '       <p>\n%s\n       </p>\n'

            if 'subversion' in networkinfo:
               version = networkinfo['subversion']
            else:
                version = 'v' + str(networkinfo['version'])
            if 'chain' in mininginfo:
                chain = mininginfo['chain']
            else:
                blockchaininfo = rpcrequest(rpchandle, 'getblockchaininfo')
                chain = blockchaininfo['chain']
            f.write(tmplt % ('Connected to daemon ' + version + ' on ' + chain + ' chain'))
            string_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(last_update))

            if 'errors' in mininginfo:
                f.write(tmplt % ('<b>' + mininginfo['errors'] + '</b>'))

            f.write(tmplt % ('Last update ' + string_time))

            kb_recv = "%.0f" % (nettotals['totalbytesrecv'] / 1024)
            kb_sent = "%.0f" % (nettotals['totalbytessent'] / 1024)
            f.write(tmplt % ('Received: ' + kb_recv + 'KB Sent: ' + kb_sent + 'KB Peers: ' + str(connectioncount)))
            string = 'Balance: ' + str(balance) + ' BTC' 
            if unconfirmedbalance:
                string += '(+' + str(unconfirmedbalance) + ' unconf)'
            f.write(tmplt % string)

            if block:
                string = 'Block height: ' + str(block['height'])
                string += '<br />\n' + 'Block hash: ' + str(block['hash'])
                string += '<br />\n' + 'Block size: ' + str(block['size']) + ' bytes (' + str(block['size']/1024) + ' KB)'
                string += '<br />\n' + 'Block timestamp: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(block['time']))

                tx_count = len(block['tx'])
                bytes_per_tx = block['size'] / tx_count
                string += '<br />\n' + 'Block transactions: ' + str(tx_count) + ' (' + str(bytes_per_tx) + ' bytes/tx)'

                if coinbase_amount:
                    if block['height'] < 210000:
                        block_subsidy = 50
                    elif block['height'] < 420000:
                        block_subsidy = 25
                    elif block['height'] < 630000:
                        block_subsidy = 12.5

                    if block_subsidy: # this will fail after block 630,000. TODO: stop being lazy and do it properly
                        total_fees = coinbase_amount - block_subsidy # assumption, mostly correct

                        if coinbase_amount > 0:
                            fee_percentage = "%0.2f" % ((total_fees / coinbase_amount) * 100)
                            coinbase_amount_str = "%0.8f" % coinbase_amount
                            string += '<br />\n' + 'Block reward: ' + coinbase_amount_str + ' BTC (' + fee_percentage + '% fees)'
                        if tx_count > 1:
                            tx_count -= 1 # the coinbase can't pay a fee
                            fees_per_tx = (total_fees / tx_count) * 1000
                            fees_per_kb = ((total_fees * 1024) / block['size']) * 1000
                            total_fees_str = "%0.8f" % total_fees + ' BTC'
                            fees_per_tx = "%0.5f" % fees_per_tx + ' mBTC/tx'
                            fees_per_kb = "%0.5f" % fees_per_kb + ' mBTC/KB'
                            string += '<br />\n' + 'Block fees: ' + total_fees_str + ' (avg ' +  fees_per_tx + ', ~' + fees_per_kb + ')'

                f.write(tmplt % string)

                if 'chainwork' in block:
                    log2_chainwork = math.log(int(block['chainwork'], 16), 2)
                    f.write(tmplt % ('Chain work: 2**' + "%0.6f" % log2_chainwork))

            f.write(tmplt % ('Mempool transactions: ' + str(mininginfo['pooledtx'])))

            f.write('\n')
            f.write('   </body>\n')
            f.write('</html>')

            f.flush()
            os.fsync(f.fileno()) 
            f.close()

            os.rename('www/index.html.tmp', 'www/index.html')

        last_update = time.time()
        update_time_delta = last_update - update_time
        log('debug.log', 1, 'update done in ' + "%.3f" % update_time_delta + 's')

        # sleep before next loop
        time.sleep(2)
