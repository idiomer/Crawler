#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr

import requests
import datetime
import subprocess
from optparse import OptionParser

import urllib3
urllib3.disable_warnings()

cfg_global = {
    "mail": {
        "address": "172.16.1.100:25",
        "from": "test <test@notify>",
        "to": [
            "xxx <xxx@yyy>",
        ],
        "cc": [
             "xx <xx@yy>",
        ],
    },
}

def _format_address(s):
    name, address = parseaddr(s)
    return formataddr((
        Header(name, 'utf-8').encode(),
        address.encode('utf-8') if isinstance(address, unicode) else address))

def send_mail(subject, message, attach=None):
    cfg = cfg_global["mail"]
    from_address = parseaddr(cfg["from"])[1]
    to_addresses = []

    for i in cfg["to"]:
        to_addresses.append(parseaddr(i)[1])
    if "cc" in cfg:
        for i in cfg["cc"]:
            to_addresses.append(parseaddr(i)[1])

    # msg = MIMEText(message, 'plain', 'utf-8')
    msg = MIMEMultipart()

    msg['From'] = _format_address(cfg["from"])  # from
    msg['To'] = ", ".join([_format_address(i) for i in cfg["to"]])
    if "cc" in cfg:
        msg['Cc'] = ", ".join([_format_address(i) for i in cfg["cc"]]) # to
    msg['Subject'] = Header(subject, 'utf-8').encode() #subject
    msg.attach(MIMEText(message, 'plain', 'utf-8')) # body

    if attach is not None:
        att = MIMEText(open(attach, 'rb').read(), 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="%s"'%(os.path.basename(attach))
        msg.attach(att)

    server = smtplib.SMTP()
    server.set_debuglevel(0)
    server.connect(cfg["address"])
    server.sendmail(from_address, to_addresses, msg.as_string())
    server.quit()

if __name__ == '__main__':
    subject = sys.argv[1]
    message = sys.argv[2]
    attach = sys.argv[3]
    send_mail(subject, message, attach)
