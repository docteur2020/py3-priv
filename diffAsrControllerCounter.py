#!/bin/python3.7
# coding: utf-8

import sys
import argparse
import pdb
import pyparsing as pp
from pprint import pprint as ppr


WIDTH=100

def getDiffCounter(result1,result2):
	ResultDiff={}
	
	for offset in result1:
		for counter in result1[offset]:
			try:
				counterFrame1=int(result1[offset][counter][0])
				counterRate1=int(result1[offset][counter][1])
				counterFrame2=int(result2[offset][counter][0])
				counterRate2=int(result2[offset][counter][0])
				ResultDiff[offset]={counter: [counterFrame2-counterFrame1,counterRate2-counterRate1]}
			except KeyError as E:
				print(E)
				ResultDiff[offset]={counter: ['Error','Error']}
				
	return ResultDiff

def parseControllerCounter(File__):
	Resultat=None
	Offset=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <100000 )
	CounterName=pp.Word(pp.nums+'_'+pp.alphas.upper())
	FrameValue=pp.Word(pp.nums)
	Rate=pp.Word(pp.nums)
	AllEntry=pp.dictOf(Offset,pp.dictOf(CounterName,pp.Group(FrameValue+Rate)))
	Header=pp.Suppress(pp.Literal('Offset')+ pp.Literal('Counter')+pp.Literal('FrameValue')  +pp.Literal('Rate') + pp.OneOrMore(pp.CharsNotIn('\n')))
	Limit=pp.Suppress(pp.Word('-')+pp.LineEnd())
	AllHeader=Header+Limit
	AllLog=pp.Suppress(pp.SkipTo(AllHeader,include=True))+AllEntry
	Resultat=AllLog.parseFile(File__)
	
	return Resultat.asDict()

if __name__ == '__main__':
	"main function"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--file", dest='file',action="store",help=u"file output 1",required=True)
	parser.add_argument("--other", dest='other',action="store",help=u"file output 2 to make diff",required=False)
	
	
	args = parser.parse_args()
	
	Resultat=parseControllerCounter(args.file)
	
	if args.other:
		Other=parseControllerCounter(args.other)
		Diff=getDiffCounter(Resultat,Other)
		ppr(Diff,width=WIDTH)
	if args.file and not args.other:
		ppr(Resultat,width=WIDTH)
	

	
	