#!/usr/bin/env python3.7
# coding: utf-8


import pyparsing as pp
from ipaddress import ip_address as ipaddr
from ParsingShow import writeCsv
import csv
import checkroute
import sys
import os
import argparse
import pickle
import pdb

class NH(object):
	"Classe NextHop"
	
	def __init__(self,Code,IP):
		"Constructeur"
		self.attribut=Code
		self.nexthop=IP
	
	def __str__(self):
		"Affichage"
		return self.attribut+";"+self.nexthop
		
	def __ne__(self,other):
		return self.IP != other.IP
			
	def __eq__(self,other):
		return self.IP == other.IP
			
	def is_eBGP(self):
		result=True
		
		if 'i' in self.attribut:
			result=False
			
		return result
		
class prefix(object):
	"definit un prefix BGP"
	
	def __init__(self,reseau="0.0.0.0",nexthops=[]):
		"Constructeur"
		
		self.reseau=reseau
		self.nexthops=nexthops	
		
	
	def __str__(self):
		"Affichage"
		resultat="P:"+str(self.reseau)+":"
		for NH__ in self.nexthops:
			resultat=resultat+"NH:"+str(NH__)+";"
		
		return resultat
		
def ParseBgpTableXR(File__):
	
	Resultat=None
	Day=pp.Literal('Mon')|pp.Literal('Tue')|pp.Literal('Wed')|pp.Literal('Thu')|pp.Literal('Fri')|pp.Literal('Sat')|pp.Literal('Sun')
	Month=pp.Literal('Jan')|pp.Literal('Feb')|pp.Literal('Mar')|pp.Literal('Apr')|pp.Literal('May')|pp.Literal('Jun')|pp.Literal('Jul')|pp.Literal('Aug')|pp.Literal('Sep')|pp.Literal('Oct')|pp.Literal('Nov')|pp.Literal('Dec')
	Date=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=31 and int(tokens[0]) >= 1 )
	Hour=pp.Word(pp.nums,exact=2)+(pp.Literal(':')+pp.Word(pp.nums,exact=2))*2+pp.Literal('.')+pp.Word(pp.nums)
	Timestamp=pp.Suppress(Day+Month+Date+Hour+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n'))+Timestamp)
	Virgule=pp.Suppress(pp.Literal(','))
	VRF__1=pp.Literal('BGP VRF ').suppress()+pp.Word(pp.alphanums+"-_*")+Virgule+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF__2=pp.Literal('VRF: ').suppress()+pp.OneOrMore(pp.CharsNotIn('\n'))+pp.Suppress(pp.Literal('--')+pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF=pp.MatchFirst([VRF__1,VRF__2])
	BGP_rd=pp.Suppress(pp.Literal('BGP Route Distinguisher:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='VRF ID:',closer='Weight Path') )
	RD=pp.Suppress(pp.Literal('Route Distinguisher:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Process=pp.Suppress(pp.Literal('Processed')+pp.OneOrMore(pp.CharsNotIn('\n')))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=(pp.Word(pp.nums)+pp.OneOrMore(pp.CharsNotIn('\n')))
	NextHop=pp.Group(ipAddress+OtherAttributes)
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes)
	FirstInfo=pp.Group(Code+Prefix+NextHop)
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(VRF,default="GRT")+pp.Optional(BGP_rd+Legend+RD),pp.Optional(pp.Group(Entries)+Process,default=None ))+pp.ZeroOrMore(hostname)
	Resultat=BlocVrf.parseFile(File__,parseAll=True)
	
	return Resultat
	
def ParseBgpTableIOS(File__):
	
	Resultat=None
	End=pp.Suppress(pp.LineEnd())
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='BGP table version',closer='Weight Path') )
	RD=pp.Suppress(pp.Literal('Route Distinguisher:')+pp.Word(pp.nums)+pp.Literal(':')+pp.Word(pp.nums))
	VRF=RD+pp.Suppress(pp.Literal('(default for vrf '))+pp.Word(pp.alphanums+"-_*")+pp.Suppress(pp.Literal(')'))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix__slash=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Prefix__wo__slash=pp.Combine(octet + ('.'+octet)*3).setParseAction(lambda s,l,t : t[0]+'/'+getDefaultMask(t[0]) )
	Prefix=pp.MatchFirst([Prefix__slash,Prefix__wo__slash])
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=pp.Word(pp.nums)+pp.White()+pp.OneOrMore(pp.CharsNotIn('\n'))
	NextHop=pp.Group(ipAddress+OtherAttributes)+End
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes+End)
	FirstInfo=Code+Prefix+NextHop
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(Legend+VRF,default="GRT"),pp.MatchFirst([pp.Group(Entries),hostname])+pp.Optional(pp.OneOrMore(hostname)))
	Resultat=BlocVrf.parseFile(File__,parseAll=True)
	
	return Resultat
	
def ParseBgpTableNxOS(File__):
	
	Resultat=None
	End=pp.Suppress(pp.LineEnd())
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='BGP table version',closer='Weight Path') )
	VRF1=pp.Suppress(pp.Literal('BGP routing table information for VRF'))+pp.Word(pp.alphanums+"-_*,").setParseAction(lambda t : t[0].replace(',',''))+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF2=pp.Suppress(pp.Literal('Unknown vrf '))+pp.Word(pp.alphanums+"-_*,")+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF=pp.MatchFirst([VRF1,VRF2])
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix__slash=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Prefix__wo__slash=pp.Combine(octet + ('.'+octet)*3).setParseAction(lambda s,l,t : t[0]+'/'+getDefaultMask(t[0]) )
	Prefix=pp.MatchFirst([Prefix__slash,Prefix__wo__slash])
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?|&r',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=pp.Word(pp.nums)+pp.White()+pp.OneOrMore(pp.CharsNotIn('\n'))
	NextHop=pp.Group(ipAddress+OtherAttributes)+End
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes+End)
	FirstInfo=pp.Group(Code+Prefix+NextHop)
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(VRF+pp.Optional(Legend),default="GRT"),pp.MatchFirst([pp.Group(Entries),hostname])+pp.Optional(pp.OneOrMore(hostname)))
	Resultat=BlocVrf.parseFile(File__,parseAll=True)
	
	return Resultat
	
def AddAttributesFirstRoute(string,location,token):
	resultat=[]
	
	
	Code_NH1=token[0][0][0]
	Prefix=token[0][0][1]
	FirstNH=token[0][0][2]
	
	listeNH=[[Code_NH1,FirstNH]]
	
	for NH in  token[0][1:]:
		listeNH.append([NH[0][0],NH[0][1:]])
	
	resultat=[Prefix,listeNH]

	return resultat	
	
def ParseBgpTable(File__):
	resultat=None
	
	try:
		resultat = ParseBgpTableIOS(File__).asDict()
	except pp.ParseException as e1:
		try:
			resultat=ParseBgpTableXR(File__).asDict()
		except pp.ParseException as e2:
			try:
				resultat=ParseBgpTableNxOS(File__).asDict()
			except pp.ParseException as e3:
				print('Erreur de parsing\n')
				print('Fichier:'+File__)
				print(e1)
				print(e2)
				print(e3)
				
				
	return resultat
	
class BGP(object):
	def __init__(self,output=None,dump=None):
		"Constructeur"
		self.table={}
		if output:
			self.table=ParseBgpTable(output)
			
		elif dump:
			self.load(dump)
			
	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		bgp__=None
		
		with open(filename,'rb') as file__:
			bgp__=pickle.load(file__)
		
		try:
			self.table=bgp__.table
		except:
			print('ERROR LOAD DUMP')	
			
	def affichage(self):
		for vrf in self.table.keys():
			for entry in self.table[vrf]:
				print(vrf,str(entry))
				
	def export_csv(self,fichier):
		writeCsv(self.__list__(),fichier)
		
	def __list__(self):
		result=[]
		for vrf in self.table.keys():
			for entry in self.table[vrf]:
				for nh in entry[1]:
					result.append([vrf,entry[0],nh])
		return result
			
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-o", "--output",action="store",help="Contient le fichier output")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump")
	parser.add_argument("-s", "--savefile",action="store",help="Save to dump File")
	parser.add_argument("-e", "--exportcsv",action="store",help="Résultat sous forme fichier csv",required=False)
	parser.add_argument("-P", "--Print",action="store_true",help="Affiche",required=False)
	args = parser.parse_args()
	
	
	
		
		
	if args.output:
		bgp__=BGP(output=args.output)
		
		if args.savefile:
			bgp__.save(args.savefile)
			
		if args.exportcsv:
			bgp__.export_csv(args.exportcsv)
		
		if args.Print:
			bgp__.affichage()
			
	elif args.dumpfile:
		bgp__=BGP(dump=args.dumpfile)

		
		if args.exportcsv:
			bgp__.export_csv(args.exportcsv)
			
		if args.Print:
			bgp__.affichage()
			
	
			
			
			
		