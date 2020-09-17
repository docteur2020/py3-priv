#!/usr/bin/env python3.7
# coding: utf-8

import pdb
import sys
import logging
import argparse
import aci.Fabric as ACISbe
from time import gmtime, strftime , localtime
from getArpUnicorn import *
from getMarleyInfo import get_last_dump , marleyContainer
import dns.resolver
from pprint import pprint as ppr
from xlsxDictWriter import xlsMatrix

sys.path.insert(0,'/home/x112097/py3')
from getHosts import *
from getsec import *
import cache as cc

DIR_LOG="/home/x112097/LOG"
LISTE_DNS=['192.16.207.80','184.12.21.17']
PATH_MARLEY_DUMP="/home/X112097/CSV/MARLEY/DUMP/"
PATH_RESULT="/home/X112097/IMPACT"

def getReverseDns(IP):
		resultat=[]
		for DNS in LISTE_DNS:
			name_cur=None
			try:
				name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),DNS).answer[0].__str__().split()[-1]
			except IndexError:
				pass
			if name_cur:
				resultat.append(name_cur)
		return resultat
		
def getBriefInfoFromDBMarley(db,mac__,ip__):
	infoMac=db.getInfoMac(mac__)
	infoIp=db.getInfoIP(ip__)
	

	
	if infoMac:
		for key in infoMac:
			for info in infoMac[key]:
				return { 'Asset ID': info['Asset ID'],'Usual name': info['Usual name'] }
				
	if ip__=='0.0.0.0':
		return
		
	if infoIp:
		for key in infoIp:
			for info in infoIp[key]:
				return { 'Asset ID': info['Asset ID'],'Usual name': info['Usual name'] }
				
	
def getMemberPo(poName,site,listNode,portchannels__):
	members=[]
	for node__ in listNode:
		members.append({'node':node__,'members':list(portchannels__[site][node__][poName]['members'].keys())} )
	
	
	return members

def getDescPo(	members,site,descriptions__):
	
	descList=[]
	
	for member in members:
		descListCur=[]
		for eth in member['members']:
			desc_cur=descriptions__[site][member['node']][eth]
			descListCur.append(eth.replace('eth','eth'+member['node']+'/')+':'+desc_cur)
		descList.append(":".join(descListCur))
		
	resultat="-".join(descList)
		
	
	return resultat
		

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--fabric", action="store",help="Aci Fabric",required=True)
	parser.add_argument("--renew", action="store_true",help="Renew all db")
	parser.add_argument("--debug", action="store_true",help="mode debug")
	args = parser.parse_args()
	
	rootLogger = logging.getLogger('Logger getImpactFabricAci')
	timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
	fileHandler = logging.FileHandler(f"{DIR_LOG}/getImpactFabricAci{timestamp}.log")
	customHandler = logging.StreamHandler()
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fileHandler.setFormatter(formatter)
	rootLogger.addHandler(fileHandler)
	rootLogger.setLevel(logging.INFO)
	
	if args.debug:
		consoleHandler = logging.StreamHandler()
		consoleHandler.setFormatter(formatter)
		rootLogger.addHandler(consoleHandler)
		rootLogger.setLevel(logging.DEBUG)
	
	if args.fabric:
		listeFabric=ACISbe.Fabric.getFabricName()
		if args.fabric not in listeFabric:
			print('Fabric unknown',file=sys.stderr)
			print('Known fabrics:',str(listeFabric))
			sys.exit(1)
			
	
	if args.renew:
		DataToSave=[]
		rootLogger.info("renew all db")
		rootLogger.info("apics fabric connection")
		fabric=ACISbe.Fabric(args.fabric,connect=True)
		
		rootLogger.info("get endpoints")
		endpoints=fabric.getEndpoint()
		rootLogger.info("saving endpoints in cache")
		DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_EP','data':endpoints})
		rootLogger.debug(f"endpoints:{endpoints}")
		
		rootLogger.info("get interface description")
		descriptions=fabric.getIntDescription()
		DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_INT_DESCRIPTION','data':descriptions})
		rootLogger.debug(f"descriptions:{descriptions}")
		
		rootLogger.info("get portachannel")
		portchannels=fabric.getPortchannel()
		DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_PORTCHANNEL','data':portchannels})
		rootLogger.debug(f"descriptions:{descriptions}")
		
		rootLogger.info("get Node")
		nodes=fabric.getNode()
		rootLogger.info("saving nodes in cache")
		DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_NODE','data':nodes})
		rootLogger.debug(f"nodes:{nodes}")
		
		rootLogger.info("get arps entries from unicorns")
		arps=getArpFromUnicorn()
		rootLogger.debug(f"arps:{arps}")
		
		rootLogger.info("Saving result in cache db")
		for data__ in DataToSave:
			cc.Cache(data__['tag'],initValue=data__['data'])

	else:
		rootLogger.info("use cache")
		rootLogger.info("get endpoints")
		endpoints=ACISbe.Fabric.getEndpointFromeCache(args.fabric)
		
		#rootLogger.debug(f"endpoints:{endpoints}")
		if not endpoints:
			rootLogger.error("No cache for endpoints")
			print("Issue to get endppoints from cache, try to use --renew option")
			sys.exit(1)
			
		rootLogger.info("get interface description")
		descriptions=ACISbe.Fabric.getIfDescriptionFromeCache(args.fabric)
		#rootLogger.debug(f"descriptions:{descriptions}")
		if not descriptions:
			rootLogger.error("No cache for descriptions")
			print("Issue to get descriptions from cache, try to use --renew option")
			sys.exit(1)
			
		rootLogger.info("get portchannel")
		portchannels=ACISbe.Fabric.getPortchannelFromeCache(args.fabric)
		rootLogger.debug(f"portchannels:{portchannels}")
		if not portchannels:
			rootLogger.error("No cache for portchannels")
			print("Issue to get portchannels from cache, try to use --renew option")
			sys.exit(1)
			
		rootLogger.info("get node")
		nodes=ACISbe.Fabric.getNodeFromeCache(name=args.fabric)
		#rootLogger.debug(f"nodes:{nodes}")
		if not nodes:
			rootLogger.error("No cache for nodes")
			print("Issue to get node from cache, try to use --renew option")
			sys.exit(1)
			
		rootLogger.info("get arps entries from unicorns")
		arps=load_json_arp(getLastDumpArp())
		#rootLogger.debug(f"arps:{arps}")
		if not arps:
			rootLogger.error("No cache for arps")
			print("Issue to get arps from cache, try to use --renew option")
			sys.exit(1)
			
	baseMarley=marleyContainer(dump=get_last_dump(PATH_MARLEY_DUMP))
	
	resultat={}
	header=['SWITCH','MAC','IP','REVERSE_DNS','VLAN','VRF/APPLICATION PROFILE','PORT','DESCRIPTION','ASSET ID','UsualName']
	
	rootLogger.debug(f"Processing endpoints...")
	for site in endpoints:
		resultat[site]=[header]
		rootLogger.debug(f"  site:{site}")
		for node in endpoints[site]:
			if '-' in node:
				node_list=node.split('-')
				switch_cur=':'.join([ nodes[site][node_cur]['name'] for node_cur in node_list ])
				rootLogger.debug(f"  switch_cur:{switch_cur}")
			else:
				switch_cur=nodes[site][node]['name']
			if '-SPN-' in switch_cur  or '-APC-' in switch_cur or '-BRD-' in switch_cur:
				continue
			for interface in endpoints[site][node]:
				if 'OTV' in interface:
					continue
				for endpoint in endpoints[site][node][interface]:
					mac_cur=endpoint[3]
					ip_cur=endpoint[4]
					if ip_cur=='0.0.0.0':
						try:
							ip_cur=arps[mac_cur][0]['ip']
						except KeyError:
							pass
					vrf_cur=endpoint[1]
					dns_cur=getReverseDns(ip_cur)
					vlan_cur=endpoint[5]
					if '-' in node:
						members=getMemberPo(interface,site,node_list,portchannels)
						desc_cur=getDescPo(	members,site,descriptions)
					else:
						desc_cur=descriptions[site][node][interface]
	
						
					infoMarleyCur=getBriefInfoFromDBMarley(baseMarley,mac_cur,ip_cur)
					if infoMarleyCur:
						asset_id_cur=infoMarleyCur['Asset ID']
						usualName=infoMarleyCur['Usual name']
					else:
						asset_id_cur='Unknown'
						usualName='Unknown'
					entry_cur=[switch_cur,mac_cur,ip_cur,dns_cur,vlan_cur,vrf_cur,interface,desc_cur,asset_id_cur,usualName]
					rootLogger.debug(f"add entry:{entry_cur}")
					resultat[site].append([str(info) for info in entry_cur])
					
	ppr(resultat)
	xlsx_file=PATH_RESULT+'/'+args.fabric.upper()+timestamp+".xlsx"
	rootLogger.debug(f"saving result to {xlsx_file}")
	xlsMatrix(xlsx_file,resultat)
		