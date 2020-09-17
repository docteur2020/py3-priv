#!/bin/python3.7
# coding: utf-8

import sys
import argparse
import pdb
sys.path.insert(0,'/home/x112097/py/dmo')
import dmoPy3.aci.msc as msc
import dmoPy3.aci.socgenbase as socgenbase
import yaml
import os
from time import gmtime, strftime , localtime
from getHosts import *
from Tunnelier import Tunnelier

from acitoolkit.acitoolkit import Session
from acitoolkit.aciphysobject import Node
from acitoolkit.acitoolkit import *
import pwd 
from getsec import *
import json
from pprint import pprint as ppr
import cache as cc

TSK="/home/x112097/CONNEXION/pass.db"
SAVEJSON="/home/x112097/json/bck"

class Loader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f)

Loader.add_constructor('!include', Loader.include)

def initCred():
	username=pwd.getpwuid(os.getuid()).pw_name
	tsk=secSbe(TSK)
	return {'username':username,'passwd':tsk.tac}
	
def getNode(apcs):
	resultat={}
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	session = Session(newUrl, Cred['username'], Cred['passwd'])
	resp = session.login()
	
	
	if not resp.ok:
		print('%% Could not login to APIC',file=sys.stderr)
		sys.exit(1)

	phy_class = Node

	items = phy_class.get(session)
	for item in items:
		resultat[item.node]={'name':item.name,'info':item.info()}
	
	tunnel.stop()
	
	return resultat
	
def append_dict(dict__,key1,key2,value):
	if key1 in dict__.keys():
		if key2 in dict__[key1].keys():
			dict__[key1][key2].append(value)
			
		else:
			dict__[key1][key2]=[value]
	else:
		dict__[key1]={key2:value}
			
	

def getIp(apcs,options={}):
	resultat_list=[]
	resultat_dict={}
	data={}
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	configYaml=getInfoYamlFabric(options.fabric)
	auth=getAuth(configYaml,options.site)
	username=Cred['username']
	if auth:
		username='apic:'+auth+'\\'+username
	session = Session(newUrl, username, Cred['passwd'])
	
	resp = session.login()
	
	if not resp.ok:
		print('%% Could not login to APIC',file=sys.stderr)
		sys.exit(1)
		
	resp = session.get('/api/class/ipv4Addr.json')
	intfs = json.loads(resp.text)['imdata']
	

	for i in intfs:
		ip = i['ipv4Addr']['attributes']['addr']
		op = i['ipv4Addr']['attributes']['operSt']
		cfg = i['ipv4Addr']['attributes']['operStQual']
		dn = i['ipv4Addr']['attributes']['dn']
		node = dn.split('/')[2].replace('node-','')
		intf = re.split(r'\[|\]', dn)[1]
		vrf = re.split(r'/|dom-', dn)[7]
		tn = vrf
		if vrf.find(":") != -1:
			tn = re.search("(.*):(.*)", vrf).group(1)
		
		
		append_dict(resultat_dict,node,intf,{'ip':ip,'vrf':vrf,'CurrentStat':op , 'AdminState':cfg})
		resultat_list.append({'node':node,'if':intf,'ip':ip,'vrf':vrf,'CurrentStat':op , 'AdminState':cfg})
	
	tunnel.stop()
	
	return (resultat_dict,resultat_list)
	
	
def getAuth(configYaml,site):
	try:
	
		for site__ in configYaml['sites']:
			if site==site__['name']:
				return site__['authdomain']
	except KeyError:
		pass
		
	except TypeError as e:
		pdb.set_trace()
		print(e)

def getTenant(apcs,options={}):
	resultat={}
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	configYaml=getInfoYamlFabric(options.fabric)
	auth=getAuth(configYaml,options.site)
	username=Cred['username']
	if auth:
		username='apic:'+auth+'\\'+username
	session = Session(newUrl, username, Cred['passwd'])
	resp = session.login()
	
	
	if not resp.ok:
		print('%% Could not login to APIC',file=sys.stderr)
		sys.exit(1)

	tenants = Tenant.get(session)
	
	if options.gettenant:
		for tenant in tenants:
			print(tenant.name)
	
	if options.savejson:
		
		suffixe_time=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		tenants_deep=Tenant.get_deep(session,config_only=True)
		for tenant__ in tenants_deep :
			filesave=SAVEJSON+'/tenants/'+options.fabric+'_'+options.site+'_'+tenant__.name+suffixe_time+".json"
			with open(filesave, 'w') as jsonfile_w:
				jsonfile_w.write(json.dumps(tenant__.get_json(), indent=4, sort_keys=True))


	tunnel.stop()
	
	return tenants
	
def getFabric(apcs,options={}):
	resultat={}
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	session = Session(newUrl, Cred['username'], Cred['passwd'])
	resp = session.login()
	
	
	if not resp.ok:
		print('%% Could not login to APIC',file=sys.stderr)
		sys.exit(1)
	
	
	pdb.set_trace()
	
	fabric=Fabric()
	epg=EPG('toto','toto')
	
	tunnel.stop()

def getTenantFromName(tenants,name):
	resultat=None
	for t in tenants:
		if t.name==name:
			resultat=t
			break
		
	return resultat
		
	
def get_epg(apcs,tenant_name="",options={}):
	
	resultat=[]
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	config_file=socgenbase.get_conf_filename(options.fabric)
	session = Session(newUrl, Cred['username'], Cred['passwd'])
	resp = session.login()
	
	tenants = Tenant.get(session)
	if tenant_name:
		tenant=getTenantFromName(tenants,tenant_name)
		apps = AppProfile.get(session, tenant)
		for app in apps:
			epgs = EPG.get(session, app, tenant)
			for epg in epgs:
				pdb.set_trace()
				resultat.append([tenant.name, app.name, epg.name,epg.name.replace('VLAN_','').replace('_EPG','')])
	else:
		for tenant in tenants:
			apps = AppProfile.get(session, tenant)
			for app in apps:
				epgs = EPG.get(session, app, tenant)
				for epg in epgs:
					pdb.set_trace()
					resultat.append([tenant.name, app.name, epg.name,epg.name.replace('VLAN_','').replace('_EPG','')])
				
	tunnel.stop()
	
	
	if options.save:
		TAG=options.fabric.upper()+'_'+options.site.upper()+'_EPGS'
		cc.Cache(TAG,initValue=resultat)
		
	return resultat
	
def getInfoYamlFabric(File__):
	
	try:
		config_file=socgenbase.get_conf_filename(File__)
		with open(config_file,'r') as file:
			config_yaml=yaml.load(file,Loader)
	except :
		print("Fabric '%s' is unknown"%fabric,file=sys.stderr)
		print("Known fabrics: '%s'")
		for (name,conf) in socgenbase.hash_of_conf_files.items():
			print(" - %s (conf file: %s)"%(name,conf),file=sys.stderr)
		print()
		print("Please edit 'hash_of_conf_file' in 'dmoPy3/aci/socgenbase.py' file to add new fabrics")
		sys.exit(1)
	
	
	return config_yaml
	
	
	
	
	
	
	
	
	
def get_epgs_node(apcs,options={}):
	resultat=[]
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	apic = Session(newUrl, Cred['username'], Cred['passwd'])

	if not apic.login().ok:
		print('%% Could not login to APIC',file=sys.stderr)
		sys.exit(1)
		
	query_url = ('/api/node/class/fvIfConn.json?n%s.json')
	resp=apic.get(query_url)	

	if not resp.ok:
		print('Could not collect APIC data for switch %s.',file=sys.stderr)
		sys.exit(1)
		
	tunnel.stop()
	
	epgs_cur=[]
	
	for data in resp.json()['imdata']:
		try:
			epgs_cur.append(parsingDnInt(data['fvIfConn']['attributes']['dn']))
		except pp.ParseException as e:
			print('Error Parsing:',data['fvIfConn']['attributes']['dn'],e,file=sys.stderr)
		
		
	resultats= setIfEgp(epgs_cur)
	
	if options.save:
		TAG=options.fabric.upper()+'_'+options.site.upper()+'_STATIC_EPG'
		cc.Cache(TAG,initValue=resultats)
		
	return resultats
	
def get_epg_node(apcs,node,interface,options={}):
	resultat=[]
	Cred=initCred()
	url="https://"+apcs[0]
	tunnel=Tunnelier()
	newUrl=tunnel.addUrl(url)
	apic = Session(newUrl, Cred['username'], Cred['passwd'])

	if not apic.login().ok:
		print('%% Could not login to APIC',file=sys.stderr)
		sys.exit(1)
		
	query_url = ('/api/node/class/fvIfConn.json?n%s.json')
	resp=apic.get(query_url)	

	if not resp.ok:
		print('Could not collect APIC data for switch %s.',file=sys.stderr)
		sys.exit(1)
		
	tunnel.stop()
	
	epgs_cur=[]
	
	for data in resp.json()['imdata']:
		try:
			epgs_cur.append(parsingDnInt(data['fvIfConn']['attributes']['dn']))
		except pp.ParseException as e:
			print('Error Parsing:',data['fvIfConn']['attributes']['dn'],e,file=sys.stderr)
		
		
	resultats= setIfEgp(epgs_cur)
	
	try:
		resultat=resultats[node][interface]
	except KeyError:
		print('No EPG on this interface')
	return resultat

def parsingDnInt(String):
	Slash=pp.Suppress(pp.Literal('/'))
	VlanId=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 0 )
	Net=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	ipAddressNet=pp.Combine(ipAddress+pp.Literal('/')+Net)
	Tenant=(pp.Suppress(pp.Literal('tn-'))+pp.Word(pp.alphanums+'_-')).setResultsName('tenant')
	Epg=(pp.Suppress(pp.Literal('epg-'))+pp.Word(pp.alphanums+'_-')).setResultsName('epg')
	Node=(pp.Suppress(pp.Literal('node-'))+pp.Word(pp.alphanums+'_-')).setResultsName('node')
	L3out=(pp.Suppress(pp.Literal('out-'))+pp.Word(pp.alphanums+'_-/')).setResultsName('l3out')
	Mgmt=(pp.Suppress(pp.Literal('mgmtp-default/'))+pp.Word(pp.alphanums+'_-')).setResultsName('mgmt')
	Interface=(pp.Suppress(pp.Literal('stpathatt-'))+pp.Suppress(pp.Literal('['))+pp.Word(pp.alphanums+'_-/')+pp.Suppress(pp.Literal(']'))).setResultsName('if')
	Vlan=(pp.Suppress(pp.Literal('conndef/conn-'))+((pp.Suppress('[vlan-')+VlanId)|(pp.Suppress('[')+pp.Literal('unknown')))+pp.Suppress(']-')).setResultsName('vlanid')
	IP=(pp.Suppress(pp.Literal('['))+pp.MatchFirst([ipAddressNet,ipAddress])+pp.Suppress(']')).setResultsName('ip')
	Ap=(pp.Suppress(pp.Literal('ap-'))+pp.Word(pp.alphanums+'_-')).setResultsName('ap')
	path_prefix=pp.Suppress(pp.Word(pp.alphas+'/-')+pp.Literal('[uni'))
	l2dn=path_prefix+Slash+Tenant+Slash+((Ap+Slash+Epg)|L3out|Mgmt)+pp.Suppress(pp.Literal(']'))+Slash+Node+Slash+pp.Optional(Interface+Slash)+Vlan+IP
	
	resultat=l2dn.parseString(String).asDict()

	
	return resultat
	

def setIfEgp(dataIf):
	resultat={}
	for if__ in dataIf:
		keys__=list(if__.keys())
		tmp_if=if__.copy()
		
		if	'if' in keys__ and 'node' in keys__:
			if 'epg' in keys__:
				if_cur=if__['if'][0]
				node_cur=if__['node'][0]
				del(tmp_if['if'])
				del(tmp_if['node'])
				if node_cur in resultat.keys():
					if if_cur in  resultat[node_cur]:
						resultat[node_cur][if_cur].append(tmp_if)
					else:
						resultat[node_cur][if_cur]=[tmp_if]
				else:
					resultat[node_cur]={if_cur:[tmp_if]}
					
	return resultat
					
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('-f','--fabric',help='fabric')
	parser.add_argument('--list-site',dest="list_site",action="store_true",help='display sites')
	parser.add_argument('-s','--site',action="store",help='display site info')
	parser.add_argument('--info-cimc',dest="cimc",action="store_true",help='display CIMC info')
	parser.add_argument('--get-node',dest="getnode",action="store_true",help='display Node')
	parser.add_argument('--get-ip',dest="getip",action="store_true",help='display IP')
	parser.add_argument('--get-tenant',dest="gettenant",action="store_true",help='display Tenant name')
	parser.add_argument('--save-json',dest="savejson",action="store_true",help='save object in json')
	parser.add_argument('--node',action="store",help='Node')
	parser.add_argument('--interface',action="store",help='Interface')
	parser.add_argument('-t','--tenant',action="store",default="",help='tenant')
	parser.add_argument('--get-epg',dest="getepg",action="store_true",help='display EPG')
	parser.add_argument('--get-all-static-epg',dest="getallstaticepg",action="store_true",help='display all EPG static binding L2 or L3')
	parser.add_argument('--get-int-epg',dest="getintepg",action="store_true",help='display EPG on a specific interface')
	parser.add_argument('--save',dest="save",action="store_true",help='Save result in Cache')
	
	args = parser.parse_args()
	
	if args.cimc and not args.site:
		 raise argparse.ArgumentError(None,'--site is manadatory with --info-cimc ')
		 
	if args.getnode and not args.site:
		 raise argparse.ArgumentError(None,'--site is manadatory with --get-node ')
		
	if args.getallstaticepg and not args.site:
		raise argparse.ArgumentError(None,'--site is manadatory with --get-all-static-epg ')
		 
	if  args.interface and not args.node:
		 raise argparse.ArgumentError(None,'--node  is manadatory with --interface ')
		 
	if  args.getintepg and not args.interface:
		 raise argparse.ArgumentError(None,'--interface  is manadatory with --get-int-epg ')
		 
	try:
		config_file=socgenbase.get_conf_filename(args.fabric)
		with open(config_file,'r') as file:
			config_yaml=yaml.load(file,Loader)
			ip_msc=config_yaml['msc']['servers'][0]['ip']
	except :
		print("Fabric '%s' is unknown"%fabric,file=sys.stderr)
		print("Known fabrics: '%s'")
		for (name,conf) in socgenbase.hash_of_conf_files.items():
			print(" - %s (conf file: %s)"%(name,conf),file=sys.stderr)
		print()
		print("Please edit 'hash_of_conf_file' in 'dmoPy3/aci/socgenbase.py' file to add new fabrics")
		sys.exit(1)
		
	print('MSC/MSO:'+ip_msc)
	if args.list_site:
		print("Sites:")
		for site in config_yaml['sites']:
			print("- "+site['name'])
			
	if args.fabric and not args.site:
		for site in config_yaml['sites']:
			pass
		
	
	if args.site:
		info={}
		for site in config_yaml['sites']:
			if site['name']==args.site:
				info=site
				break
				
		
		apcs__ip=[]
		if not info:
			print("Site unknown",file=sys.stderr)
			sys.exit(2)
		else:
			hosts__=Hosts(dump=get_last_dump_host(PATH_HOST))
			print("apics("+site['name']+"):")
			for apc in info['apcs']:
				ip_cur=hosts__.getIP(apc)[0]
				apcs__ip.append(ip_cur)
				if ip_cur:
					print("- "+apc+"("+ip_cur+")")
				else:
					print("- "+apc)
			
			if args.cimc:
				print("cimcs("+site['name']+"):")
				for cimc in info['cimcs']:
					ip_cur=hosts__.getIP(cimc)[0]
					if ip_cur:
						print("- "+cimc+"("+ip_cur+")")
					else:
						print("- "+cimc)
						
			if args.getnode:
				nodes=getNode(apcs__ip)
				
				print('nodes('+site['name']+"):")
				for node in nodes.keys():
					print('- '+node+':'+nodes[node]['name'])
					
				if args.node:
					print("Detail for node "+args.node+":")
					print(nodes[args.node]['info'])
				
			if args.getip:
				ips__=getIp(apcs__ip,options=args)
				ppr(ips__,width=600)
				
			if args.gettenant:
				tenants_cur=getTenant(apcs__ip,options=args)
				
			if args.getepg:
				epgs_curs=get_epg(apcs__ip,args.tenant,options=args)
				ppr(epgs_curs)
				
			if args.getintepg:
				if__info=get_epg_node(apcs__ip,args.node,args.interface)
				ppr(if__info,width=300)
				
			if args.getallstaticepg:
				epgs_static=get_epgs_node(apcs__ip,options=args)
				ppr(epgs_static,width=300)
		#getFabric(apcs__ip,options=args)
					
					