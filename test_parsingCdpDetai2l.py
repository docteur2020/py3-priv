#!/usr/bin/env python3.7
# coding: utf-8

import pyparsing as pp
import argparse
import pdb
import re

def ParseCdpNeighborDetail(File__):
	Resultat={}
	Limitation=pp.Suppress(pp.lineStart+pp.Literal('----------')+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	DeviceID=(pp.Literal('Device ID').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'-_().')).setParseAction(lambda s,l,t : re.split('\.|\(',t[0])[0].upper()).setResultsName('Neighbor')
	Interface=(pp.Literal('Interface').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'/')).setResultsName('Interface')
	Virgule=pp.Literal(',').suppress()
	InterfaceNeigh=(Virgule+pp.Literal('Port ID (outgoing port)').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'/')).setResultsName('Interface Neighbor')
	
	EntryCDP=Limitation+DeviceID+pp.SkipTo(Interface).suppress()+Interface+InterfaceNeigh

	with open(File__,'r') as fich__:	
		file_str=fich__.read()
	
	temp_list=[]
	for parsingCDPEntry in EntryCDP.scanString(file_str):
		temp_list.append(parsingCDPEntry[0].asDict())
		
	print(temp_list)
		
	for cdp__ in temp_list:
		Resultat[cdp__['Interface'][0]]={'Neighbor': cdp__['Neighbor'] , 'Interface Neighbor': cdp__['Interface Neighbor']}
	
		
	return Resultat
	
def setToDict(string,location,token):
	return None
	
if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--file",action="store",help=u"Fichier",required=True)
	args = parser.parse_args()
	
	resultat=ParseCdpNeighborDetail(args.file)
	
	
	
	print(resultat)