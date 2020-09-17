#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import argparse
from pprint import pprint as ppr
import pdb
import re
import sys
import logging
from time import gmtime, strftime , localtime
import xlrd
from netaddr import IPNetwork

from xlsxDictWriter import xlsMatrix

from prefixFilter import *


DIR_LOG="/home/x112097/LOG"
DIR_RESULT="/home/x112097/RESULT"
PREFIXSETS_FILE='/home/x112097/RPL/PREFIXSET/10082020/ori-c1_20200810_15h29m09s.log'
DIR_RPL="/home/x112097/RPL/PREFIXSET/address/"

def formatList(f):
	def formatList_wrapper(*args,**kwargs):

		new_arg=list(args)
		
		try:
			args[0][0]
		except KeyError as E:
			return f(*args,**kwargs)
		if isinstance(args[0][0],list):
			new_arg[0]=[element[0] for element in args[0] ]
			resultat=f(*new_arg,**kwargs)
			if isinstance(resultat,list):
				return [[element] for element in resultat]
			elif isinstance(resultat,dict):
				return [[key,str(value)] for key,value in resultat.items()]
		return f(*args,**kwargs)



	return formatList_wrapper
	
@formatList
def replaceNetinList(ListNet,ListPrefix):
	resultat=[]
	

	for net in ListNet:
		netObjCur=IPNetwork(net)
		prefixPresent=False
		for prefix in ListPrefix:
			prefixObjCur=IPNetwork(prefix)
			if netObjCur in prefixObjCur:
				prefixPresent=True
				if prefix not in resultat:
					resultat.append(prefix)
		if not prefixPresent:
			if net not in resultat:
				resultat.append(net)
	return resultat
	

def isRFC1918Net(netStr):
	
	netObj=IPNetwork(netStr)
	
	if netObj in IPNetwork('10.0.0.0/8'):
		return True
		
	if netObj in IPNetwork('172.16.0.0/12'):
		return True
		
	if netObj in IPNetwork('192.168.0.0/16'):
		return True
	
	return False

@formatList
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

@formatList	
def suppressMinRoute(listNet):
	alreadyUsed=[]
	resultat={}
	
	resultat={listNet[0]:[listNet[0]]}
		
	for net in listNet:
		
		testCur=netinList(net,resultat)
		
		if testCur['in']:
			netMax=getMaxNet(testCur['match'])
			if IPNetwork(net).prefixlen<IPNetwork(netMax).prefixlen:
				resultat[net]=resultat[netMax]+[net]+testCur['match']
				for net__ in testCur['match']:
					del resultat[net__]
			else:
				resultat[netMax].append(net)
			
			alreadyUsed.append(net)
		else:
			resultat[net]=[net]
			
				
	return resultat
	
def initXlsSpec(xlsx__,logger):
	Result={}
	xl_workbook = xlrd.open_workbook(xlsx__)
	sheet_names = xl_workbook.sheet_names()
	
	
	for sheet__ in sheet_names:
		logger.debug(f"current sheet {sheet__}")
		if sheet__=="CONFLICT":
			logger.info(f"get informations from {sheet__}")
			xl_sheet = xl_workbook.sheet_by_name(sheet__)
			Result[sheet__]=[]
			for rownum in range(0,xl_sheet.nrows):
				if rownum == 0:
					vrf1=xl_sheet.row_values(rownum)[0]
					vrf2=xl_sheet.row_values(rownum)[1]
					Result[sheet__]={'vrf':[vrf1,vrf2],'nets':[]}
					continue
				Result[sheet__]['nets'].append([xl_sheet.row_values(rownum)[0].strip(),xl_sheet.row_values(rownum)[1].strip()])
		elif sheet__=="RVP_SHAREDSERVICES" or sheet__=="ITECinRIX" or sheet__=="RIXinITEC":
			Result[sheet__]=[]
			logger.info(f"get informations from {sheet__}")
			xl_sheet = xl_workbook.sheet_by_name(sheet__)
			for rownum in range(0,xl_sheet.nrows):
				Result[sheet__].append(xl_sheet.row_values(rownum)[0].strip())
		else:
			pdb.set_trace()
			logger.info(f"{sheet__} not included")
	return Result
		
def initPrefixSetObj(name,PrefixListStr):
	resultat=None
	PrefixListObj=[]
	for prefixsetentryStr in PrefixListStr:
		try:
			dataCur=ParsePrefixSetEntry(prefixsetentryStr)
		except pp.ParseException as E:
			pdb.set_trace()
			print(E)
		prefixCurStr=list(dataCur.keys())[0]
		filterPrefixCur=dataCur[prefixCurStr]
		PrefixListObj.append(prefixSetEntry(prefixCurStr,filterPrefix=filterPrefixCur))
		
	resultat=prefixSet(name=name,PrefixSetList=PrefixListObj)
	
	return resultat
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--xlsx", action="store",help="Excel File that contains informations",required=True)
	parser.add_argument("--debug", action="store_true",help="mode debug")
	args = parser.parse_args()
	
	rootLogger = logging.getLogger('Logger FilterAddressSpec')
	timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
	FileResult=f"{DIR_RESULT}/FilterAddressSpecResult{timestamp}.xlsx"
	fileHandler = logging.FileHandler(f"{DIR_LOG}/FilterAddressSpec{timestamp}.log")
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
	
	rootLogger.info("get informations from xlsx")
	info=initXlsSpec(args.xlsx,rootLogger)
	rootLogger.debug(f"value info:{info}")
	ppr(info)
	
	rootLogger.info("Check conflict already annonced")
	ResultConflictAnnonced=[['ITEC','RIX','ITEC in RIX?','RIX in ITEC?','ITEC From RVP_SHAREDSERVICES?','RIX From RVP_SHAREDSERVICES?','ITEC RFC1918?','RIX RFC 1918?']]
	ResultConflictAnnoncedWoSharedServices=[['ITEC','RIX','ITEC in RIX?','RIX in ITEC?','ITEC From RVP_SHAREDSERVICES?','RIX From RVP_SHAREDSERVICES?','ITEC RFC1918?','RIX RFC 1918?','RIX match PFX?','ITEC match PFX?']]
	ResultMaxNetRIX=[['RIX Max Conflict']]
	ResultMaxNetITEC=[['ITEC Max Conflict']]
	AllITECConflict=[]
	AllRIXConflict=[]
	rootLogger.debug(f"init prefix-set-obj")
	prefixSetsObj=prefixSets(PREFIXSETS_FILE,verbose=args.debug)
	whiteListRIX2ITEC=[]
	whiteListITEC2RIX=[]
	AllRIXConflictAuthorizedInITEC=[]
	AllITECConflictAuthorizedInRIX=[]
	for conflict in info['CONFLICT']['nets']:
		ResITEC=conflict[1]
		ResRIX=conflict[0]
		
		testITEC_RFC1918=isRFC1918Net(ResITEC)
		testRIX_RFC1918=isRFC1918Net(ResRIX)
		
		matchPrefixRIX2ITEC=prefixSetsObj['pfx-RCSG-bgp-in-p2'].search(ResRIX)
		matchPrefixITEC2RIX=prefixSetsObj['pfx-RCSG-bgp-out'].search(ResITEC)
		
		
		if ResITEC in info["ITECinRIX"]:
			ResCur=['yes']
			ITECinRIX=True
		else:
			ResCur=['no']
			ITECinRIX=False
			
		if ResRIX in info["RIXinITEC"]:
			ResCur.append('yes')
			RIXinITEC=True
		else:
			ResCur.append('no')
			RIXinITEC=False
			
		if ResITEC in info["RVP_SHAREDSERVICES"]:
			ResCur.append('yes')
			Cur_SS_ITEC=True
		else:
			ResCur.append('no')	
			Cur_SS_ITEC=False
					
					
		if ResRIX in info["RVP_SHAREDSERVICES"]:
			ResCur.append('yes')
			Cur_SS_RIX=True
		else:
			ResCur.append('no')
			Cur_SS_RIX=False
			
		if not Cur_SS_RIX and not testRIX_RFC1918:
			AllRIXConflict.append([ResRIX,matchPrefixRIX2ITEC])
			if RIXinITEC:
				if ResRIX not in AllRIXConflictAuthorizedInITEC:
					AllRIXConflictAuthorizedInITEC.append(ResRIX)

			
		if not Cur_SS_ITEC and not testITEC_RFC1918:
			AllITECConflict.append([ResITEC,matchPrefixITEC2RIX])
			if ITECinRIX:
				if ResITEC not in AllITECConflictAuthorizedInRIX:
					AllITECConflictAuthorizedInRIX.append(ResITEC)
		
		rootLogger.debug(f"values ResITEC:{ResITEC} ResRIX:{ResRIX} ITECinRIX: {ResCur[0]} RIXinITEC:{ResCur[1]} prefix RIX 2 ITEC: { matchPrefixRIX2ITEC} prefix ITEC 2 RIX:{matchPrefixITEC2RIX}")		
		ResultConflictAnnonced.append(conflict+ResCur+[str(testITEC_RFC1918),str(testRIX_RFC1918)])
		
			
		if not (Cur_SS_ITEC and Cur_SS_RIX) and not (testITEC_RFC1918 and testRIX_RFC1918):
			ResultConflictAnnoncedWoSharedServices.append(conflict+ResCur+[str(testITEC_RFC1918),str(testRIX_RFC1918),str(matchPrefixRIX2ITEC),str(matchPrefixITEC2RIX)])
		
	rootLogger.debug(f"Suppress duplicate RIX")
	AllRIXConflictUniq=suppressDuplicateNet(AllRIXConflict)
	rootLogger.debug(f"Suppress duplicate ITEC")
	AllITECConflictUniq=suppressDuplicateNet(AllITECConflict)
	AllConflictUniq=suppressDuplicateNet(AllRIXConflict+AllITECConflict)
	
	rootLogger.debug(f"Summarize RIX")
	AllRIXConflictUniqSummary=suppressMinRoute(AllRIXConflictUniq)
	rootLogger.debug(f"Summarize ITEC")
	AllITECConflictUniqSummary=suppressMinRoute(AllITECConflictUniq)
	
	rootLogger.debug(f"BlackList")

	BlackListCur=suppressMinRoute(AllConflictUniq)
	BlackList=[]
	BlackListNormal=[]

		
	
	
	
	for entry in sorted(BlackListCur,key=lambda t: t[0] ):
		if '/32' in entry[0]:
			BlackList.append([entry[0]])
			BlackListNormal.append(entry[0])
		else:
			BlackList.append([ f'{entry[0]} le 32'] )
			BlackListNormal.append(f'{entry[0]} le 32')
			
	
	BlackListPrefixSet=initPrefixSetObj("BlackList",BlackListNormal)
	
	rootLogger.debug(f"Replace Interco RIX")
	AllRIXConflictUniqSummaryFiltered=replaceNetinList(AllRIXConflictUniqSummary,['192.0.0.0/14','192.4.0.0/16'])
	rootLogger.debug(f"Replace Interco ITEC")
	AllITECConflictUniqSummaryFiltered=replaceNetinList(AllITECConflictUniqSummary,['192.0.0.0/14','192.4.0.0/16'])
	
	rootLogger.debug(f"white list initialization RIX")

	for entry in info["RIXinITEC"]:
		if entry in BlackListPrefixSet:
			matchPrefixRIX2ITECCur=prefixSetsObj['pfx-RCSG-bgp-in-p2'].search(entry)
			whiteListRIX2ITEC.append([entry,str(matchPrefixRIX2ITECCur),matchPrefixRIX2ITECCur[3]])
	
	
    
	
	rootLogger.debug(f"white list initialization ITEC")	
	for entry in info["ITECinRIX"]:
		if entry in BlackListPrefixSet:
			matchPrefixITEC2RIXCur=prefixSetsObj['pfx-RCSG-bgp-out'].search(entry)
			whiteListITEC2RIX.append([entry,str(matchPrefixITEC2RIXCur),matchPrefixITEC2RIXCur[3]])
	
	
			
	rootLogger.debug(f"value info:{info}")
	
	rootLogger.debug(f"Black List prefix-set object generation")
	blackListFilename=f'{DIR_RPL}BLACK_LIST_RIX_ITEC{timestamp}.TXT'
	
	#whiteListRIX2ITEC.sort(key=lambda t:IPNetwork(t[0]))
	#whiteListITEC2RIX.sort(key=lambda t:IPNetwork(t[0]))
	rootLogger.debug(f"Sorting prefix-list before writing in file")
	whiteListRIX2ITEC__=list(set([ entry[2] for entry in whiteListRIX2ITEC ]))
	whiteListITEC2RIX__=list(set([ entry[2] for entry in whiteListITEC2RIX ]))
	whiteListRIX2ITEC__.sort(key=lambda t:IPNetwork(t.split()[0]))
	whiteListITEC2RIX__.sort(key=lambda t:IPNetwork(t.split()[0]))
	rootLogger.debug(f"prefix-list file generation")
	with open(blackListFilename,'w') as file_bl_w:
		file_bl_w.write("\r\n".join([ entry[0] for entry in BlackList ]))
	rootLogger.debug(f"White List RIX prefix-set object generation")
	whiteListRIXFilename=f'{DIR_RPL}WHITE_LIST_RIX{timestamp}.TXT'
	with open(whiteListRIXFilename,'w') as file_wl_rix_w:
		file_wl_rix_w.write("\r\n".join(whiteListRIX2ITEC__))
	rootLogger.debug(f"White List ITEC prefix-set object generation")
	whiteListITECFilename=f'{DIR_RPL}WHITE_LIST_ITEC{timestamp}.TXT'
	with open(whiteListITECFilename,'w') as file_wl_itec_w:
		file_wl_itec_w.write("\r\n".join(whiteListITEC2RIX__))
		
	rootLogger.debug(f"Excel generation")
	xlsMatrix(FileResult,{'CONFLICT CURRENT ANALYSIS':ResultConflictAnnonced,\
						'CONFLICT Wo SHARED SERV':ResultConflictAnnoncedWoSharedServices,\
						'RIX Conflict wo SS wo Private':[['RIX']]+AllRIXConflictUniq,\
						'ITEC Conflict wo SS wo Private':[['ITEC']]+AllITECConflictUniq,\
						'RIX Conflict Summary':[['Supernet','Nets']]+AllRIXConflictUniqSummary,\
						'ITEC Conflict Summary':[['Supernet','Nets']]+AllITECConflictUniqSummary,\
						'RIX Conflict Filtered':[['Supernet']]+AllRIXConflictUniqSummaryFiltered,\
						'ITEC Conflict Filterd':[['Supernet']]+AllITECConflictUniqSummaryFiltered,\
						'BlackList':[['Supernet']]+BlackList,\
						'White List RIX': [['prefix','match','prefix-set-entry']] +[ entry for entry in sorted(whiteListRIX2ITEC)] ,\
						'White List RVP_ITEC': [['prefix','match','prefix-set-entry']] + [ entry for entry in sorted(whiteListITEC2RIX)] })
	
	
			
