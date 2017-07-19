#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于进行http请求，以及MD5加密，生成签名的工具类
import http.client
import requests
import urllib
import hashlib
import time

def buildMySign(params,secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) +'&'
    data = sign+'secret_key='+secretKey
    return  hashlib.md5(data.encode("utf8")).hexdigest().upper()

def httpGet(url,resource,params=''):
    response = requests.get(url + resource, params=params, timeout=10)
    return response.json()

def httpPost(url,resource,params):
    headers = {
           "Content-type" : "application/x-www-form-urlencoded",
    }
    temp_params = urllib.parse.urlencode(params)
    response = requests.post(url + resource, data=temp_params, timeout=10, headers=headers)
    return response.json()
