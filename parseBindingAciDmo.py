#!/bin/python3.7
# coding: utf-8

import sys
import argparse
import pdb
import pyparsing as pp
import cache as cc 

def parseFileBinding(file):
	resultat=None
	Site=pp.Suppress(pp.Literal("Bindings on site")+pp.OneOrMore(pp.CharsNotIn('\n')))
	Ligne=pp.Literal('====')+pp.OneOrMore(pp.CharsNotIn('\n'))
	
	Vlan=pp.Combine(pp.Literal("Bindings for Vlan: ").suppress()+pp.Word(pp.nums)+pp.Literal('.').suppress())
	Node=pp.Combine(pp.Literal("- topology/pod-1/paths-").setParseAction(pp.replaceWith('Node'))+pp.Word(pp.nums,exact=3))
	NodeVPC=pp.Combine((pp.Literal("- topology/pod-1/protpaths-")).setParseAction(pp.replaceWith('Node'))+pp.Word(pp.nums,exact=3)+pp.Literal('-')+pp.Word(pp.nums,exact=3))
	Interface=pp.Combine(pp.Literal("/pathep-[").suppress()+pp.Literal("eth")+pp.Word(pp.nums+'/')+pp.Suppress(pp.Literal(']'))+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n'))))
	None__=pp.Literal('None').setParseAction(pp.replaceWith(None))
	VPC=pp.Combine(pp.Literal("/pathep-[").suppress()+pp.Word(pp.alphanums+'_-')+pp.Suppress(pp.Literal(']'))+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n'))))
	binding=Site+Ligne+pp.dictOf(Vlan,pp.MatchFirst([None__,pp.Group(pp.OneOrMore( pp.Group((Node|NodeVPC)+(Interface|VPC)) ))] ) )
	
	resultat=binding.parseFile(file,parseAll=True)

	
	return resultat.asDict()
	
def BindingbyInterface(bind_dict):
	resultat={}
	for Vlan in bind_dict:
		if bind_dict[Vlan]:
			for interface in bind_dict[Vlan]:
				EntryCur=bind_dict[Vlan]
				NodeCur=interface[0]
				interfaceCur=interface[1]
				
				if NodeCur=='N':
					pdb.set_trace()
				
				if NodeCur in resultat.keys():
					if interfaceCur in resultat[NodeCur].keys():
						resultat[NodeCur][interfaceCur].append(Vlan)
					else:
						resultat[NodeCur][interfaceCur]=[Vlan]
				else:
					resultat[NodeCur]={}
					resultat[NodeCur][interfaceCur]=[Vlan]
				
	return resultat

if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file')
	parser.add_argument("-t","--tag", action="store",help="tag du cache",required=False)
	args = parser.parse_args()
	
	bindind_raw=parseFileBinding(args.file)
	#print(bindind_raw)
	bindind_parsed=BindingbyInterface(bindind_raw)
	print(str(bindind_parsed))
	
	if args.tag:
		cc.Cache(args.tag,initValue=bindind_parsed)
	