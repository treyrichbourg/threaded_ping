#!/usr/bin/env python
# ping a list of host with threads for increase speed
# use standard linux /bin/ping utility

from threading import Thread
import subprocess

try:
    import queue
except ImportError:
    import Queue as queue
import re
import timeit

start = timeit.default_timer()
# some global vars
num_threads = 15
ips_q = queue.Queue()
out_q = queue.Queue()

with open("./workstations.txt") as f:
    rough_data = f.readlines()
    ips = [i.rstrip("\n") for i in rough_data]


# thread code : wraps system ping command
def thread_pinger(i, q):
    """Pings hosts in queue"""
    while True:
        # get an IP item form queue
        ip = q.get()
        # ping it
        args = ["/bin/ping", "-c", "1", "-W", "1", str(ip)]
        p_ping = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
        # save ping stdout
        p_ping_out = str(p_ping.communicate()[0])

        if p_ping.wait() == 0:
            # rtt min/avg/max/mdev = 22.293/22.293/22.293/0.000 ms
            search = re.search(
                r"rtt min/avg/max/mdev = (.*)/(.*)/(.*)/(.*) ms",
                p_ping_out,
                re.M | re.I,
            )
            ping_rtt = search.group(2)
            out_q.put("OK " + str(ip) + " rtt= " + ping_rtt)
        else:
            out_q.put(f"DOWN {ip}")

        # update queue : this ip is processed
        q.task_done()


# start the thread pool
for i in range(num_threads):
    worker = Thread(target=thread_pinger, args=(i, ips_q))
    worker.setDaemon(True)
    worker.start()

# fill queue
for ip in ips:
    ips_q.put(ip)

# wait until worker threads are done to exit
ips_q.join()

# print result
while True:
    try:
        msg = out_q.get_nowait()
    except queue.Empty:
        break
    print(msg)

stop = timeit.default_timer()
print(f"{(stop - start)} seconds")
