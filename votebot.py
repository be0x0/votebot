import random
import re
import time
import requests
import asyncio
import concurrent.futures

# Replace with your own payload
payload = {'poll': 123456, 'vote': 'Team 1'}

# Replace with your own headers
voteHeader = {'Host': 'https://www.targeturl.com', 'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded', 'Accept': '*/*',
            'Origin': 'https://www.targeturl.com', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.targeturl.com/poll.html',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9'}

# Header to use when checking results
resultHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=-1', 'Connection': 'keep-alive',
    'Cookie': '',
    'Host': 'www.targeturl.com', 'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'no-cors', 'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?0', 'Sec-Fetch-Dest': 'empty',
    'User-Agent': 'Mozilla/4.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}


# Import SOCKS4 proxy list
def get_socks4():
    proxies = []
    with open("socks4list.txt") as file:
        for line in file:
            line = line.strip()
            line = 'socks4://' + line
            proxies.append(line)
    proxies.pop() # Remove ending whitespace
    return proxies


# Import SOCKS5 proxy list
def get_socks5():
    proxies = []
    with open("socks5list.txt") as file:
        for line in file:
            line = line.strip()
            line = 'socks5://' + line
            proxies.append(line)
    proxies.pop()
    return proxies


# Import HTTPS proxy list
def get_https():
    proxies = []
    with open("httpslist.txt") as file:
        for line in file:
            line = line.strip()
            line = 'https://' + line
            proxies.append(line)
    proxies.pop()   
    return proxies


# Shortcut to import all proxies at once and shuffle the list.
def gen_proxies():
    socks4 = get_socks4()
    socks5 = get_socks5()
    https = get_https()
    proxies = socks4 + socks5 + https
    random.shuffle(proxies)
    return proxies


def good_proxies():
    proxies = []
    with open("newgoodlist.txt") as file:
        for line in file:
            line = line.strip()
            proxies.append(line)
    proxies.pop()   
    random.shuffle(proxies)
    return proxies

# Gets the results by getting the main page and looking for a regex match. You'll need to change the regex depending on the poll.
def update_results():
    url = 'https://www.targeturl.com/poll.html'
    r = requests.get(url=url, headers=resultHeader)
    update = re.findall("(\w{1,10} [0-9]{4})|(\d{1,5}(?= votes))", r.text)  # Regex. Group 1 is a 1-10 characters (team name) followed by a 4 digits (year). 
                                                                            # Group 2 is a number followed by ' votes', excluding the ' votes'.
    results = []
    for i in range(len(update)):    # Looks for group 2 matches (vote counts) and adds them to the results array with the previous group 1 match (team name).
        if update[i][1] != '':
            results.append(update[i - 1][0])
            results.append(update[i][1])
            
    if results[4] == 'team 1':  # Check the results order- higher scoring team is always ranked first. 
        team1 = int(results[5])
        team2 = int(results[7])
    else:
        team1 = int(results[7])
        team2 = int(results[5]) 

    margin = team1 - team2  # Calculates how much team 1 is winning by.
    results = { 'team 1':team1, 'team 2': team2, 'margin': margin }
    return results


def vote(proxy):
    code = 0
    proxyArg = {'http':proxy, 'https':proxy}    # Correct formatting for requests.post()
    url = "https://www.targeturl.com/cf/remote.cfc?method=remote_poll&noCache=" + str(int(time.time() * 1e3))
    try:
        r = requests.post(url=url, data=payload, headers=voteHeader, proxies=proxyArg, timeout=10)

        if r.status_code == 500:    # 500 error probably means the payload or address is wrong. Check request data.
            print('error code: ' + str(r.status_code))
            print('Request data: ' + r.request.data)
            print('Response data: ' + r.response.data)
    except Exception as e:  # Assume error is a bad proxy. Track which proxies work and which don't for future reference.
        print('Proxy: ' + proxy)
        print('Error: ' + str(e))
        with open('badproxies.txt', 'a') as file:
            file.write(proxy+'\n')
    else:
        print('Good proxy: ' + proxy)
        with open('goodproxies.txt', 'a') as file:
            file.write(proxy+'\n')


async def multi_vote(threads, proxies):
    # Casts an arbitrarily large number of votes at once and and waits for them all to finish.
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor,
                vote,
                proxies[i]
            )
            for i in range(threads)
        ]
        for response in await asyncio.gather( * futures):   
            pass


def cast_votes(tries, proxies): # Basically just asyncio sample code. No idea how this works.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(multi_vote(tries, proxies))
