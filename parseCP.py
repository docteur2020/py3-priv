#!/usr/bin/env python3.7
# coding: utf-8

import pyparsing as pp
import argparse
import codecs
import pdb
import re

def parseCheckpointOjbC(File__="",Str__=""):

	resultat=None
	
	Entry=expr=pp.Forward()
	GroupObject=pp.Forward()
	
	LParenthese, RParenthese= map(pp.Suppress, "()")
	Value=pp.OneOrMore(pp.CharsNotIn('()')).setParseAction(lambda t : re.sub('\s+', ' ',t[0].replace(':','').replace('\t',' ').replace('\n',' ').strip()) )
	Key=pp.Literal(':').suppress()+pp.Word(pp.alphanums+'-_')
	Entry<<( Value | pp.Group(GroupObject)
	Object= ( Key + LParenthese+ (Entry) + RParenthese )
	
	
	expr=pp.Forward()
	
	#Value= pp.OneOrMore( (pp.Word(pp.alphanums+":-_", excludeChars="()")  ).setParseAction(lambda t : t[0].replace(':','').replace('\t',' ').replace('\n',' ')) )
	#re.sub('\s+', ' ', mystring).strip()
	Value=pp.OneOrMore(pp.CharsNotIn('()')).setParseAction(lambda t : re.sub('\s+', ' ',t[0].replace(':','').replace('\t',' ').replace('\n',' ').strip()) )
	Key=pp.Literal(':').suppress()+pp.Word(pp.alphanums+'-_')
	expr <<  LParenthese+ pp.Optional(Entry) + RParenthese )

	def parseAction(string, location, tokens):
		return { tokens[0] : tokens[1:]}

	expr.setParseAction(parseAction)
	
	all_expr=LParenthese+pp.dictOf( Key , expr) + RParenthese
	
	if File__:
		resultat=all_expr.parseFile(File__)
	elif Str__:
		resultat=all_expr.parseString(Str__)
	
	return resultat.asDict()
	
	


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--objectc", action="store",help="Checkpoint object.c",required=True)
	parser.add_argument("-s", "--save", action="store",help="Fichier de commandes",required=False)
	args = parser.parse_args()
	
	testdata = """
(
	:anyobj (Any
		:color (Blue)
	)
	:superanyobj (
		: (Any
			:color (Blue)
		)
	)
	:serverobj (serverobj)
	:translations (translations)
	:servgen ()
	:log-props ()
)
	"""
	
	testdata2="""
	(
		:stateact (
		:comanndotinst2inst (tryrtytry)
		:commandnotinst2dis (fgdgfd)
		:commandins2notinst (statuslert)
		:commandinst2dis (status_alert)
		:commanddis2inst ()
		:commandis2notinst ()
	)
	"""

	if args.objectc:
		object_str=codecs.open(args.objectc, 'r', 'iso-8859-1').read()
		#resultat= parseCheckpointOjbC(Str__=object_str)
		resultat= parseCheckpointOjbC(Str__=testdata)
		print(resultat)