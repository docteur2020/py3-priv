#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import json
import glob
import os
import pdb
import pyparsing as pp
import sys
import re
from pprint import pprint

OUI_DIR = "/home/x112097/DUMP/OUI"

def getMacOUI(mac__):
	return {'mac':mac__,'oid':mac__[0:8],'long_oid':mac__[0:13]}
	
def getMacSuffixe(mac__):
	return {'mac':mac__,'suffixe':mac__[8:17],'long_suffixe':':'+mac__[13:17]}

def ParseMac(macStr):
	resultat=None
	Octet=pp.Word(pp.nums+'abcdef'+'ABCDEF',exact=2).setParseAction(lambda t : t[0].upper())
	Separator=pp.Word(':-.',exact=1).setParseAction(pp.replaceWith(':'))
	MacWoSep=pp.Combine(6*Octet).setParseAction(lambda t : t[0][0]+t[0][1]+":"+t[0][2]+t[0][3]+":"+t[0][4]+t[0][5]+":"+t[0][6]+t[0][7]+":"+t[0][8]+t[0][9]+":"+t[0][10]+t[0][11])
	MacCisco=pp.Combine((2*Octet+Separator)*2+(2*Octet)).setParseAction(lambda t : t[0][0]+t[0][1]+":"+t[0][2]+t[0][3]+":"+t[0][5]+t[0][6]+":"+t[0][7]+t[0][8]+":"+t[0][10]+t[0][11]+":"+t[0][12]+t[0][13])
	MacUnix=pp.Combine((Octet+Separator)*5+Octet)
	Mac=pp.MatchFirst([MacWoSep,MacCisco,MacUnix])
	try:
		resultat=Mac.parseString(macStr,parseAll=True).asList()[0]
	except  pp.ParseException as ppError:
		print("Vérifiez le format de l'adresse Mac")
		sys.exit(1)
	 
	return resultat
	

class jsonFile(object):
	def __init__(self,nom_fichier):
		self.fichier=nom_fichier
	
	def save(self,data):
		with open(self.fichier,'w') as file:
			json.dump(data,file)
	
	def load(self):
		data=None
		try:
			with open(self.fichier,'r') as file:
				data=json.load(file)
		except json.decoder.JSONDecodeError as e:
			if e.msg=='Extra data':
				data={}
				dataOUI={}
				dataComp={}
				#print(e.msg)
				
				with open(self.fichier,'r') as file:
					all_lines=[ line.rstrip('\n') for line in file] 
					for line in all_lines:
						dict_cur=json.loads(line)
						dataOUI[dict_cur['oui']]=dict_cur
						if dict_cur['companyName'] in dataComp.keys():
							dataComp[dict_cur['companyName']].append(dict_cur['oui'])
						else:
							dataComp[dict_cur['companyName']]=[dict_cur['oui']]
						
				data['oui']=dataOUI	
				data['companyName']=dataComp
				
		
		return data


class OUIContainer(object):

	def __init__(self):
		self.dumpFile=self.getLastDump()
		self.dump=jsonFile(self.dumpFile)
		self.data=self.dump.load()
			
	def getLastDump(self):
		return max(glob.glob(OUI_DIR+'/*'),key=os.path.getctime)
		
	def getInfoMac(self,mac):
		info=None
		mac__allinfo=getMacOUI(mac_cur)
		try:
			info=self.data['oui'][mac__allinfo['long_oid']]
		except KeyError:
			try:
				info=self.data['oui'][mac__allinfo['oid']]
			except KeyError:
				print("Info non trouvée")
	
		return info
		
	def getAllCompany(self,regex=""):
		if regex:
			 regex__= re.compile(regex, re.IGNORECASE)
			 return [ company__ for company__ in self.data['companyName'].keys() if regex__.search(company__)]
		else:
			return [ company__ for company__ in self.data['companyName'].keys() ]
		
	def getOIDCompany(self,regex):
		resultat={}
		regex__= re.compile(regex, re.IGNORECASE)
		for company__ in self.data['companyName'].keys():
			if regex__.search(company__):
				resultat[company__]=self.data['companyName'][company__]
				
		return resultat
		
	def translateMac(self,mac__):
		info=None
		resultat=mac__
		mac__allinfo=getMacOUI(mac__)
		mac__suffixe=getMacSuffixe(mac__)
		pattern = re.compile('\W')
		try:
			info=self.data['oui'][mac__allinfo['long_oid']]
			prefixe=re.sub(pattern,'',info['companyName'])
			resultat=prefixe+mac__suffixe['long_suffixe']
		except KeyError:
			try:
				info=self.data['oui'][mac__allinfo['oid']]
				prefixe=re.sub(pattern,'',info['companyName'])
				resultat=prefixe+mac__suffixe['suffixe']
			except KeyError:
				print("Info non trouvée")
				
		return resultat
		
	def translate(self,mac_):
		info=None
		mac__=ParseMac(mac_)
		resultat=mac__
		mac__allinfo=getMacOUI(mac__)
		mac__suffixe=getMacSuffixe(mac__)
		pattern = re.compile('\W')
		try:
			info=self.data['oui'][mac__allinfo['long_oid']]
			prefixe=re.sub(pattern,'',info['companyName'])
			resultat=prefixe+mac__suffixe['long_suffixe']
		except KeyError:
			try:
				info=self.data['oui'][mac__allinfo['oid']]
				prefixe=re.sub(pattern,'',info['companyName'])
				resultat=prefixe+mac__suffixe['suffixe']
			except KeyError:
				print("Info non trouvée")
				
		return resultat	
		
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-m", "--mac",action="store",help=u"Recherche d'un oui pour une mac",required=False)
	parser.add_argument("--listCompany",action="store",help=u"Liste les company (regex) ALL pour tous",required=False)
	parser.add_argument("-c", "--companyName",action="store",help=u"Recherche des mac pour une company (regex)",required=False)
	parser.add_argument("-t", "--translate",action="store",help=u"remplace OUI par nom du constructeur",required=False)
	args = parser.parse_args()
	
	ouiDB=OUIContainer()
	
	if args.translate:
		mac_cur=ParseMac(args.translate)
		mac__t=ouiDB.translateMac(mac_cur)
		print(mac__t)
		
	if args.mac:
		mac_cur=ParseMac(args.mac)
		info__=ouiDB.getInfoMac(mac_cur)
		print(info__)
		
	if args.listCompany:
		if args.listCompany=='ALL':
			allCompany__=ouiDB.getAllCompany()
			pprint(allCompany__)
		else:
			allCompany__=ouiDB.getAllCompany(args.listCompany)
			pprint(allCompany__)
	if args.companyName:
		oid__=ouiDB.getOIDCompany(args.companyName)
		pprint(oid__)

		
			
