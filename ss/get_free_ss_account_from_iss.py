#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import json

issURL = 'http://ss.ishadowx.com'
resp = requests.get(issURL)
resp.encoding='utf-8'

tag = r'(?:<.*?>)?' #not-catch into group; exist or not

reIp = re.compile(ur'IP Address ?[:：] ?%s([\w\.]+)'%(tag))
rePort = re.compile(ur'Port ?[:：] ?%s(\d+)'%(""))
rePassword = re.compile(ur'Password ?[:：] ?%s(\w+)'%(tag))
reMethod = re.compile(ur'Method ?[:：] ?%s([\w-]+)'%(tag))

ips = reIp.findall(resp.text)
ports = rePort.findall(resp.text)
passwords = rePassword.findall(resp.text)
methods = reMethod.findall(resp.text)

print len(ips), len(ports), len(passwords), len(methods)

cfgs = {}
cfgs["localPort"] = 1080
cfgs["shareOverLan"] = False
cfgs["configs"] = list()
for i in xrange(min(len(ips), len(ports), len(passwords), len(methods))):
	cfg = {}
	cfg["server"] = ips[i]
	cfg["server_port"] = int(ports[i])
	cfg["password"] = passwords[i]
	cfg["method"] = methods[i]
	cfg["remarks"] = ips[i]
	cfgs["configs"].append(cfg)

with open("ss.config.json", "w") as fw:
	data = json.dumps(cfgs, ensure_ascii=False, indent=2)
	data = data if isinstance(data, str) else data.encode('utf-8')
	fw.write(data)
