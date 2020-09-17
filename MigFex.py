#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import csv
import argparse
import io
import pdb
from ParsingShow  import ParseShFexString , ParsePortChannelCisco , getLongPort , getShortPort , ParseRunInterface , ParseShNextPo
from connexion import *
import re
import sys
import os
from ParseVlanListe import vlan , liste_vlans
from math import ceil
import pyparsing as pp
from cache import Cache
from sedFile import SedFile 


def writeConfig(config_str,fichier):
	
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
	return None
	
def getRunningInterface(equipment__):

	Interface=None
	
	con_get_Interface_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log","TMP","show run",timeout=300,verbose=False)
	Interface=con_get_Interface_cur.launch_withParser(ParseRunInterface)
	
		
	return Interface
	
def getFex(equipment__):

	Fex=None
	
	con_get_Fex_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shfex.log","TMP","show fex",timeout=300,verbose=False)
	
	try:
		Fex=con_get_Fex_cur.launch_withParser(ParseShFexString)
	except pp.ParseException as e:
		print(e)
		pass
	
		
	return Fex
	
def getFexNextId(fex__):

	resultat='100'
	if fex__:
		try:
			resultat=str(int(max(fex__.keys()))+1)
		except ValueError as e:
			print(e)
			print(fex__.keys()+" non pris en compte")
			pass
			
	return resultat
	
def getPortChannel(equipment__):

	Portchannels={}
	
	con_get_Portchannel_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shport_channel_summary.log","TMP","show port-channel summary",timeout=300,verbose=False)
	Portchannels__=con_get_Portchannel_cur.launch_withParser(ParsePortChannelCisco)
	
	for Portchannel__ in Portchannels__:
		Portchannels[Portchannel__[0]]=Portchannel__
		
	return Portchannels
	
	

def getInterfacePo(channel__):
	resultat={}
	for equipement_ in channel__.keys():
		resultat[equipement_]=[]
		for po__ in channel__[equipement_]:
			try:
				for int__ in  po__[3]:
					interface_cur=int__[0]
					if interface_cur not in resultat:
						resultat[equipement_].append(interface_cur)
			except KeyError:
				pass
	return resultat
	
		
def sort_dict(dict__):
	
	result={}
	sort_keys=sorted(dict__.keys())
	for key__ in sort_keys:
		result[key__]=dict__[key__]
		
	return result
	
class NextPo(object):
	
	def __init__(self,FirstPo,incr=1):
		self.Po=str(int(FirstPo)-1)
		self.incr=incr
		
	def __next__(self):
		Po_int=int(self.Po)
		Po_int+=self.incr
		
		self.Po=str(Po_int)
		
		return  self.Po
		
class NextId(object):
	
	def __init__(self,FirstId,incr=1):
		self.id=str(int(FirstId)-incr)
		self.incr=incr
		
	def __next__(self):
		id_int=int(self.id)
		id_int+=self.incr
		
		self.id=str(id_int)
		
		return  self.id
	
def extract_po_fex(config__):
	resultat=[]
	for interface__ in config__.keys():
		if re.search('Ethernet1[0-9][0-9]/[0-9]/[0-9]',interface__):
			print(interface__)
			try:
				for entry in config__[interface__]:
					if re.search('channel-group',entry):
						PoId_cur=entry.split()[1]
						if PoId_cur not in resultat:
							resultat.append(PoId_cur)
						
			except TypeError:
				pass
		
	resultat.sort(key=int)
					
	return resultat
	
def extract_int_fex(config__,Fex_src):
	resultat=[]
	liste_fex=list(Fex_src.keys())
	for interface__ in config__.keys():
		if re.search('Ethernet1[0-9][0-9]/[0-9]/[0-9]',interface__):
			if getFexIdFromIf(interface__)[0] in liste_fex:
				resultat.append(interface__)
						
	return resultat
	
def getFexIdFromIf(interface__):

	resultat__pp=None
	Interface=pp.Suppress(pp.Literal('interface')+pp.Literal('Ethernet'))+pp.Word(pp.nums,exact=3)+pp.Suppress(pp.Literal('/')+pp.Word(pp.nums)+pp.Literal('/'))+pp.Word(pp.nums)
	
	try:
		resultat__pp=Interface.parseString(interface__).asList()
		
	except pp.ParseException:
		pass
		
	return resultat__pp
	
	
def getNewConfFex(config__,fex__int,iterId,dictPo__,dictFexId,regex=None):
	resultat=io.StringIO()
	liste_fex_id_done=[]
	dict_fex_id_new={}

	for if__ in fex__int:
		if regex:
			if not re.search(regex,if__):
				continue
		info_id_old_cur=getFexIdFromIf(if__)
		if info_id_old_cur:
			try:
				fex_id_old_cur=info_id_old_cur[0]
				port_id_cur=info_id_old_cur[1]
			except KeyError:
				fex_id_old_cur=""
				#pdb.set_trace()
			if fex_id_old_cur not in liste_fex_id_done and fex_id_old_cur:
				if not regex:
					liste_fex_id_done.append(fex_id_old_cur)
					dict_fex_id_new[fex_id_old_cur]=next(iterId)
				else:
					if re.search(regex,fex_id_old_cur):
						liste_fex_id_done.append(fex_id_old_cur)
						dict_fex_id_new[fex_id_old_cur]=next(iterId)
				
			new_interface='interface Ethernet'+dict_fex_id_new[fex_id_old_cur]+'/1/'+port_id_cur
			resultat.write(new_interface+'\n')
			try:
				for entry in config__[if__]:
					if not re.search('\ channel-group\ ',entry):
						resultat.write(entry.rstrip()+'\n')
					else:
						PoId_cur=entry.split()[1]
						resultat.write(entry.replace(PoId_cur,dictPo__[PoId_cur]).rstrip()+'\n')
			except KeyError:
				pdb.set_trace()
			except TypeError:
				pass

	#dictFexId=dict_fex_id_new.copy()
	
	for key in dict_fex_id_new:
		dictFexId[key]=dict_fex_id_new[key]
	
	return resultat.getvalue()
	
def getNewConfPo(config__,po__int,PoId,PoDict_src,regex=""):
	resultat=resultat=io.StringIO()
	dict_po_id_new={}
	
	
	for po__id in po__int:
		if regex:
			if not re.search(regex,PoDict_src[po__id][3][0][0]):
				continue
		dict_po_id_new[po__id]=next(PoId)				
		new_interface='interface port-channel'+dict_po_id_new[po__id]
		resultat.write(new_interface+'\n')
		try:
			for entry in config__['interface port-channel'+po__id]:
				if not re.search('\ vpc\ ',entry):
					resultat.write(entry.rstrip()+'\n')
				else:
					resultat.write('  vpc '+dict_po_id_new[po__id]+'\n')
		except KeyError:
			pdb.set_trace()
		except TypeError:
			pass
			
	dict_po_id_new
	

	return [resultat.getvalue(),dict_po_id_new]
				
def getFirstPo(equipment__):

        PoID=None

        con_get_NextPo_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+"_shNextPo_"+equipment__.lower()+".log","TMP","shNextPo",timeout=300,verbose=False)
        PoID=con_get_NextPo_cur.launch_withParser(ParseShNextPo)
        # try:
        #       con_get_NextPo_cur=connexion(equipement(equipement__),None,None,None,'SSH',"TMP/"+"_shNextPo_"+equipement__.lower()+".log","TMP","shNextPo",timeout=300,verbose=False)
        #       PoID=con_get_NextPo_cur.launch_withParser(ParseShNextPo)
        # except Exception as e:
        #       print("Erreur Connexion...")
        #       print((str(e)))
        #       sys.exit(2)

        return PoID
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-s","--src",action="store",help="Equipement Source",required=True)
	parser.add_argument("-c","--cible",action="store",help="Equipement Cible",required=True)
	parser.add_argument("-r","--resultat",action="store",help="Fichier Contenant le resultat",required=True)
	parser.add_argument("-p","--poid",action="store",help="Premier po id",required=False)
	parser.add_argument("--incr",action="store",default=1,type=int,help="increment",required=False)
	parser.add_argument("--fexid",action="store",type=int,help="Premier Fex id",required=False)
	parser.add_argument("--regex",action="store",default=None,help="Sélection de fex",required=False)
	parser.add_argument("--saveinfo",action="store_true",default=None,help="Enregistrement des données",required=False)
	parser.add_argument("--split-conf",dest='splitconf',action="store_true",default=None,help="split les config par fex",required=False)
	parser.add_argument("--replace",dest='replace',action="store",default=None,help="replacement type SedFile",required=False)
	args = parser.parse_args()
	
			

	Pos__={}
	ConfigInt__={}
	Fex__src={}
	Fex__dst={}
	dictPoId={}
	dictFexId={}
	
	print("Recuperation des informations des fex")
	Fex__src=getFex(args.src)
	
	Fex__dst=getFex(args.cible)
	
	print([Fex__src,Fex__dst])
	
	if not args.fexid:
		NewFexId=NextId(getFexNextId(Fex__dst),args.incr)
	else:
		NewFexId=NextId(args.fexid,args.incr)
	
	#pdb.set_trace()
	
	print("Recuperation des configurations des interfaces")
	ConfigInt__=getRunningInterface(args.src)
	
	po_fex=extract_po_fex(ConfigInt__)
	int_fex=extract_int_fex(ConfigInt__,Fex__src)

	print("Recuperation des port-channel")
	
	Channels=getPortChannel(args.src)
	
	if args.poid:
		NewPoId=NextPo(args.poid)
	else:
		print("Recuperation du premier PoID libre")
		NewPoId=NextPo(getFirstPo(args.cible)['Non_VPC_Po_to_Servers'])
		
	if not NewPoId:
		NewPoId=NextPo('500')
		
	[ NewConfigPo,dictPoId] =getNewConfPo(ConfigInt__,po_fex,NewPoId,Channels,args.regex)
	
	NewConfigFex=getNewConfFex(ConfigInt__,int_fex,NewFexId,dictPoId,dictFexId,regex=args.regex)
	
	if args.saveinfo:
		tag="MIGFEX_"+args.src.upper()+'_'+args.cible.upper()
		info={ "source":args.src,
			   "destination":args.cible,
			   "po":dictPoId,
			   "fex":dictFexId }
			   
		fexCache=Cache(tag,initValue=info)
		
	
	print(NewConfigPo)
	
	print("Sauvegarde du fichier de configuration")
	
	if not args.replace:
		writeConfig(NewConfigPo+'\n'+NewConfigFex,args.resultat)
	else:
		Sed=SedFile(args.replace)
		filtered=filter(lambda x: not x.isspace(),(Sed.replace(NewConfigPo+'\n!\n!'+NewConfigFex)).split('\n'))
		writeConfig("\n".join(filtered),args.resultat)
	
	
	





	