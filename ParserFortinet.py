#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import pyparsing as pp
import argparse
from pprint import pprint as ppr
import pdb

def ParseFortigateAddr(str__,mode='str'):
	'''Scan Addr Grpoupe'''
	
	result=None
	head_global=pp.LineStart()+pp.Keyword('config global')
	head_address=(pp.LineStart()+pp.Keyword('config firewall address'))
	Quote=pp.Suppress(pp.Literal('"'))
	ObjName=Quote+pp.Word(pp.alphanums+'_-. \/()=[]:{},?')+Quote
	GrpAddr=pp.Literal('edit').suppress()+ObjName
	Vdom=(pp.Literal('config vdom')+pp.Literal('edit')).suppress()+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))
	End=pp.Suppress(pp.SkipTo(pp.Literal('end'),include=True))
	EndOfConfig=pp.Suppress((pp.LineStart()+pp.Keyword('end'))*2)
	Next=pp.Suppress(pp.Keyword('next'))
	AttributGrpAddr=pp.dictOf(pp.Literal('set').suppress()+pp.Word(pp.alphanums+'-_:[]{}.'),pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n'))))
	BlocAddr=pp.dictOf(GrpAddr,AttributGrpAddr+Next)
	SectionConfigAddr=pp.Suppress(pp.SkipTo(head_global)+head_global)+pp.dictOf(pp.Suppress(pp.SkipTo(Vdom))+Vdom,pp.Suppress(pp.SkipTo(head_address,failOn=Vdom|EndOfConfig))+pp.Optional(head_address.suppress()+BlocAddr+End,default={}))
	
	if mode=='str':
		result=SectionConfigAddr.parseString(str__)
	elif mode=='file':
		result=SectionConfigAddr.parseFile(str__)
		
	return result.asDict()
	
def ParseFortigateGrpAddr(str__,mode='str'):
	'''Scan Addr Grpoupe'''
	
	result=None
	head_global=pp.LineStart()+pp.Keyword('config global')
	head_grpAddr=(pp.LineStart()+pp.Keyword('config firewall addrgrp'))
	Quote=pp.Suppress(pp.Literal('"'))
	ObjName=Quote+pp.Word(pp.alphanums+'_-. \/()=[]:{},')+Quote
	ObjName2=Quote+pp.Combine(pp.OneOrMore(pp.CharsNotIn('"')))+Quote
	ClassicAttr=pp.Word(pp.alphanums+'-')
	GrpAddr=pp.Literal('edit').suppress()+ObjName2
	Vdom=(pp.Literal('config vdom')+pp.Literal('edit')).suppress()+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))
	End=pp.Suppress(pp.SkipTo(pp.Literal('end'),include=True))
	EndOfConfig=pp.Suppress((pp.LineStart()+pp.Keyword('end'))*2)
	Next=pp.Suppress(pp.Keyword('next'))
	AttributGrpAddr=pp.dictOf(pp.Literal('set').suppress()+pp.Word(pp.alphanums+'-_:[]{}.'),  pp.MatchFirst( [ pp.Group(pp.OneOrMore(ObjName)), ClassicAttr , pp.Group(pp.OneOrMore(ObjName2)) ] ) )
	BlocGrpAddr=pp.dictOf(GrpAddr,AttributGrpAddr+Next)
	SectionConfigAddr=pp.Suppress(pp.SkipTo(head_global)+head_global)+pp.dictOf(pp.Suppress(pp.SkipTo(Vdom))+Vdom,pp.Suppress(pp.SkipTo(head_grpAddr,failOn=Vdom|EndOfConfig))+pp.Optional(head_grpAddr.suppress()+BlocGrpAddr+End,default={}))
	
	if mode=='str':
		result=SectionConfigAddr.parseString(str__)
	elif mode=='file':
		result=SectionConfigAddr.parseFile(str__)
		
	return result.asDict()

def ParseFortigateRule(str__,mode='str'):
	'''Scan Addr Groupe'''
	result=None
	head_global=pp.LineStart()+pp.Keyword('config global')
	head_policy=(pp.LineStart()+pp.Keyword('config firewall policy'))
	GrpRule=pp.Literal('edit').suppress()+pp.Word(pp.nums)
	Vdom=(pp.Literal('config vdom')+pp.Literal('edit')).suppress()+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))
	End=pp.Suppress(pp.SkipTo(pp.Literal('end'),include=True))
	EndOfConfig=pp.Suppress((pp.LineStart()+pp.Keyword('end'))*2)
	Next=pp.Suppress(pp.Keyword('next'))
	Quote=pp.Suppress(pp.Literal('"'))
	ObjName=Quote+pp.Word(pp.alphanums+'_-. \/()=[]:{},'+'\n'+'\r')+Quote
	ObjName2=Quote+pp.Combine(pp.OneOrMore(pp.CharsNotIn('"')))+Quote
	ClassicAttr=pp.Word(pp.alphanums+'-')
	AttributRule=pp.dictOf(pp.Literal('set').suppress()+pp.Word(pp.alphanums+'-_:[]{}.'),  pp.MatchFirst( [ pp.Group(pp.OneOrMore(ObjName2)),pp.Group(pp.OneOrMore(ObjName)), ClassicAttr  ] ) )
	BlocRule=pp.dictOf(GrpRule,AttributRule+Next)
	SectionConfigRule=pp.Suppress(pp.SkipTo(head_global)+head_global)+pp.dictOf(pp.Suppress(pp.SkipTo(Vdom))+Vdom,pp.Suppress(pp.SkipTo(head_policy,failOn=Vdom|EndOfConfig))+pp.Optional(head_policy.suppress()+BlocRule+End,default={}))
	
	
	if mode=='str':
		result=SectionConfigRule.parseString(str__)
	elif mode=='file':
		result=SectionConfigRule.parseFile(str__)

	return result.asDict()
	
def ParseFortigateStaticRoute(str__,mode='str'):
	'''Scan Addr Groupe'''
	result=None
	head_global=pp.LineStart()+pp.Keyword('config global')
	head_route=(pp.LineStart()+pp.Keyword('config router static'))
	GrpRoute=pp.Literal('edit').suppress()+pp.Word(pp.nums)
	Vdom=(pp.Literal('config vdom')+pp.Literal('edit')).suppress()+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))
	End=pp.Suppress(pp.SkipTo(pp.Literal('end'),include=True))
	EndOfConfig=pp.Suppress((pp.LineStart()+pp.Keyword('end'))*2)
	Next=pp.Suppress(pp.Keyword('next'))
	Quote=pp.Suppress(pp.Literal('"'))
	ObjName=Quote+pp.Word(pp.alphanums+'_-. \/()=[]:{},'+'\n'+'\r')+Quote
	ObjName2=Quote+pp.Combine(pp.OneOrMore(pp.CharsNotIn('"')))+Quote
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	ClassicAttr=pp.Word(pp.alphanums+'-')
	AttributRoute=pp.dictOf(pp.Literal('set').suppress()+pp.Word(pp.alphanums+'-_:[]{}.'),  pp.MatchFirst( [ pp.OneOrMore(ipAddress),pp.Group(pp.OneOrMore(ObjName2)),pp.Group(pp.OneOrMore(ObjName)), ClassicAttr  ] ) )
	BlocRoute=pp.dictOf(GrpRoute,AttributRoute+Next)
	SectionConfigRule=pp.Suppress(pp.SkipTo(head_global)+head_global)+pp.dictOf(pp.Suppress(pp.SkipTo(Vdom))+Vdom,pp.Suppress(pp.SkipTo(head_route,failOn=Vdom|EndOfConfig))+pp.Optional(head_route.suppress()+BlocRoute+End,default={}))
	
	
	if mode=='str':
		result=SectionConfigRule.parseString(str__)
	elif mode=='file':
		result=SectionConfigRule.parseFile(str__)

	return result.asDict()
	
if __name__ == '__main__':
	"main function"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--file",action="store",help=u"Fortigate File config to parse",required=True)
	args = parser.parse_args()
	
	
	
	Addr=ParseFortigateAddr(args.file,mode='file')
	
		
	ppr(Addr)
	
	GrpAddr=ParseFortigateGrpAddr(args.file,mode='file')
	
	ppr(GrpAddr,width=1000)
	
	Rule=ParseFortigateRule(args.file,mode='file')
	
	
	ppr(Rule,width=1000)
	
	Route=ParseFortigateStaticRoute(args.file,mode='file')
	ppr(Route,width=1000)
	
	
	print('FIN')

	