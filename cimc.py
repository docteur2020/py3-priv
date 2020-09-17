#########################################
#### Base classes and functions 
########################################

__all__=['AciObject','AciController','dmoJson']

from ..dmoBase.decorators import authenticated
import requests
import ipaddress
from  json import loads as jloads
from json import dumps as jdumps
from json.decoder import JSONDecodeError
from ..dmoBase.dmoErrors import *
from collections import UserDict
from pathlib import Path
import re
import urllib.parse
from contextlib import ContextDecorator
import xml.etree.ElementTree as ET
import sys

import logging
try:
    from logging.handlers import NullHandler
except:
    class NullHandler(logging.Handler):
        def emit(self,record): pass




            
class CimcServer():
    ''' Base Class to be used to construct Msc or Apic objects
    '''
    def __init__(self,ip,**kwargs):
        #super().__init__(**kwargs)
        try:
            self.ip=ip
        except:
            raise dmoError("IP Must be specified")
        self.name=kwargs.get("name",None)
        self.log=kwargs.get('log',None)

   
        self.version=None
        self.state=None
        self.port=443
        self.protocol="https"
        self.token=None
        self.user=kwargs.get('user',None)
        self.password=kwargs.get('password',None)
        self.session=None
        self.api_path=kwargs.get('api_path','/nuova')
        if self.protocol.lower()=='https' and str(self.port)=='443':
            self.api_url='%s://%s%s'%(self.protocol,self.ip,self.api_path)
        else:
            self.api_url='%s://%s:%s%s'%(self.protocol,self.ip,self.port,self.api_path)

        self.verify=kwargs.get('verify',True)
        try:
           self.log.debug("api_url=%s"%self.api_url)
        except:
            pass

        
    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_val,exc_tb):
        if exc_type:
            print("Interruption %s ==> %s"%(exc_type,exc_val),file=sys.stderr)
        if self.token is not None:
            self.logout()

        

    def login(self):
        self.connect()



    @authenticated
    def upgrade_all(self,timeout=90,remote_ip=None,remote_path=None,map_type='www',remote_user=None,remote_password=None):
        log=self.log
        body='''<configConfMo cookie="%s"   inHierarchical="true" dn='sys/huu/firmwareUpdater'> <inConfig>  <huuFirmwareUpdater dn='sys/huu/firmwareUpdater'  adminState='trigger' remoteIp='%s' remoteShare='%s'  mapType='%s' username='%s' password='%s' stopOnError='yes' timeOut='%s' verifyUpdate='yes' updateComponent='all' />  </inConfig> </configConfMo>'''%(self.token,remote_ip,remote_path,map_type,remote_user,remote_password,timeout)

        

        log.debug('upgrade_all body: %s'%body)
            
        r=self.post('',data=body)
        log.debug("upgrade_all. Result=%s"%r.content)
        
        try:
            root=ET.fromstring(r.text)
        except Exception as e:
            log.debug("root attrib: %s"%root.attrib)
            log.debug("login: response: %s"%r.content)
            log.err("Erreur dans xml: %s"%e)
       
        try:
            result_xml=root.find('./outConfig/huuFirmwareUpdater/huuFirmwareUpdateStatus')
        except Exception as e:
            raise dmoError("Cannot access ./outConfigs/huuFirmwareUpdater/huuFirmwareUpdateStatus xml subelement")

        
        result=result_xml.get('overallStatus')
        return result


    @authenticated
    def show_upgrade(self):
        log=self.log
        body='''<configResolveClass cookie="%s" inHierarchical="true" classId="huuFirmwareUpdater"/>'''%self.token
        
        log.debug('show_upgrade body: %s'%body)

            
        r=self.post('',data=body)

        log.debug("show_upgrade: %s"%r.content)
        
        try:
            root=ET.fromstring(r.text)
        except Exception as e:
            log.debug("root attrib: %s"%root.attrib)
            log.debug("login: response: %s"%r.content)
            log.err("Erreur dans xml: %s"%e)
       
        try:
            result_xml=root.find('./outConfigs/huuFirmwareUpdater/huuFirmwareUpdateStatus')

        except Exception as e:
            raise dmoError("Cannot access ./outConfigs/huuFirmwareUpdater xml subelement")


        try:
            components_xml=root.findall('./outConfigs/huuFirmwareUpdater/huuFirmwareUpdateStatus/huuUpdateComponentStatus')
        except:
            components_xml=[]

        
        result_overall=result_xml.get('overallStatus')
  
        return (result_overall,components_xml)



    @authenticated
    def get_version(self):
        if self.version is None:
            raise dmoValueError("Cannot find version")
        return self.version

    def logout(self):
        if self.token is None:
            return


        log=self.log
        log.debug("Logout: %s"%self.ip)

        body='<aaaLogout inCookie="%s" />'%(self.token)
        s=self.session

        try:            
            r=s.post(self.api_url,data=body)
            log.debug("Headers request: %s"%s.headers)
            r.raise_for_status()
            log.debug("Headers: %s"%r.headers)
            log.debug("Response: %s"%r.text)
            
        except Exception as e:
            log.debug("Headers: %s"%r.headers)
            log.debug("Response: %s"%r.text)
            raise dmoError("Cannot Logout") from e





    def connect(self):
        log=self.log
        if self.token is not None:
            return

 
        if self.session is None:
            s=requests.Session()
            self.session=s
            s.verify=self.verify
            s.headers.update({'Content-Type':'application/x-www-form-urlencoded'})
            #s.headers.update({'Content-Type':'application/xml'})
        #log.debug("connect: data=%s"%body)

        body='<aaaLogin inName="%s" inPassword="%s" />'%(self.user,self.password)


        try:            
            r=s.post(self.api_url,data=body)
            log.debug("Headers request: %s"%s.headers)
            r.raise_for_status()
            log.debug("Headers: %s"%r.headers)
            log.debug("Response: %s"%r.text)
            
        except Exception as e:
            log.debug("Headers: %s"%r.headers)
            log.debug("Response: %s"%r.text)
            raise dmoError("Cannot connect") from e
        
        try:
            root=ET.fromstring(r.text)
        except Exception as e:
            log.debug("root attrib: %s"%root.attrib)
            log.debug("login: response: %s"%r.content)
            log.err("Erreur dans xml: %s"%e)


        log.debug("root attr:%s"%root.attrib)
        self.token=root.get('outCookie')

        if not self.token:
            raise dmoError("Cannot log to %s"%self.ip)
        self.version=root.get('outVersion')
        


    @authenticated
    def get(self,url_end,binary=False,**kwargs):
        url=self.api_url+url_end
        s=self.session
        try:
            r=s.get(url,**kwargs)
            r.raise_for_status()
        except Exception as e:
            raise dmoError("Cannot do get...") from e

        return r.text

    @authenticated
    def post(self,url_end,data='',binary=False):
        log=self.log
        url=self.api_url+url_end
        log.debug("Post: %s"%url)
        s=self.session
        try:
            r=s.post(url,data=data)
            r.raise_for_status()
        except Exception as e:
            raise dmoError("Cannot do post...") from e

        return r
    
    @authenticated
    def delete(self,url_end):
        url=self.api_url+url_end
        s=self.session
        try:
            r=s.delete(url)
            r.raise_for_status()
        except Exception as e:
            raise dmoError("Cannot do delete... r:'%s'"%r.text) from e
        
        try:
            encoded=r.json()
        except JSONDecodeError:
            encoded={}
            
        return encoded

    @authenticated
    def put(self,url_end,data='',binary=False):
        log=self.log
        url=self.api_url+url_end
        s=self.session
        try:
            r=s.put(url,json=data)
            r.raise_for_status()
        except Exception as e:
            raise dmoError("Cannot do put...: '%s' '%s'"%(e,r.text)) from e

        if not binary:
            return r.json()
        else:
            return r.content
        



