#!/usr/bin/env python3.7
# coding: utf-8

import time
from sshtunnel import SSHTunnelForwarder
from json import loads as jloads
from json import dumps as jdumps
import requests
import argparse
import pdb
import ipaddress
import io
import os
import ruamel.yaml as yaml
import warnings
from functools import wraps
import xmltodict
from collections import OrderedDict



HOST_YAML='/home/x112097/yaml/http_host_api.yml'
MODEL_YAML='/home/x112097/yaml/http_model_api.yml'

PAER="192.64.10.129"
LOCALHOST="127.0.0.1"
REMOTE_USER = 'x112097'
REMOTE_HOST =  PAER
REMOTE_PORT = 22
LOCAL_HOST =  LOCALHOST
LOCAL_PORT = 5000
SOCKS_PROXY_PORT=5000
KEY='/home/x112097/.ssh/id_rsa'



def ignore_warnings(f):
    @wraps(f)
    def inner(*args, **kwargs):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore")
            response = f(*args, **kwargs)
        return response
    return inner



@ignore_warnings
def init_yaml(fichier_yaml):
	resultat={}
	
	with open(fichier_yaml, 'r') as contenu_yml:
		resultat = yaml.load(contenu_yml)
	
	return resultat
	
def OrderedToDict(ordered_dict):
	resultat={}
	for dict_key in ordered_dict.keys():
		if isinstance(ordered_dict[dict_key],OrderedDict):
			element=OrderedToDict(ordered_dict[dict_key])
			
		elif isinstance(ordered_dict[dict_key],list):
			liste_cur=[]
			for element__ in ordered_dict[dict_key]:
				if isinstance(element__,OrderedDict):
					liste_cur.append(OrderedToDict(element__))
				else:
					liste_cur.append(element__)
			element=liste_cur
		else:
			element=ordered_dict[dict_key]
		resultat[dict_key]=element
		
	return resultat
	
def tunnelisation(new_port):
	def tunnelier(f):
		def tunnel_wrapper(*args,**kwargs):
			tunnel= SSHTunnelForwarder(
							(PAER, 22),
							ssh_username=REMOTE_USER,
							ssh_pkey=KEY,
							remote_bind_address=(args[0].ip, 443),
							local_bind_address=(LOCALHOST,new_port))
				
			tunnel.start()
			if f.__name__!='getDomain':
				args[0].api_url="https://"+str(LOCALHOST)+":"+str(new_port)+'/'
			else:
				args[0].api_domain_url="https://"+str(LOCALHOST)+":"+str(new_port)+'/'
			f(*args,**kwargs)
			time.sleep(2)
			tunnel.stop()
		return tunnel_wrapper
	return tunnelier
	
		
def authenticated(f):
	def auth_wrapper(*args,**kwargs):
		if args[0].hostname.authentication=='COOKIE':
			Auth=HttpAuth(args[0].hostname.ip)
			Auth.getCookie()
			args[0].cookie={'APIC-Cookie': Auth.Cookie}
			args[0].headers['APIC-challenge']=Auth.url_Cookie

		elif args[0].hostname.authentication=='BEARER':
			Auth=HttpAuth(args[0].hostname.ip)
			Auth.getToken()
			args[0].headers['authorization']='Bearer '+Auth.Bearer
			
		elif args[0].hostname.authentication=='XMLCOOKIE':
			Auth=HttpAuth(args[0].hostname.ip)
			Auth.getTokenXml()
			args[0].cookie=Auth.Token
		else:
			print("Mode d'authenfication non pris en compte")
			os.exit(2)
		f(*args,**kwargs)

	return auth_wrapper
					
class HttpAuth(object):
	def __init__(self,ip):
		self.ip=ip
		self.Bearer=None
		self.Cookie=None
		self.Token=None
		
	@tunnelisation(LOCAL_PORT)
	def getToken(self):
		
		s=requests.Session()
		self.session=s
		s.trust_env = False
		
		body={}
		body['username']="x112097"
		body['password']="Tek3pmac!"
		self.getDomain()
		body['domainId']=self.domainid
		
		try:            
			r=s.post('%sapi/v1/auth/login'%self.api_url,json=body,verify=False,proxies={})
			r.raise_for_status()
			data=jloads(r.text)
			self.token=data['token']
			s.headers.update({'Content-Type':'application/json'})
			self.Bearer=self.token
		except Exception as e:
			print(e)
			
		self.Bearer=self.token
		return self.Bearer
		
		s.close()
		
		
	
	@tunnelisation(LOCAL_PORT)
	def getTokenXml(self):
		
		s=requests.Session()
		self.session=s
		s.trust_env = False
		self.Token = None
		

		post_data = "<aaaLogin inName='admin' inPassword='C1sc0-123'></aaaLogin>"
		 
		try:            
			r=s.post('%snuova'%self.api_url,data=post_data,verify=False,proxies={})
			r.raise_for_status()
			data=r.text
			data_dict=xmltodict.parse(data)
			self.Token=data_dict['aaaLogin']['@outCookie']
			#print(str(data_dict))
			# self.token=data['X-Auth-Token']
			# s.headers.update({'Content-Type':'application/json'})
			# self.Bearer=self.token

		except Exception as e:
			print(e)
		
		s.close()
		
		return self.Token	
		
		
		
		
	def printBearer(self):
		if self.Bearer:
			print("Bearer:")
			print(self.Bearer)
		else:
			print('None')
			
	def printCookie(self):
	
		if self.Cookie:
			print("Cookie:")
			print(self.Cookie)
		else:
			print('None')
		
	@tunnelisation(LOCAL_PORT)
	def getCookie(self):
		body={}
		body['aaaUser']={}
		body['aaaUser']['attributes']={}
		attributes=body['aaaUser']['attributes']
		self.authdomain="TACACS"
		attributes['name']="x112097"
		attributes['pwd']="Tek3pmac!"
		
		s=requests.Session()
		self.session=s
		s.trust_env = False
		
		try:            
			r=s.post('%sapi/aaaLogin.json?gui-token-request=yes'%self.api_url,json=body,verify=False)
			r.raise_for_status()
		except Exception as e:
			print(e)
        
		data=jloads(r.text)
		
		#print(data)
		self.Cookie=data['imdata'][0]['aaaLogin']['attributes']['token']
		self.url_Cookie=data['imdata'][0]['aaaLogin']['attributes']['urlToken']
		s.headers.update({'Content-Type':'application/json'})
		s.close()
		
		return self.Cookie
	
	@tunnelisation(LOCAL_PORT+1)	
	def getDomain(self,method='tacacs'):
	
		domainid=""
		s=requests.Session()
		self.session=s
		s.trust_env = False
	
		try:
			r=s.get('%sapi/v1/auth/login-domains'%self.api_domain_url,verify=False)
			r.raise_for_status()
		except Exception as e:
			print(e)
			
		data=jloads(r.text)
		
		for domain__ in data['domains']:
			if domain__['realm']==method:
				domainid=domain__['id']
				self.domainid=domain__['id']
				
		s.close()	


		return domainid

class HttpRestRequest(object):
	def __init__(self,hostname=None,alias="RET-APC-DC2-2A1-0001",action="",models__=MODEL_YAML,hosts__=HOST_YAML):
		
		self.cookie={}
		self.bearer=""
		
		self.headers={'Content-Type':'application/json'}
		self.models__=RestModelsContainer(models__)
		self.hosts__=RestHostsContainer(hosts__)
	
		if hostname:
			self.hostname=hostname
		elif alias:
			self.hostname=self.hosts__.getHostFromAlias(alias)
		
		
		self.model=self.hostname.type
		self.action=self.models__.getFullAction(self.model,action)
		
		self.ip=self.hostname.ip

		
	@authenticated
	@tunnelisation(LOCAL_PORT)	
	def launch(self):
	
		if self.hostname.authentication == "BEARER" or self.hostname.authentication == "COOKIE":
			try:
				url_action=self.action['url']
				url=self.api_url+url_action
			except KeyError as e:
				print("Erreur initialisation action")
				pdb.set_trace()
			
			s=requests.Session()
			if self.action['method']=='GET':
				try:
					r=s.get(url,cookies=self.cookie,headers=self.headers,verify=False)
					r.raise_for_status()
				except Exception as e:
					print(e)
					
				print(r.json())
			elif self.action['method']=='POST':
				try:
					r=s.post(url,cookies=self.cookie,headers=self.headers,verify=False)
					r.raise_for_status()
				except Exception as e:
					print(e)
					
				print(r.json())
				
		elif self.hostname.authentication == 'XMLCOOKIE':
			try:
				data=self.action['data'].replace('<COOKIE>',self.cookie)
				url=self.api_url+"/nuova"
			except KeyError as e:
				print("Erreur initialisation action")
				
			s=requests.Session()
			if self.action['method']=='GET':
				try:
					r=s.get(url,data=data,verify=False)
					r.raise_for_status()
					data=r.text
					data_dict=xmltodict.parse(data)
					print(data_dict)
					self.logout()
				except Exception as e:
					print(e)
					
				print(r.json())
			elif self.action['method']=='POST':
				try:
					r=s.post(url,data=data,verify=False)
					r.raise_for_status()
					data=r.text
					data_dict=xmltodict.parse(data)
					print(str(OrderedToDict(data_dict)))
					self.logout()
				except ValueError as e:
					pdb.set_trace()
					print(e)
				except Exception as e:
					print(e)
					
		s.close()	
				
		
	
	def logout(self):
	
		if self.hostname.authentication == 'XMLCOOKIE':
			s=requests.Session()
			url=self.api_url+"/nuova"
			data="<aaaLogout cookie='%s' inCookie='%s'></aaaLogout>" % (self.cookie, self.cookie)
			r=s.post(url,data=data,verify=False)
		
		
class RestHost(yaml.YAMLObject):

	yaml_tag= u'!RestHost'
	
	
	def __init__(self,nom="Test",alias="Test",ip="0.0.0.0",auth_mode="BEARER",type="RIEN"):
		self.hostname=nom
		self.alias=alias
		self.ip=ip
		self.authentication=auth_mode
		self.type=type
		
	def __str__(self):

		return "hostname:"+self.hostname+",alias:"+self.alias+",ip:"+self.ip+",authentication:"+self.authentication+",type:"+self.type
		
	def __repr__(self):
		return "hostname:"+self.hostname+",alias:"+self.alias+",ip:"+self.ip+",authentication:"+self.authentication+",type:"+self.type
		
class RestHostsContainer(object):
	def __init__(self,hosts_yaml):
		self.hosts=init_yaml(hosts_yaml)
		
	def getHostFromAlias(self,alias):
		resultat=None
		for host__ in self.hosts['ALL']:
			if host__.alias==alias:
				resultat=host__
			
		return resultat
		
class RestModelsContainer(object):
	def __init__(self,models_yaml):
		self.hosts=init_yaml(models_yaml)
		
	def getFullAction(self,model,action):
		resultat=None
		
		try:
			resultat=self.hosts['Models'][model]['MODEL']['actions'][action]
		except KeyError:
			print("Action ou model inconnu")
			pass
			
		return resultat
		
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group_yaml=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument("-b", "--bastion",  action="store",default=REMOTE_HOST,help="Ssh Server",required=False)
	parser.add_argument("-p", "--port",     action="store",default=REMOTE_PORT,help="Ssh Server port",required=False)
	parser.add_argument("-L", "--localport",action="store",default=LOCAL_PORT, help=u"Proxy Server Port IP for localhost",required=False)
	parser.add_argument("-P", "--Print",action="store_true", help=u"affiche les hosts ou les modèles ",required=False)
	parser.add_argument("-a", "--alias",  action="store",help=u"Alias",required=False)
	group_yaml.add_argument("-H", "--Hosts",   action="store",default=HOST_YAML  ,help=u"fichier yaml hosts par défaut",required=False)
	group_yaml.add_argument("-M", "--Models",  action="store",default=MODEL_YAML,help=u"fichier yaml models par défaut",required=False)
	parser.add_argument("-A", "--Action",  action="store",help=u"Action à effectuer",required=False)
	
	args = parser.parse_args()
	
	if args.alias and args.Action:
		Req=HttpRestRequest(alias=args.alias,action=args.Action)
		Req.launch()
	



