#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) Feather Workshop 2012
#
# Author:     Feather.et.ELF <fledna@qq.com>
#             smallevilbeast <houshao55@gmail.com>
#
# Maintainer: Feather.et.ELF <fledna@qq.com>
#             smallevilbeast <houshao55@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import urllib
import urllib2
import httplib
import urlparse
import re
import cookielib
import time
import random
import string
import cgi


try:
    import simplejson as json
except ImportError:    
    import json
    
import socket    
socket.setdefaulttimeout(40) # 40s

from logger import Logger
from xdg_support import get_cache_file

def timestamp():
    return int(time.time() * 1000)

def radix(n, base=36):
    digits = string.digits + string.lowercase
    def shortDiv(n, acc=list()):
        q, r = divmod(n, base)
        return [r] + acc if q == 0 else shortDiv(q, [r] + acc)
    return ''.join(digits[i] for i in shortDiv(n))

def timechecksum():
    return radix(timestamp())

__cookies__ = get_cache_file("cookie.txt")

class HiLib(Logger):
    def __init__(self, username, password):
        
        self.username = username.decode("utf-8").encode("gbk")
        self.password = password
        
        # 保存cookie
        cj = cookielib.LWPCookieJar(__cookies__)
        cookie_handler = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_handler)
        
        opener.addheaders = [
            ('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.24 ' \
             '(KHTML, like Gecko) Chrome/19.0.1056.0 Safari/535.24'),]
        
        self.cookiejar = cj
        self.opener = opener
        self.__seq = 0 
        self.apidata = dict()
        self.__pickack = ""
        self.last_message_timestamp = 0
        
        self.group_infos = []
        self.multi_team_info = []
        self.block_list = []
        self.old_system = []
        self.old_message = []
        self.old_notify = []
        self.old_notify = []
        self.system_message = []
        self.old_group_message = []
        
    @property    
    def seq(self):    
        ret = self.__seq
        self.__seq += 1
        return ret
    
    @seq.setter
    def seq(self, value):
        self.__seq = value
        
    def login(self, stage=0):
        self.apidata = dict()
        req = urllib2.Request("http://web.im.baidu.com/")
        ret = self.opener.open(req)
        ret.read() # Fix
        ret = self.api_request("check", v=30, time=timechecksum())        
        self.logdebug("Login check return value: %s", ret)
        
        # 登陆校验成功.
        if ret["result"] == "ok":
            self.cookiejar.save()
            self.loginfo("Login check success!")
            return True
        
        # 登陆校验失败(超过两次登陆校验)
        elif stage >= 2:
            self.loginfo("Login check failed!")
            return False
        assert ret['result'] == 'offline'
        req = urllib2.Request('http://passport.baidu.com/api/?login&tpl=mn&time=%d' % timestamp())
        data = self.opener.open(req).read().strip()[1:-1] # remove brackets
        data = eval(data, type('Dummy', (dict,), dict(__getitem__=lambda s,n:n))())
        if int(data["error_no"]) != 0:
            self.logdebug("Login passport error: %s", data)
            return False
        param_out = data["param_out"]
        param_in = data["param_in"]
        params = {v : param_out[k.replace("name", "contex")] for k, v in param_out.items() if k.endswith("_name")}
        params.update({v: param_in[k.replace("name", "value")] for k,v in param_in.items() if k.endswith("_name")})
        
        params["username"] = self.username
        params["password"] = self.password
        params["safeflg"]  = ""
        params["mem_pass"] = "on"
        if int(params["verifycode"]) == 1 and stage == 1:
            self.loginfo("Login check require verifycode")
            params["verifycode"] = self.get_verify_code()
            
        params['staticpage'] = 'http://web.im.baidu.com/popup/src/login_jump.htm'
        self.logdebug("After filing params: %s", params)

        req = urllib2.Request('https://passport.baidu.com/api/?login',
                              data=urllib.urlencode(params))
        html = self.opener.open(req).read()
        url = re.findall(r"encodeURI\('(.*?)'\)", html)[0]
        self.opener.open(url).read()
        
        # 二次登陆校验
        if stage == 0:
            self.loginfo("Begin second login check..")
        elif stage == 1:    
            self.loginfo("Begin three login check..")
        return self.login(stage=stage+1)
    
    def init(self):
        
        # 登陆后初始化.
        self.seq = 0
        guid = timechecksum()
        
        # API请求公用数据
        self.apidata = dict(v=30, session="", source=22, guid=guid,
                            seq=lambda : self.seq)
        
        # 开始登陆过程
        self.api_request("welcome", method="POST", extra_data={"from" : 0},
                         seq=self.seq, force="true")
        ret = self.api_request("init", method="POST", status="online")
        
        if ret["result"] == "ok":
            self.loginfo("Login ok: username=%s, nick=%s", ret["content"]["username"],
                         ret["content"]["nickname"])
            
        # 第一次 pick 自己是否登陆成功,  ack = 0
        self.pick()    
        
        # 获取分组信息
        self.get_multi_team_info() 
        self.logdebug("Team infos: %s", self.multi_team_info)
        
        # 获取阻止联系人信息
        self.get_block_list()
        self.logdebug("Block list: %s", self.block_list)
        
        # 获取离线系统信息
        self.get_old_system()
        self.logdebug("Old system: %s", self.old_system)
        
        # 获取离线消息
        self.get_old_message()
        self.logdebug("Old message: %s", self.old_message)
        
        # 获取离线通知信息
        self.get_old_notify()
        self.logdebug("Old notify: %s", self.old_notify)
        
        # 获取系统信息 
        self.get_system_message()
        
        # 获取离线群信息
        self.get_old_group_message()
        self.logdebug("Old group message: %s", self.old_group_message)
        
        return True
        
    def get_multi_team_info(self):
        ret = self.api_request("getmultiteaminfo")
        if ret["result"] == "ok":
            self.multi_team_info = ret["content"]["fields"]
            
    def get_block_list(self):        
        ret = self.api_request("blocklist", page=0)
        if ret["result"] == "ok":
            self.block_list = ret["content"]["fields"]
            
    def get_old_system(self):        
        ret = self.api_request('oldsystem', lastMessageId=0, lastMessageTime=0)
        if ret["result"] == "ok":
            self.old_system = ret["content"]["fields"]
            
    def get_old_message(self):        
        ret = self.api_request('oldmessage', lastMessageId=0, lastMessageTime=0)
        if ret["result"] == "ok":
            self.old_message = ret["content"]["fields"]
        
    def get_old_notify(self):        
        ret = self.api_request('oldmessage', lastMessageId=0, lastMessageTime=0)
        if ret["result"] == "ok":
            self.old_notify = ret["content"]["fields"]
            
    def get_system_message(self):        
        self.api_request("getsystemmessage")
        
    def get_old_group_message(self):    
        ret = self.api_request("oldgroupmessage", lastGid=0, lastMessageId=0, lastMessageTime=0)
        if ret["result"] == "ok":
            self.old_group_message = ret["content"]["fields"]
        
    def pick(self):    
        ''' main callable func.'''
        ret = self.api_request("pick", type=23, flag=1, ack=self.__pickack)
        if ret["result"] != "ok":
            if ret["result"] == "kicked":
                self.logerror("Kicked by system!")
            elif ret["result"] == "networkerror":
                self.log.fatal("Network error!")
            else:    
                self.logerror("Pick error: %s", ret)
        if ret["content"]:
            self.__pickack = ret["content"]["ack"]
            for field in ret["content"]["fields"]:
                self.handle_pick_field(field)
                
    def handle_pick_field(self, field):            
        pass
        
    def get_verify_code(self):
        url = 'https://passport.baidu.com/?verifypic&t=%d' % timestamp()
        req = urllib2.Request(url)
        data = self.opener.open(req).read()
        pic_image = get_cache_file("pic.jpg")
        with open(pic_image, "wb") as fp:
            fp.write(data)
        if os.path.exists(pic_image):    
            return pic_image
        else:
            return None
        
    def query_info(self, username):    
        ret = self.api_request("queryinfo", username=username,
                               field="relationship,username,showname,showtype,status")
        if ret["result"] == "ok":
            return ret["content"]["fields"]
        return None
    
    def verify_code(self, type, **params):
        ret = self.api_request("verifycode", type=type, **params)
        vdata = ret["content"]["validate"]
        
        if vdata.get("v_code", None):
            return ",".join([vdata['v_url'], vdata['v_period'], vdata['v_time'], vdata['v_code']])
        else:
            self.logerror('Verifycode not implemented! type=%s, args=%s', type, params)
            return None
        
        image_url = 'http://vcode.im.baidu.com/cgi-bin/genimg?%s&_time=%s' % (vdata["v_url"], timechecksum())
        data = self._opener.open(image_url).read()
        pic_image = get_cache_file("pic.jpg")
        with open(pic_image, 'wb') as fp:
            fp.write(data)
            self.loginfo('Verify code pic download ok!')
        code = 'abcd'
        return ','.join([vdata['v_url'], vdata['v_period'], vdata['v_time'], code])
    
    def add_friend(self, username, tid=0, comment=u""):
        if not isinstance(comment, unicode): comment = unicode(comment, "utf-8")
        users = self.query_info(username)
        if users in None:
            self.logerror("Add friend <uid:%s> failed: aquire userinfo fail", username)
            return False
        # info = users[0]
        #if info['relationship'] != 2:
        #    self.logerror('Add friend <uid:%s> failed: relationship != 2', username)
        #    return False
        validate = self.verify_code(type="addfriend", username=username)
        ret = self.api_request("addfriend",  username=username, tid=tid, comment=comment, validate=validate)
        
        if ret["result"] == "ok":
            return True
        else:
            self.logerror('Add friend <uid:%s> failed: %s', username, ret)
        return False
    
    def delete_friend(self, username):
        validate = self.verifycode(type='deletefriend', username=username)
        ret = self.api_reqest('deletefriend', username=username, validate=validate)
        if ret['result'] == 'ok':
            return True
        else:
            self.logerror('Delete friend <uid:%s> failed: %s', username, ret)
        return False
    
        
    def api_request(self, api, method="GET", extra_data=dict(), retry_limit=2, **params):    
        url = urlparse.urljoin("http://web.im.baidu.com/", api)
        data = self.apidata.copy()
        data.update(extra_data)
        data.update(params)
        for key in data:
            if callable(data[key]):
                data[key] = data[key]()
            if isinstance(data[key], (list, tuple, set)):
                data[key] = ",".join(map(str, list(data[key])))
            if isinstance(data[key], unicode):    
                data[key] = data[key].encode("utf-8")
                
        if method == "GET":        
            query = urllib.urlencode(data)
            url = "%s?%s" % (url, query)
            req = urllib2.Request(url)
        elif method == "POST":
            body = urllib.urlencode(data)
            req = urllib2.Request(url, data=body)
            
        self.logdebug("API request url: %s", url)    
        start = time.time()    
        try:
            ret = self.opener.open(req)
        except Exception, e:    
            if retry_limit == 0:
                self.logdebug("API request error: url=%s error=%s",  url, e)
                return dict(result="network_error")
            else:
                retry_limit -= 1
                return self.api_request(api, method, extra_data, retry_limit, **params)
        raw = ret.read()
        try:
            data = json.loads(raw)
        except:    
            data = eval(raw, type("Dummy", (dict,), dict(__getitem__=lambda s,n: n))())
        self.logdebug("API response %s: %s TT=%.3fs", api, data, time.time() - start )
        return data

if __name__ == "__main__":    
    hi_lib = HiLib(sys.argv[1], sys.argv[2])
    if hi_lib.login():
        hi_lib.init()
