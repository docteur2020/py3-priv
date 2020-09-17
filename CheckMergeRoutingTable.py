#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals



import argparse
from pprint import pprint
import pdb
import re
import sys
import checkroute
from ipcalc import Network
from xlsxDictWriter import xlsMatrix
from getNetmapInfo import NETMAPContainer
import glob
import os
from pprint import pprint as ppr

PATH_NET_DUMP="/home/X112097/CSV/NETMAP/DUMP/"

def get_last_dump_ip(rep__):
	return max(glob.glob(rep__+'/*'),key=os.path.getctime)


def checkExclude(net__,toExclude,pfxLengthMin,pfxLengthMax):
	resultat=False
	
	
	if toExclude:
		if net__.__str__() in toExclude:
			return True
			
	if net__==Network('0.0.0.0/0'):
		return True
			
	pfx_cur=net__.subnet()
	if pfx_cur > pfxLengthMax:
		return True
		
	if pfx_cur < pfxLengthMin:
		return True
	
	return resultat

def getRecoveryPrefix(dump1,dump2,toExclude=[],excludedDump=[],prefixMin=0,prefixMax=32,netmapCtr=None):

	result=[]
	RT1=checkroute.table_routage_allVRF(dump=dump1)
	RT2=checkroute.table_routage_allVRF(dump=dump2)
	
	vrf1=list(RT1.dict_RT_AllVRF.keys())[0]
	vrf2=list(RT2.dict_RT_AllVRF.keys())[0]
	
	result.append([vrf1,vrf2])
	
	sumStep=len(RT1.dict_RT_AllVRF[vrf1].tab_prefix)*len(RT2.dict_RT_AllVRF[vrf2].tab_prefix)
	step=1
	
	for entry1 in RT1.dict_RT_AllVRF[vrf1].tab_prefix:
		if checkExclude(entry1.reseau,toExclude,prefixMin,prefixMax):
			print('pass:'+entry1.reseau.__str__(),'step:',str(step)+'/'+str(sumStep))
			step+=1
			continue
		if netmapCtr:
			infoNetmap1=netmapCtr.getBestMatchInfoNet(entry1.reseau.__str__(),mode='best')
		for entry2 in RT2.dict_RT_AllVRF[vrf2].tab_prefix:
			if checkExclude(entry2.reseau,toExclude,prefixMin,prefixMax):
				print('pass:'+entry2.reseau.__str__(),'step:',str(step)+'/'+str(sumStep))
				step+=1
				continue
			if netmapCtr:
				infoNetmap2=netmapCtr.getBestMatchInfoNet(entry2.reseau.__str__(),mode='best')
			if entry1.reseau in entry2.reseau:
				if netmapCtr:
					result.append([entry1.reseau.__str__(),infoNetmap1,entry2.reseau.__str__(),infoNetmap2])
					ppr([entry1.reseau.__str__(),infoNetmap1,entry2.reseau.__str__(),infoNetmap2])
				else:
					result.append([entry1.reseau.__str__(),entry2.reseau.__str__()])
					ppr([entry1.reseau.__str__(),entry2.reseau.__str__()])
			
			ppr({'ok':[entry1.reseau.__str__(),entry2.reseau.__str__()],'step':str(step)+'/'+str(sumStep)})
			step+=1
			
	return {vrf1+' vs '+vrf2:result}

	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('dump1',help="1st dump that contains routing table")
	parser.add_argument('dump2',help="2nd dump that contains routing table")
	parser.add_argument("-x", "--xlsx", action="store",help="Excel file result the analysis",required=True)
	parser.add_argument("--exclude",  action="append",help="Exclude network",required=False)
	parser.add_argument("--file-to-exclude", dest='fileToExcluded', action="store",help="File that contains Exclude network",required=False)
	parser.add_argument("--dump-excluded", dest='dumpExcluded', action="append",help="Exclude dump that contains routing table",required=False)
	parser.add_argument("--prefix-min",dest='prefixMin', action="store",type=int,default=1,help="length prefix min",required=False)
	parser.add_argument("--prefix-max",dest='prefixMax', action="store",type=int,default=32,help="length prefix max",required=False)
	parser.add_argument("--netmap", action="store_true",default=None,help="add netmap info",required=False)
	args = parser.parse_args()
	
	if args.netmap:
		netmapDump=NETMAPContainer(dump=get_last_dump_ip(PATH_NET_DUMP))
	else:
		netmapDump=None
	
	ExcludedList=[]
	if args.fileToExcluded:
		with open(args.fileToExcluded) as file__:
			ExcludedList=[ entry.strip() for entry in file__.readlines() ]
	
	
	if args.exclude:
		ExcludedList+=args.exclude
	
	result1=getRecoveryPrefix(args.dump1,args.dump2,toExclude=ExcludedList,excludedDump=args.dumpExcluded,prefixMin=args.prefixMin,prefixMax=args.prefixMax,netmapCtr=netmapDump)
	result2=getRecoveryPrefix(args.dump2,args.dump1,toExclude=ExcludedList,excludedDump=args.dumpExcluded,prefixMin=args.prefixMin,prefixMax=args.prefixMax,netmapCtr=netmapDump)
	result1.update(result2)
	
	xlsMatrix(args.xlsx,result1)


	
