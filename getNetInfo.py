#!/usr/bin/env python3.7
# coding: utf-8


import sys
import os
import argparse
from getNetmapInfo import NETMAPContainer
from ipEnv import ifEntries , interface
import glob
import pdb
from xlsxDictWriter import xlsMatrix
from netaddr import IPNetwork
from pprint import pprint as ppr

import pdb

PREFIX_DUMP_DIR="/home/x112097/DUMP/PREFIX"
IP_DUMP_DIR="/home/x112097/IP/DUMP/CISCO-ALL"
PATH_NET_DUMP="/home/X112097/CSV/NETMAP/DUMP/"

def getListNetFromFile(filename):
	with open(filename,'r') as file_r:
		listNet=file_r.read().split()
		return listNet

def get_last_dump_ip(rep__):
	return max(glob.glob(rep__+'/*'),key=os.path.getctime)

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	groupNet=parser.add_mutually_exclusive_group(required=True)
	groupNet.add_argument("-n", "--network",action="store",help="Network or IP")
	groupNet.add_argument("-f", "--file",action="store",help="Text file that contains Network or IP")
	parser.add_argument("--xlsx",action="store",help="Résultat sous forme fichier excel",required=False)

	
	args = parser.parse_args()
	
	defaultDump=get_last_dump_ip(IP_DUMP_DIR)
	DC_IP=ifEntries(dump=defaultDump)
	netmapContainer=NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP))
	
	if args.network:
		infoConnected=DC_IP.getConnected(args.network)
		infoNetmap=netmapContainer.getBestMatchInfoNet(args.network,mode='best')
		infoReverseip=DC_IP.searchIP(args.network)
		resultat=[args.network,infoConnected,infoNetmap,infoReverseip]
		
		ppr(resultat)
		
	if args.file:
		resultat=[]
		listeNetwork=getListNetFromFile(args.file)
		nbEntry=len(listeNetwork)
		step=1
		for net__ in listeNetwork:
			infoConnectedCur=DC_IP.getConnected(net__)
			infoNetmapCur=netmapContainer.getBestMatchInfoNet(net__,mode='best')
			infoReverseipCur=DC_IP.searchIP(net__)
			resultat.append([net__,str(infoConnectedCur),str(infoNetmapCur),str(infoReverseipCur)])
			print('step:'+str(step)+'/'+str(nbEntry))
			step+=1
		if args.xlsx:
			resultat.insert(0,['NETWORK/IP','CONNECTED INTERFACE','NETMAP INFO','REVERSE IP'])
			xlsMatrix(args.xlsx,{'INFO NETWORKS':resultat})
		
		ppr(resultat)

