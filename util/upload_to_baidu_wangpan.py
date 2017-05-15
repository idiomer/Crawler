#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
上传文件到百度网盘
>>> python upload_to_baidu_wangpan.py data/finance_news/finance_news.2017-05-14.csv.bz2 /Crawler/stock/finance_news/
"""

import sys
import os,json,sys,tempfile
from baidupcsapi import PCS

pcs = PCS('username','password')
chinksize = 1024*1024*16
fid = 1
md5list = []
tmpdir = tempfile.mkdtemp('bdpcs')
with open(sys.argv[1],'rb') as infile:
    while 1:
        data = infile.read(chinksize)
        if len(data) == 0: break
        smallfile = os.path.join(tmpdir, 'tmp%d' %fid)
        with open(smallfile, 'wb') as f:
            f.write(data)
        print('chunk%d size %d' %(fid, len(data)))
        fid += 1
        print('start uploading...')
        ret = pcs.upload_tmpfile(open(smallfile, 'rb'))
        md5list.append(json.loads(ret.content)['md5'])
        print('md5: %s' %(md5list[-1]))
        os.remove(smallfile)

os.rmdir(tmpdir)

remote_path=sys.argv[2] if not sys.argv[2].endswith('/') else sys.argv[2]+os.path.basename(sys.argv[1])
ret = pcs.upload_superfile(remote_path, md5list)
print ret.content

