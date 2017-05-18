#!/usr/bin/env python
#-*- coding: utf-8 -*-

import tushare as ts
import sys
import gzip, bz2

newsDF = ts.get_latest_news(top=1000, show_content=True)
# print newsDF.columns #Index([u'classify', u'title', u'time', u'url', u'content'], dtype='object')
# print newsDF['time'].map(lambda x:x.split()[0]),unique()

yesterday = sys.argv[1] #2017-05-01
year, monthday = yesterday.split('-', 1) #2017, 05-01
assert(len(monthday)==5 and monthday[:2].isdigit() and monthday[2]=='-' and monthday[3:].isdigit())

output_file = 'data/finance_news/finance_news.%s.csv.bz2'%(yesterday)
target = newsDF[newsDF['time'].map(lambda x:x.split()[0])==monthday]
target.to_csv(bz2.BZ2File(output_file, "w"), index=False, encoding='utf-8')
print "save %d finance news(%s) to %s "%(len(target), yesterday, output_file)
