#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import pdb
from pprint import pprint as ppr
from ipcalc import Network , IP
from netaddr import IPNetwork

from ParsingShow import ParseRunAccessList

def wildcard_to_netmask(wildcard):
	# print(str(IP(int(IP('255.255.255.255'))-int(netmask))))
	return str(IP(int(IP('255.255.255.255'))-int(IP(wildcard))))
	
def trAclWildcardToNetmask(acl):
	resultat=[]
	for ace in acl:
		new_ace=ace
		if new_ace[3]=='ip':
			new_ace[4]=[ ace[4][0], wildcard_to_netmask(ace[4][1]) ]
			new_ace[5]=[ ace[5][0], wildcard_to_netmask(ace[5][1]) ]
		resultat.append(new_ace)
	return resultat
	
def suppressDuplicateNet(listNet):
	alreadyUsed=[]
	resultat=[]
	
	for net in listNet:
		netStr='/'.join(net)
		if netStr not in alreadyUsed:
			resultat.append(net)
			alreadyUsed.append(netStr)
			
	return resultat

def netinList(net,listNet):

	
	netObj=IPNetwork(net)
	ResList=[]
	alreadyUsed=[]
	
	for netCur in listNet:
		netObjCur=IPNetwork(netCur)
		if netObjCur in netObj or netObj in netObjCur:
			if netCur not in alreadyUsed:
				alreadyUsed.append(netCur)
			ResList.append(netCur)
			
	resultat={ 'in':len(ResList)>0 , 'match':ResList}
			
		
	return resultat
	
def getMaxNet(listNet):

	resultat=listNet[0]
	
	for netCur in listNet:
		netObjCur=IPNetwork(netCur)
		if netObjCur.prefixlen<IPNetwork(resultat).prefixlen:
			resultat=netCur
	
	return resultat
	
def suppressMinRoute(listNet):
	alreadyUsed=[]
	resultat={}
	
	resultat={listNet[0]:[listNet[0]]}
		
	for net in listNet:
		
		testCur=netinList(net,resultat)
		
		if testCur['in']:
			netMax=getMaxNet(testCur['match'])
			if IPNetwork(net).prefixlen<IPNetwork(netMax).prefixlen:
				resultat[net]=resultat[netMax]+[net]
				del resultat[netMax]
			else:
				resultat[netMax].append(net)
			
			alreadyUsed.append(net)
		else:
			resultat[net]=[net]
			
	return resultat


if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	groupSrcOrDst=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument('-f','--file',action="store",help='file containing show run',required=True)
	parser.add_argument('--acl',action="append",help='id or acl name')
	parser.add_argument('--show',action="store_true",help='show all acl')
	parser.add_argument('--mask',action="store_true",help='replace wildcard by netmask')
	groupSrcOrDst.add_argument('--only-src',dest='onlysrc',action="store_true",help='show only src')
	groupSrcOrDst.add_argument('--only-dst',dest='onlydst',action="store_true",help='show only dst')
	parser.add_argument('--uniq',action="store_true",help='suppress same multiples entries')
	
	args = parser.parse_args()
	
	if  (args.uniq  and not args.onlysrc) and (args.uniq and not args.onlydst):
		raise argparse.ArgumentError(None,'--only-src or --only-ds is manadatory with --uniq')
	
	acls=ParseRunAccessList(args.file)
	
	filterResult=args.onlysrc or args.onlydst
	
	if args.show:
		ppr(list(acls.keys()))
		
	result={}	
	
	if filterResult:
		ResultFiltered=[]
	
	if args.acl:
		try:
			for aclId in args.acl:
			
				if not args.mask:
					result[aclId]=acls[aclId]
				else:
					result[aclId]=trAclWildcardToNetmask(acls[aclId])
				
				
				if args.onlysrc:
					for ace in acls[aclId]:
						ResultFiltered.append(ace[4])
				if args.onlydst:
					for ace in acls[aclId]:
						ResultFiltered.append(ace[5])
				
		except KeyError as E:
			print(f'id or acl name unknown:{args.acl}')
			
	if filterResult:
		if not args.uniq:
			ppr(ResultFiltered)
		else:
			ResultUniq=suppressDuplicateNet(ResultFiltered)
			ppr(ResultUniq)
	else:
		ppr(result,width=300)

