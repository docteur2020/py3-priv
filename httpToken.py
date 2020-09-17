#!/usr/bin/env python3.7
# coding: utf-8

import time
from sshtunnel import SSHTunnelForwarder
from json import loads as jloads
from json import dumps as jdumps
import requests
import argparse
import pdb
#import pickle
import dill as pickle
import dns.resolver
import ipaddress
import io
import os
import yaml



PAER="192.64.10.129"
LOCALHOST="127.0.0.1"
REMOTE_USER = 'x112097'
REMOTE_HOST =  PAER
REMOTE_PORT = 22
LOCAL_HOST =  LOCALHOST
LOCAL_PORT = 5000
SOCKS_PROXY_PORT=5000
KEY='/home/x112097/.ssh/id_rsa'
PATH_DB='/home/x112097/CONNEXION/dbREST'
MODEL_YAML='/home/x112097/yaml/http_model_api.yml'

MODEL=['APIC','CIMC','MSC']
AUTH_TYPE=['BEARER','COOKIE','XMLCOOKIE']


				
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
			args[0].api_url="https://"+str(LOCALHOST)+":"+str(new_port)+'/'
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
			args[0].cookie=Auth.getTokenXml()
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
		
	def getToken(self):
		
		s=requests.Session()
		self.session=s
		s.trust_env = False
		
		body={}
		body['username']="admin"
		body['password']="C1sc0-123"
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
		
		s.close()
		
		return self.Bearer
	
	def getTokenXml(self):
		
		s=requests.Session()
		self.session=s
		s.trust_env = False
		

		post_data = "<aaaLogin inName='admin' inPassword='C1sc0-123'></aaaLogin>"
		 
		try:            
			r=s.post('%s/nuova'%self.api_url,data=post_data,verify=False,proxies={})
			r.raise_for_status()
			data=r.text
			self.Token=r.attrib['outCookie']
			pdb.set_trace()
			# self.token=data['X-Auth-Token']
			# s.headers.update({'Content-Type':'application/json'})
			# self.Bearer=self.token
			print("Cocuoiu")
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
		
		
class HttpRestRequest(object):
	def __init__(self,hostname,action):
		self.hostname=hostname
		self.action=action
		self.cookie={}
		self.bearer=""
		self.ip=self.hostname.ip
		self.headers={'Content-Type':'application/json'}
		
	@authenticated
	@tunnelisation(LOCAL_PORT)	
	def launch(self):
	
		if self.hostname.authentication == "BEARER" or self.hostname.authentication == "COOKIE":
			try:
				url_action=RestModelsContainer().models[self.hostname.type].actions[self.action]
				url=self.api_url+url_action
			except KeyError as e:
				print("Erreur initialisation action")
				pdb.set_trace()
			
			s=requests.Session()
			try:
				r=s.get(url,cookies=self.cookie,headers=self.headers,verify=False)
				r.raise_for_status()
			except Exception as e:
				print(e)
				
			print(r.json())
		
		else:
			self.hostname.authentication == "BEARER"		
		return r.json()
		
		s.close()


class RestModel(object):
	def __init__(self,nom,actions,auth_mode):
		self.nom=nom
		self.actions=actions
		self.authentication=auth_mode
		
	def __str__(self):
		output=io.StringIO()
		output.write("nom:"+self.nom+",auth:"+self.authentication+'\n')
		for action in self.actions.keys():
			output.write(" -action:"+action+",url:"+self.actions[action]+'\n')
			
		return output.getvalue()
		
		output.close()
		
	def __repr__(self):
		output=io.StringIO()
		output.write("nom:"+self.nom+",auth:"+self.authentication)
		for action in self.actions.keys():
			output.write("action:"+action+",url:"+self.actions[action])
			
		return output.get_value()
		
		output.close()
		
	def add_action(self,alias,url):
		self.actions[alias]=url
		
		
class RestModelsContainer(object):
	def __init__(self,db=PATH_DB+'/models'):
		self.models={}
		self.db=db
		if os.path.exists(db):
			self.load(db)
		else:
			self.save(db)	
			
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		if os.path.getsize(filename) > 0:      
			with open(filename,'rb') as file__:
				try:
					dc=pickle.load(file__)
				except EOFError as e:
					print(e)
				except TypeError as e:
					print(e)
					
				self.models=dc.models

	
	def __contains__(self,model):
		resultat=True
		try:
			test=self.models[model.upper()]
		except:
			resultat=False
			
		return resultat
		
	def append(self,model):
					
		if model.nom not in self:	
			self.models[model.nom.upper()]=model
			self.save(self.db)
			
		else:
			print(model.nom+" va être ajouté/modifié")
			reponse=input("Etes-vous sûr de vouloir modifié le modèle "+model.nom+":y/n[n]")
			
			if reponse=='y':
				pass
				
			else:
				print("Aucune modification effectuée")
				
	def append_action(self,model,action,url):
					
		if model not in self:	
			self.models[model.upper()]=model
			self.save(self.db)
			
		else:
			print("Le modèle "+model+" va être modifié (ajout d'actions)")
			reponse=input("Etes-vous sûr de vouloir modifié le modèle "+model+":y/n[n]")
			
			if reponse=='y':
				try:
					self.models[model].add_action(action,url)
					self.save(self.db)
				except KeyError:
					print("Le modèle "+model+" n'existe pas")
				
			else:
				print("Aucune modification effectuée")
						
							
	def addModel(self,nom_model_ ):
		MODEL_=None
		TYPE_=None
		NOM_=nom_model_.upper()
		if nom_model_.upper() not in self:
			print(u"Le modèle "+nom_model_+u" n'est pas connu.")
		else:
			print(u"L'equipement "+nom_model_+u" est connu et va être modifier")
			
		
		while TYPE_ not in AUTH_TYPE:
			TYPE_=input("Quel est le type de connexion "+ "|".join(AUTH_TYPE)+":[COOKIE]")
			if not TYPE_:
				TYPE_="COOKIE"
			
		model_cur=RestModel(NOM_,{},TYPE_)
		self.append(model_cur)
		
		ACTION_YN=input("Voulez-vous ajouter des actions:(y/n)[y]")
		
		if not ACTION_YN:
			ACTION_YN='y'
			ACTION__TEST=True
		while ACTION__TEST:
			ALIAS_ACTION=None
			while not ALIAS_ACTION:
				ALIAS_ACTION=input("Alias de l'action:")
			URL_ACTION=None
			while not URL_ACTION:
				URL_ACTION=input("Url de l'action:")
			self.append_action(NOM_,ALIAS_ACTION,URL_ACTION)
			ACTION_YN=input("Voulez-vous ajouter des actions supplémentaires:(y/n)[n]")
			if not ACTION_YN or ACTION_YN!='y':
				ACTION_YN='n'
				ACTION__TEST=False
			else:
				ACTION__TEST=True
		
	def  __getitem__(self,key):
		try:
			return self.hosts[key]
		except KeyError:
			return None

	def affichage(self):
		
		for model__ in self.models:
			print(self.models[model__].__str__())
		
class Model(yaml.YAMLObject):
	yaml_tag= u'!MODEL'
	
	def __init__(self,name,action):
		self.name=name
		self.actions=actions
		
	def __repr__(self):
		return "name:%s\n actions:%s" % self.name,str(self.actions)
		
class RestHost(object):
	yaml_tag= u'!RESTHOST'
	
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
	def __init__(self,db):
		self.hosts={}
		self.hosts_alias={}
		self.db=db
		if os.path.exists(db):
			self.load(db)
		else:
			print("Fichier inexstant")
	
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		if os.path.getsize(filename) > 0:      
			with open(filename,'rb') as file__:
				try:
					dc=pickle.load(file__)
				except EOFError as e:
					print(e)
				except TypeError as e:
					print(e)
					
				self.hosts=dc.hosts
				self.hosts_alias=dc.hosts_alias
				self.db=dc.db

	
	def __contains__(self,nom_equipement):
		resultat=True
		try:
			test=self.hosts[nom_equipement.upper()]
		except:
			resultat=False
			
		return resultat
		
	def append(self,equipement_):
					
		if equipement_.hostname not in self:	
			self.hosts[equipement_.hostname.upper()]=equipement_
			self.hosts_alias[equipement_.alias.upper()]=equipement_
			self.save(self.db)

		else:
			print(equipement_.hostname+" va être modifié")
			reponse=input("Etes-vous sûr de vouloir modifié l'équipement "+equipement_.hostname+":y/n[n]")
			
			if reponse=='y':
				self.hosts[equipement_.hostname]=equipement_
				self.hosts_alias[equipement_.alias.upper()]=equipement_
				self.save(self.db)
				
			else:
				print("Aucune modification effectuée")
						
							
	def addHost(self,nom_equipement_ ):
		MODEL_=None
		TYPE_=None
		ALIAS_=None
		NOM_=nom_equipement_.upper()
		if nom_equipement_ not in self:
			print(u"L'équipement "+nom_equipement_+u" n'est pas connu.")
		else:
			print(u"L'equipement "+nom_equipement_+u" est connu et va être modifier")
		while MODEL_ not in MODEL:
			MODEL_=input("Quel est le type d'équipement "+"|".join(MODEL)+"[APIC]:")
			if not MODEL_:
				MODEL_="APIC"
		dns_requete=dns.query.udp(dns.message.make_query(nom_equipement_+'.dns63.socgen', dns.rdatatype.A, use_edns=0),'192.16.207.80')
		if dns_requete.rcode()==0:
			IP_DEFAULT=dns_requete.answer[0].__str__().split()[4]
		else:
			IP_DEFAULT=""
		test_format_IP=False
		#pdb.set_trace()
		while not test_format_IP:
			if IP_DEFAULT:
				IP_=input('Quel est l\'IP('+IP_DEFAULT+'):')
				if IP_=="":
					IP_=IP_DEFAULT
			else:
				IP_=input('Quel est l\'IP:')
			try:
				ipaddress.ip_address(IP_)
				test_format_IP=True
			except:
				pass
								
		while TYPE_ not in AUTH_TYPE:
			TYPE_=input("Quel est le type de connexion "+ "|".join(AUTH_TYPE)+":[COOKIE]")
			if not TYPE_:
				TYPE_="COOKIE"
				
		while not ALIAS_:
			ALIAS_=input("Quel est l'alias ["+nom_equipement_.upper()+"]:")
			if not ALIAS_:
				ALIAS_=nom_equipement_.upper()
			
		host_cur=RestHost(NOM_,ALIAS_,IP_,TYPE_,MODEL_)
		self.append(host_cur)
		
	def  __getitem__(self,key):
		try:
			return self.hosts[key]
		except KeyError:
			return None

	def affichage(self):
		
		for host__ in self.hosts:
			print(self.hosts[host__].__str__())
	
		

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-b", "--bastion",  action="store",default=REMOTE_HOST,help="Socks5 Server",required=False)
	parser.add_argument("-p", "--port",     action="store",default=REMOTE_PORT,help="Socks5 Server port",required=False)
	parser.add_argument("-L", "--localport",action="store",default=LOCAL_PORT, help=u"Proxy Server Port IP for localhost",required=False)
	parser.add_argument("-m", "--modify",action="store", help=u"ajoute ou modifie un équipement",required=False)
	parser.add_argument("-P", "--Print",action="store_true", help=u"affiche la db",required=False)
	group1.add_argument("-e", "--editdb",   action="store",help=u"db Rest Host",required=False)
	group1.add_argument("-M", "--Modeldb",  action="store",help=u"db Rest Model",required=False)
	group1.add_argument("-a", "--alias",  action="store",help=u"Alias",required=False)
	parser.add_argument("-A", "--Action",  action="store",help=u"Action à effectuer",required=False)
	
	args = parser.parse_args()
	
	with open(MODEL_YAML, 'r') as model_yml:
		other_model = yaml.load(model_yml,Loader=yaml.SafeLoader)
	
	print(other_model)

	if args.editdb:
		db__=RestHostsContainer(args.editdb)
		if args.modify:
			db__.addHost(args.modify)
			
		if args.Print:
			db__.affichage()
			
	if args.Modeldb:
		db__=RestModelsContainer(args.Modeldb)
		if args.modify:
			db__.addModel(args.modify)
			
		if args.Print:
			db__.affichage()
	
	if args.alias:
		db__cur=RestHostsContainer("/home/x112097/CONNEXION/dbREST/hosts")
		try:
			host_cur=db__cur.hosts_alias[args.alias]
			#Auth1=HttpAuth(host_cur.ip)
			#Auth1.getCookie()
			#Auth1.printCookie()
			
			if args.Action:
				RestReq=HttpRestRequest(host_cur,args.Action)
				RestReq.launch()
				
		except KeyError as e:
			print("Equipement inconnu")
			print(e)
			

			


