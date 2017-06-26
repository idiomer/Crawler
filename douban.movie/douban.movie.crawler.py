#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

# num_per_page = 20
# now_start = 0

# for now_start in xrange(0, 50*num_per_page, num_per_page):
#     # url = u"https://movie.douban.com/tag/综艺"
#     url = u"https://movie.douban.com/tag/国产电视剧"
#     params = {"start": now_start, "type": "T"}
#     resp = requests.get(url, params=params, verify=False)

#     if resp.ok:
#         bs = BeautifulSoup(resp.content, 'lxml')
#         items = bs.find_all('div', attrs={"class": "pl2"})
#         print "\n".join([it.find('a').text.strip().replace('\n', ' ') for it in items]).encode('utf-8')
#     else:
#         print resp.status_code
#         print resp.reason
#         raise Exception("get url page fail")

def rstrip_digit(x):
    ##??todo: 三国演义（精编版）说的就是你II  少年包青天Ⅲ之天芒传奇
    if len(x)==0 or not x[-1].isdigit():
        return x
    else:
        return rstrip_digit(x[:-1])

def zhi_cut(x):
    pos = x.find(u'之')
    if pos < 0 or pos == 1 or pos == len(x)-1:
        return x
    else:
        return '\n'.join(x.split(u'之'))


def getShowName(line):
    line = line.decode('utf-8') if isinstance(line, str) else line.lower()
    raw_name = line.split('/', 1)[0].strip()
    strip_suffix_name = raw_name.split()[0]
    return zhi_cut(rstrip_digit(strip_suffix_name).encode('utf-8'))

if __name__ == '__main__':
    for line in open('raw_show_names.txt'):
        print getShowName(line)
