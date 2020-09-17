#!/bin/python3.7
# coding: utf-8

import sys
import argparse
import pdb
import yaml
import os
from time import gmtime, strftime , localtime

import aci.Fabric

from acitoolkit.acitoolkit import Session
from acitoolkit.aciphysobject import Node
from acitoolkit.acitoolkit import *
import pwd 

import json
from pprint import pprint as ppr

sys.path.insert(0,'/home/x112097/py3')
from getHosts import *
from getsec import *
import cache as cc


import logging


def getAllFabric():
	return list(aci.Fabric.hash_of_conf_files.keys())
	


if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	connexion=parser.add_argument_group('Need Connexion')
	saving=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument('--list-all',dest='list_all',action="store_true",help='display all known fabric')
	parser.add_argument('-f','--fabric',action="store",help='Fabric Name')
	parser.add_argument('-s','--site',action="store",help='Site Name')
	connexion.add_argument('--list-tenant',dest='list_tenant',action="store_true",help='display all known fabric tenant')
	parser.add_argument('--list-site',dest='list_site',action="store_true",help='display sites')
	parser.add_argument('--list-apics',dest='list_apics',action="store_true",help='display apics')
	parser.add_argument('--list-msc',dest='list_msc',action="store_true",help='display msc/mso controller')
	connexion.add_argument('--list-epgs',dest='list_epgs',action="store_true",help='display epgs')
	connexion.add_argument('--list-ip',dest='list_ip',action="store_true",help='list all IPv4 Address')
	connexion.add_argument('--list-bd',dest='list_bd',action="store_true",help='list all BridgeDomain')
	connexion.add_argument('--list-nodes',dest='list_nodes',action="store_true",help='list all Nodes')
	connexion.add_argument('--get-version',dest='getVersion',action="store_true",help='get apic and nodes version')
	connexion.add_argument('--get-ifstatus',dest='getIntStatus',action="store_true",help='get interface status')
	connexion.add_argument('--get-ifdescription',dest='getIntDescription',action="store_true",help='get interface description')
	connexion.add_argument('--get-portchannel',dest='getPortchannel',action="store_true",help='get port-channel')
	connexion.add_argument('--get-endpoint',dest='getEndpoint',action="store_true",help='get endpoint')
	connexion.add_argument('--get-health',dest='getHealth',action="store_true",help='get health')
	connexion.add_argument('--get-route',dest='getRoute',action="store_true",help='get route')
	connexion.add_argument('--get-contract',dest='getContract',action="store_true",help='get contract')
	saving.add_argument('--save',action="store_true",help='Save result')
	saving.add_argument('--cache',action="store_true",help='Use cache')
	args = parser.parse_args()
	
	timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
	logging.basicConfig(filename='LOG/envAci'+timestamp+'.log', level=logging.DEBUG)
	

	NeedConection=False
	if args.list_tenant or args.list_epgs or args.list_ip or args.list_bd or args.list_nodes or args.getVersion or args.getIntStatus or args.getIntDescription or args.getEndpoint or args.getHealth or args.getRoute or args.getContract or args.getPortchannel:
		NeedConection=True
		
	if args.save:
		DataToSave=[]
		
	if args.fabric: 
		fabric=aci.Fabric.Fabric(args.fabric,connect=NeedConection)
		
		sites=fabric.get_sites()
		if args.list_site:
			ppr(sites)
			
		if args.list_msc:
			ppr(fabric.mscs)
			
		if args.site:
			if args.list_apics:
				ppr(fabric.apics[args.site])
				
			if args.list_tenant:
				tenants=fabric.getTenants(site=args.site)
				fabric.print_tenants(tenants)
				
			if args.list_epgs:
				epgs=fabric.getEpgs(site=args.site)
				ppr(epgs,width=300)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_EPGS','data':epgs})
				
			if args.list_ip:
				ipv4=fabric.getIPv4Address(site=args.site)
				ppr(ipv4,width=300)
				
			if args.list_bd:
				Bds=fabric.getBds(site=args.site)
				ppr(Bds,width=300)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_BDS','data':Bds})
				
			if args.list_nodes:
				Nodes=fabric.getNode(site=args.site)
				ppr(Nodes,width=500)	
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_NODE','data':Nodes})
				
			if args.getHealth:
				Healths=fabric.getHealth(site=args.site)
				ppr(Healths,width=5)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_HEALTH','data':Healths})
				
			if args.getVersion:
				Versions=fabric.getVersion(site=args.site)
				ppr(Versions,width=5)
				
			if args.getIntStatus:
				ifStatus=fabric.getIntStatus(site=args.site)
				ppr(ifStatus,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_INT_STATUS','data':ifStatus})
					
			if args.getPortchannel:
				Portchannels=fabric.getPortchannel(site=args.site)
				ppr(Portchannels,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_PORTCHANNEL','data':Portchannels})
					
			if args.getIntDescription:
				ifDescription=fabric.getIntDescription(site=args.site)
				ppr(ifDescription,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_INT_DESCRIPTION','data':ifDescription})
					
			if args.getEndpoint:
				EPs=fabric.getEndpoint(site=args.site)
				ppr(EPs,width=500)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_EP','data':EPs})
			
			if args.getRoute:
				Rib=fabric.getRoute(site=args.site)
				ppr(Rib,width=10)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_Ribv4','data':Rib})
					
			if args.getContract:
				Cts=fabric.getContract(site=args.site)
				ppr(Cts,width=10)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_'+args.site+'_Contract','data':Cts})
					
		else:
			if args.list_apics:
				ppr(fabric.apics)
				
			if args.list_tenant:
				tenants=fabric.getTenants()
				fabric.print_tenants(tenants)
				
			if args.list_epgs:
				epgs=fabric.getEpgs()
				ppr(epgs,width=300)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_EPGS','data':epgs})
				
			if args.list_ip:
				ipv4=fabric.getIPv4Address()
				ppr(ipv4,width=300)	
				
			if args.list_nodes:
				Nodes=fabric.getNode()
				ppr(Nodes,width=500)	
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_NODE','data':Nodes})
					
			if args.list_bd:
				Bds=fabric.getBds()
				ppr(Bds,width=300)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_BDS','data':Bds})
				
			if args.getVersion:
				Versions=fabric.getVersion(site=args.site)
				ppr(Versions,width=5)
				
						
			if args.getHealth:
				Healths=fabric.getHealth()
				ppr(Healths,width=5)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_HEALTH','data':Healths})
					
			if args.getIntStatus:
				ifStatus=fabric.getIntStatus()
				ppr(ifStatus,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_INT_STATUS','data':ifStatus})
					
			if args.getPortchannel:
				Portchannels=fabric.getPortchannel()
				ppr(Portchannels,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_PORTCHANNEL','data':Portchannels})
					
			if args.getIntDescription:
				ifDescription=fabric.getIntDescription()
				ppr(ifDescription,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_INT_DESCRIPTION','data':ifDescription})		
					
			if args.getEndpoint:
				EPs=fabric.getEndpoint()
				ppr(EPs,width=1000)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_EP','data':EPs})
					
			if args.getRoute:
				Rib=fabric.getRoute()
				ppr(Rib,width=500)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_Ribv4','data':Rib})
					
			if args.getContract:
				Cts=fabric.getContract()
				ppr(Cts,width=10)
				
				if args.save:
					DataToSave.append({'tag':'ACI_'+args.fabric+'_ALLSITE_Contract','data':Cts})
				
	else:
		Fabrics_name=getAllFabric()
		
		if args.list_all:
			ppr(Fabrics_name)
			
		fabrics={}
		for fabric_name in getAllFabric():
			fabrics[fabric_name]=aci.Fabric.Fabric(name=fabric_name,connect=NeedConection)
			
		

		if args.list_site:
			sites={}
			for fabric_name in fabrics:
				sites[fabric_name]=fabrics[fabric_name].get_sites()
			ppr(sites)


		if args.list_tenant:
			tenants={}
			for fabric_name in fabrics:
				print("Fabric:",fabric_name)
				tenants[fabric_name]=fabrics[fabric_name].getTenants()
				fabrics[fabric_name].print_tenants(tenants[fabric_name])
				
		if args.list_epgs:
			epgs={}
			for fabric_name in fabrics:
				print("getting epgs for ",fabric_name,'...')
				epgs[fabric_name]=fabrics[fabric_name].getEpgs()
			ppr(epgs,width=300)
			
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_ALLSITE_EPGS','data':epgs})
				
		if args.list_ip:
			ipv4={}
			for fabric_name in fabrics:
				ipv4[fabric_name]=fabrics[fabric_name].getIPv4Address()
			ppr(ipv4,width=300)	
			
		if args.list_bd:
			Bds={}
			for fabric_name in fabrics:
				Bds[fabric_name]=fabrics[fabric_name].getBds()
			ppr(Bds,width=300)
			
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_ALLSITE_BDS','data':Bds})
		
		if args.list_nodes:
			Nodes={}
			for fabric_name in fabrics:
				print("getting node for ",fabric_name,'...')
				Nodes[fabric_name]=fabrics[fabric_name].getNode()
			ppr(Nodes,width=300)
			
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_ALLSITE_NODE','data':Nodes})
				
		if args.getVersion:
			Version={}
			for fabric_name in fabrics:
				Versions[fabric_name]=fabrics[fabric_name].getVersion()
			ppr(Versions,width=5)
			
		if args.getHealth:
			Healths={}
			for fabric_name in fabrics:
				Healths[fabric_name]=fabrics[fabric_name].getHealth()
				
			ppr(Healths,width=5)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_HEALTH','data':Healths})
				
		if args.getIntStatus:
			ifStatus={}
			for fabric_name in fabrics:
				ifStatus[fabric_name]=fabrics[fabric_name].getIntStatus()
			ppr(ifStatus,width=1000)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_INT_STATUS','data':ifStatus})
		
		if args.getPortchannel:
			Portchannels={}
			for fabric_name in fabrics:
				Portchannels[fabric_name]=fabrics[fabric_name].getPortchannel()
				
			ppr(Portchannels,width=1000)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_PORTCHANNEL','data':Portchannels})
				
		if args.getIntDescription:
			ifDescription={}
			for fabric_name in fabrics:
				ifDescription[fabric_name]=fabrics[fabric_name].getIntDescription()
			ppr(ifDescription,width=1000)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_INT_DESCRIPTION','data':ifDescription})
				
		if args.getEndpoint:
			EPs={}
			for fabric_name in fabrics:
				EPs[fabric_name]=fabrics[fabric_name].getEndpoint()
			ppr(EPs,width=1000)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_EP','data':EPs})
				
		if args.getRoute:
			Rib={}
			for fabric_name in fabrics:
				try:
					Rib[fabric_name]=fabrics[fabric_name].getRoute()
				except TypeError as E:
					pdb.set_trace()
					print('Error to get route for fabric ',fabric_name)
					print(E)
					
			ppr(Rib,width=1000)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_Ribv4','data':Rib})
				
		if args.getContract:
			Cts={}
			for fabric_name in fabrics:
				Cts[fabric_name]=fabrics[fabric_name].getContract()
			ppr(Cts,width=10)
				
			if args.save:
				DataToSave.append({'tag':'ACI_ALL_FABRIC_ALLSITE_Contract','data':Cts})
				
	if args.save:
		for data__ in DataToSave:
			cc.Cache(data__['tag'],initValue=data__['data'])
			