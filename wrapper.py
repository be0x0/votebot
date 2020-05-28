from importlib import reload
from itertools import cycle
import votebot as vb
import time

proxylist = vb.gen_proxies()

proxy_pool = cycle(proxylist)

totalTries = 0
totalVotes = 0

while True:
    results = vb.update_results()
    if int(results['margin']) >= 420: # Try to win by 420
        time.sleep(300) 
    else:
        tries = 2   # Max continuous votes
        proxies = [ # Get next set of proxies
            next(proxy_pool)
            for i in range(tries)
        ]
        initVotes = results['team1']

        #Vote and get results
        vb.cast_votes(tries,proxies)
        results = vb.update_results()
        print(results)

        # Update total tries, total votes, and find change in votes
        endVotes = results['team1']
        diffVotes = endVotes - initVotes        
        totalVotes = totalVotes + diffVotes
        totalTries = totalTries + tries
        
        # "hit rate" tracks the percent of votes that actually go through, e.g. the % of proxies that worked
        print('Instantaneous hit rate: ' + str(diffVotes/tries))
        print('Total hit rate: ' + str(totalVotes/totalTries))
        time.sleep(5)   # Rest for a bit, let's not get too crazy
