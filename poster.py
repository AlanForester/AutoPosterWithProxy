import requests
import datetime
import random
import time

from random import randint
from threading import Thread
from faker import Factory


class Poster:
    post_url = None
    start_rid = 0
    current_rid = 0
    post_script = None
    proxies = None
    max_threads = 200
    threads = None
    ua = None
    faker = None

    def __init__(self):
        self.post_url = "http://www.domain.ru/srv/addcomment"
        script_file = open("./data/script.txt", "r")
        self.post_script = script_file.read()
        script_file.close()
        proxies_file = open("./data/proxies.txt", "r")
        proxies = proxies_file.readlines()
        self.proxies = []
        for proxy in proxies:
            self.proxies.append({
                'url': proxy.strip(),
                'cookies': None,
                'ua': 'Mozilla/{r1}.0 (X11; CrOS i686 {r2}.{r3}.0) AppleWebKit/{r4}.{r5} (KHTML, like Gecko) Chrome/{r6}.0.{r7}.{r8} Safari/{r9}.{r10}'.format(
                    r1=randint(1, 10),
                    r2=randint(1, 20),
                    r3=randint(1, 500),
                    r4=randint(1, 999),
                    r5=randint(1, 999),
                    r6=randint(1, 30),
                    r7=randint(1, 999),
                    r8=randint(1, 999),
                    r9=randint(1, 999),
                    r10=randint(1, 20),
                )
            })
        self.threads = []
        self.current_rid = 0
        self.faker = Factory.create('ru_RU')

    def start_service(self, start_rid, end_rid):
        print("Start cleaning pool")
        cleaner = Thread(target=self.clean_died_threads)
        cleaner.setDaemon(True)
        cleaner.start()

        rid_file = open("./data/rid.txt", "r+")
        rid = rid_file.read().strip()
        if rid == "None" or rid == "":
            rid = start_rid
        self.current_rid = int(rid)
        while self.current_rid <= end_rid:
            if len(self.threads) < self.max_threads:
                if self.current_rid % 5 == 0:
                    print("Run new thread on {cr}".format(cr=self.current_rid))
                    thread = Thread(target=self.post, args=(self.current_rid,))
                    thread.setDaemon(True)
                    thread.start()
                    self.threads.append(thread)
                self.current_rid += 1
            else:
                time.sleep(1)

        for thread in self.threads:
            thread.join()
        print("Job completed " + str(len(self.threads)))

    def clean_died_threads(self):
        while True:
            for thread in self.threads:
                if not thread.is_alive():
                    self.threads.remove(thread)
            print("Threads count: " + str(len(self.threads)))
            time.sleep(1)

    def post(self, rid):
        rid_file = open("./data/rid.txt", "r+")

        proxy = self.get_proxy()
        self.send_request(rid, proxy)

        rid_file.write(str(rid))
        rid_file.close()

    def get_proxy(self, proxy=None):
        if proxy:
            print("Select new proxy")
            self.proxies.remove(proxy)

        select = random.choice(self.proxies)
        try:
            if not select['cookies']:
                response = requests.get(
                    url='http://www.neberitrubku.ru',
                    proxies={
                        "http": "http://" + select['url']
                    },
                    timeout=5
                )
                if response.cookies:
                    select['cookies'] = dict(response.cookies)
                    requests.get(
                        url='https://www.neberitrubku.ru/nomer-telefona/89263592706',
                        proxies={
                            "http": "http://" + select['url']
                        },
                        cookies=select['cookies']
                    )
                    return select
                else:
                    return self.get_proxy(select)
        except requests.exceptions.RequestException:
            return self.get_proxy(select)

    def send_request(self, rid, proxy, repeat=''):
        log_file = open("./logs/" + datetime.datetime.now().strftime("%Y-%m-%d") + ".txt", "a+")
        try:
            response = requests.get(
                url=self.post_url,
                params={
                    "rid": rid,
                    "name": self.faker.name(),
                    "comment": self.post_script,
                },
                proxies={
                    "http": "http://" + proxy['url']
                },
                headers={
                    'User-Agent': proxy['ua'],
                    'Cookie': "jwt=" + proxy['jwt']
                },
                timeout=10
            )
            split_test = str(response.content).split('|')
            if split_test[0] == 'b\'OK':
                r = ''
                if repeat != '':
                    r = '[{repeat}] '.format(repeat=repeat)
                log_file.write('{r}{time} {rid}: {status_code} {content} \n'.format(
                    r=r,
                    time=datetime.datetime.now().strftime("%H:%M:%S"),
                    rid=rid,
                    status_code=response.status_code,
                    content=response.content
                ))
                log_file.close()
                return
            else:
                log_file.close()
                return self.send_request(rid, self.get_proxy(proxy), 'REPEAT')

        except requests.exceptions.RequestException:
            log_file.write('[ERROR] {time} {rid}: Failed \n'.format(
                time=datetime.datetime.now().strftime("%H:%M:%S"),
                rid=rid
            ))
            log_file.close()
            return self.send_request(rid, self.get_proxy(proxy), 'REPEAT')

    @staticmethod
    def start():
        model = Poster()
        model.post(32251102)
        # model.start_service(30000000, 50068238)

