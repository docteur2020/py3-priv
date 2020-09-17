#!/usr/bin/env python3.7
# coding: utf-8

import pyparsing as pp
import pdb

def list_to_dict(liste__):
	resultat={}
	for element in liste__:
		resultat[element[0]]=element[1]
		
	return resultat

def replace(dict_parametre):
	"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
	def parseAction(s,l,t):
		resultat=t[0]
		try:
			resultat=resultat.replace(t[0],dict_parametre[t[0]])
		except KeyError as e:
			print(e)
			#pdb.set_trace()
			#print('stop')
			pass
		return resultat
		
	return parseAction
	
def ifPrint(liste_parametre):
	"Affichage conditionnel"
	def parseAction(s,l,t):
		resultat=""
		try:
			if liste_parametre[t[0]]:
				resultat=t[1]
		except KeyError as e:
			print(e)
			pass
		return resultat
		
	return parseAction
	


def ParseTemplate(Str__,param__):
	if isinstance(param__,dict):
		param=param__
	elif isinstance(param__,tuple):
		param=list_to_dict(param__)
	elif isinstance(param__,tuple):
		param=list_to_dict(param__)
	else:
		raise  ValueError("Verifiez le type de "+param__)
	CommonLine=pp.Combine(pp.OneOrMore(pp.CharsNotIn('{}<>')))
	ToReplace=(pp.Combine(pp.Literal('<').suppress()+pp.Word(pp.alphanums+'-_')+pp.Literal('>').suppress())).setParseAction(replace(param))
	ConditionalPrint=(pp.Suppress(pp.Literal('{')+pp.Literal('if'))+pp.Word(pp.alphanums+'-_')+pp.Combine(pp.OneOrMore(pp.CharsNotIn('{}'))+ pp.Suppress(pp.Literal('}')))).setParseAction(ifPrint(param))
	result_temp=ToReplace.transformString(Str__)
	
		
	return ConditionalPrint.transformString(result_temp)
	




