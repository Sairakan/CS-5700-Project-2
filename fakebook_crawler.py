# -*- coding: utf-8 -*-
"""
Authors: Jason Teng, Seung Son
2018-10-2

This file contains the code for CS 5700 Project 2
"""

import socket, select, argparse, htmllib, xml
from HTMLParser import HTMLParser

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
    s = response.split('\r\n\r\n', 1)
    if len(s) < 2:
        return s[0], ''
    return s[0], s[1]

def getCookie(headers, cookiename):
    cookies = headers['Set-Cookie']
    cstart = cookies.find(cookiename + '=') + len(cookiename) + 1
    cend = cookies.find(';', cstart)
    return cookies[cstart:cend]

# takes a HTTP message and returns a dictionary of the headers
def parseHeaders(rawheaders):
    headers = {}
    rawheaders = rawheaders.splitlines()[1:-1]
    for s in rawheaders:
        header = s.split(':', 1)
        if headers.has_key(header[0]):
            headers[header[0]] = headers.get(header[0]) + '\n' + header[1]
        else:
            headers[header[0]] = header[1]
    return headers

def getResponse(s, message):
    print ('MESSAGE:\n' + message)
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
    if headers.has_key('Content-Length'):
        bodylength = int(headers['Content-Length'])-1
        while len(rawhtml) < bodylength:
            rawhtml += s.recv(8192)
    print('RESPONSE:')
    print(rawheaders)
    print(rawhtml)

    return headers, rawhtml

# Performs a GET from the fakebook homepage to get a CSRF token
def getCSRFToken(s):
    message = 'GET http://' + base_url + '''/accounts/login/?next=/fakebook/ HTTP/1.1
Host: cs5700f18.ccs.neu.edu\r\n\r\n'''
    headers, rawhtml = getResponse(s, message)
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
    headers, rawhtml = getResponse(s, message)
    return getCookie(headers, 'sessionid')

# takes the socket, the csrftoken, and the sessionid of the logged-in user and 
# crawls Fakebook to find the secret flags
def crawl(s, csrftoken, sessionid):
    secretFlagList = []
    secretFlagTag = "<h2 class='secret_flag' style=\"color:red\">FLAG: "
    pagesToVisit = [base_url]
    startIndex = 0

    for url in pagesToVisit[startIndex:]:
        if len(secretFlagList) == 5:
            break
        try:
            print("Visiting: " + url)
            
            #TODO:
            #Connect to page and get raw html
            
            if secretFlagTag in rawhtml:
                secretFlagIndex = rawhtml.find(secretFlagTag)+len(secretFlagTag)
                secretFlag = rawhtml[secretFlagIndex:secretFlagIndex + 64]
                secretFlagList.append(secretFlag)

            # Adds links in current page to list of links to crawl through
            parser = LinkParser()
            linkList = parser.getLinks(rawhtml, url)
        except:
            print("**Failed!**")
        startIndex = startIndex + 1

    for flag in secretFlagList:
        print(flag)

# Gets links in raw html as list
class LinkParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    newUrl = self.baseUrl + value
                    if newUrl not in self.list:
                        self.list = self.list + [newUrl]
    
    def getLinks(self, html, baseUrl):
        self.list = []
        self.baseUrl = baseUrl
        self.feed(html) 

        print("LIST OF LINKS: ")
        print(self.list)
        print("")
        return self.list

################################################################################
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((base_url, DEFAULT_PORT))

# GET from login page to get csrf token
csrftoken = getCSRFToken(s)

# login and get sessionid
sessionid = login(s, username, password, csrftoken)
print(sessionid)

# Event loop
crawl(s, csrftoken, sessionid)





# RESOURCES!
# http://www.netinstructions.com/how-to-make-a-web-crawler-in-under-50-lines-of-python-code/
# ^ can't use urllib though