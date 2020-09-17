#!/usr/bin/env python3.7
# coding: utf-8

import pyparsing as pp
import argparse
import pdb

def ParseCdpNeighborDetail(File__):
	Resultat=[]
	Limitation=pp.Suppress(pp.lineStart+pp.Literal('----------')+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Label_str=['Platform','Port ID (outgoing port)','Holdtime','Version','Advertisement Version','Native VLAN','Duplex','Mgmt address(es)','System Name','MTU','Physical Location','advertisement version','Entry address(es)','Capabilities']
	Mgnt=pp.Literal('Management address(es)')+pp.Literal(':').suppress()+pp.Optional(pp.OneOrMore(pp.CharsNotIn('\n')),default='None')
	VTP=pp.MatchFirst([pp.Literal('VTP Management Domain Name'),pp.Literal('VTP Management Domain')])+pp.Literal(':').suppress()+pp.Optional(pp.OneOrMore(pp.CharsNotIn('\n')),default='None')
	Interface=pp.MatchFirst([pp.Literal('Interface address(es)'),pp.Literal('Interface')])+pp.Literal(':').suppress()+pp.Optional(pp.OneOrMore(pp.CharsNotIn('\n')),default='None')
	Spec=Mgnt|VTP|Interface
	LabelClassique=pp.Literal('Device ID')+pp.Suppress(':')
	for label in Label_str:
		LabelClassique=LabelClassique|(pp.Literal(label)+ pp.Suppress(':'))
		
	Label=LabelClassique
	attr_value = (pp.OneOrMore(pp.Word(pp.printables), stopOn=Label|Limitation|hostname|Spec).setParseAction(' '.join))

	BlocEquipement=pp.dictOf(Label,attr_value)
	
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingEntry in BlocEquipement.scanString(file_str):
			temp_list=parsingEntry[0].asDict()
			pdb.set_trace()
			try:
				if temp_list:
					Resultat.append(temp_list[0])
					pdb.set_trace()
			except IndexError:
				pass
				
	return Resultat
	
def setToDict(string,location,token):
	return None
	
if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--file",action="store",help=u"Fichier",required=True)
	args = parser.parse_args()
	
	resultat=ParseCdpNeighborDetail(args.file)
	
	
	
	print(resultat)