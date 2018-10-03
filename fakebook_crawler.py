# -*- coding: utf-8 -*-
"""
Authors: Jason Teng, Seung Son
2018-10-2

This file contains the code for CS 5700 Project 2
"""

import socket, select, argparse, htmllib, xml

parser = argparse.ArgumentParser(description='Client script for Project 2.')
parser.add_argument('username', help='the username of the account')
parser.add_argument('password', help='the password of the account')

args = parser.parse_args()

# Connection params
base_url = 'cs5700f18.ccs.neu.edu'
DEFAULT_PORT = 80

username = args.username
password = args.password

# takes a HTTP message and returns the raw header and html as separate strings
def parseResponse(response):
    s = response.split('\n\n', 1)
    return s[0], s[1]

def getCookie(headers, cookiename):
    cookies = headers['Set-Cookie']
    cstart = cookies.find(cookiename + '=') + len(cookiename) + 1
    cend = cookies.find(';', cstart)
    return cookies[cstart:cend]

# takes a HTTP message and returns a dictionary of the headers
def parseHeaders(rawheaders):
    headers = {}
    rawheaders = rawheaders.split('\r\n')[1:-1]
    for s in rawheaders:
        header = s.split(':', 1)
        if headers.has_key(header[0]):
            headers[header[0]] += '\n' + header[1]
        else:
            headers[header[0]] = header[1]
    return headers

# Performs a GET from the fakebook homepage to get a CSRF token
def getCSRFToken(s):
    message = 'GET http://' + base_url + '''/accounts/login/?next=/fakebook/ HTTP/1.1
Host: cs5700f18.ccs.neu.edu\r\n\r\n'''
    s.send(message)
    response = ''
    try:
        readable, writable, errored = select.select([s,], [], [], 30)
    except select.error:
        s.close()
        exit()
    if len(readable) > 0:
        response = s.recv(8192)
    else:
        print('timeout')
    
    rawheaders, rawhtml = parseResponse(response)
    headers = parseHeaders(rawheaders)
    return getCookie(headers, 'csrftoken')


# logs into Fakebook using the given socket, username, and password, and returns
# the sessionid for the user session.
def login(s, username, password, csrftoken):
    headers = 'POST http://' + base_url + '''/accounts/login/ HTTP/1.1
Host: cs5700f18.ccs.neu.edu
Cookie: csrftoken=''' + csrftoken + ''';
Content-Type: application/x-www-form-urlencoded
Content-Length: ''' + str(40 + len(username) + len(password) + len(csrftoken)) + '\r\n\r\n'
    content = 'username=' + username + '&password=' + password \
        + '&csrfmiddlewaretoken=' + csrftoken + '&next=%2Ffakebook%2F' + '\r\n'
    message = headers + content
    s.send(message)
    response = ''
    try:
        readable, writable, errored = select.select([s,], [], [], 10)
    except select.error:
        s.close()
        exit()
    if len(readable) > 0:
        response = s.recv(8192)
    else:
        print('timeout')
    
    rawheaders, rawhtml = parseResponse(response)
    headers = parseHeaders(rawheaders)
    return getCookie(headers, 'sessionid')
    
def handleMessage(message, s):
    print message

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((base_url, DEFAULT_PORT))

# GET from login page to get csrf token
csrftoken = getCSRFToken(s)

# login and get sessionid
sessionid = login(s, username, password, csrftoken)
print sessionid

# Event loop
