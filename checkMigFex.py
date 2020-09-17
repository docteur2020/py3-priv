#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


from ParsingShow import ParsePortChannelCisco , ParseStatusCisco , ParseSwitchPortString , parseShIntFex 
import cache as cc
from connexion import *

from dictdiffer import diff
import pyparsing as pp
import argparse
from pprint import pprint
import pdb
import ntpath
import re
import sys
from dictdiffer import diff

import os.path, time
import diffIntStatus
import diffIntSwitchport
import diffPortchannel



COMMANDES={ 'PORT-CHANNEL':{ 'commandes':'sh port-channel summary' , 'parser':ParsePortChannelCisco} , 'STATUS':{ 'commandes':'sh interface status' , 'parser':ParseStatusCisco} ,'SWITCHPORT':{ 'commandes':'sh interface switchport' , 'parser':ParseSwitchPortString},'INTERFACE-FEX':{ 'commandes':'sh interface fex-fabric' , 'parser':parseShIntFex}}
PATH_CACHE='/home/x112097/TMP/CACHE/'

	
class ResultCommande(object):
	
	def __init__(self,equipement,action,options=None,type=""):
		self.resultat=None
		if action not in COMMANDES.keys():
			raise ValueError('Action non supportée\nLes actions supportés sont:'+ "\n - ".join([ com for com in COMMANDES.keys()]) )
			
		self.equipement=equipement
		self.action=action
		self.tag="CHECK_MIG_FEX_"+equipement.upper()+'_'+action
		self.cacheCmd=cc.Cache(self.tag)
		self.type=type
		if not options:
			if self.cacheCmd.isOK():
				self.resultat=self.cacheCmd.load()
			else:
				print( "Pas de cache pour l'action %s pour l'équipement %s" % (self.action,self.equipement) )
				self.resultat=self.getCommande(equipement,COMMANDES[action]['commandes'],COMMANDES[action]['parser'])
				self.cacheCmd.save(self.resultat)
		elif options:
			if not options.renew:
				if self.cacheCmd.isOK():
					self.resultat=self.cacheCmd.load()
				else:
					print( "Pas de cache pour l'action %s pour l'équipement %s" % (self.action,self.equipement) )
					self.resultat=self.getCommande(equipement,COMMANDES[action]['commandes'],COMMANDES[action]['parser'])
					self.cacheCmd.save(self.resultat)
			else:
				if (options.onlysource and self.type=="source") or (options.onlydest and self.type=="destination") or not self.type:
					print( "Le cache ne sera pas utilisé: %s %s"  % (self.action,self.equipement) )
					self.resultat=self.getCommande(equipement,COMMANDES[action]['commandes'],COMMANDES[action]['parser'])
					self.cacheCmd.save(self.resultat)
				else:
					if self.cacheCmd.isOK():
						self.resultat=self.cacheCmd.load()
					else:
						print( "Pas de cache pour l'action %s pour l'équipement %s" % (self.action,self.equipement) )
						self.resultat=self.getCommande(equipement,COMMANDES[action]['commandes'],COMMANDES[action]['parser'])
						self.cacheCmd.save(self.resultat)

					
		else:
			raise ValueError("options non prise en charge")
			
	@staticmethod
	def getCommande(equipment__,commandes,parserCisco):
		Result=None
		
		commandes_str=commandes.strip().replace(' ','_').replace("\\",'_').replace("/",'_')
		suffixe="_"+commandes_str+".log"
		con_get__cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+suffixe,"TMP",commandes,timeout=300,verbose=False)
		Result=con_get__cur.launch_withParser(parserCisco)
	
		return Result
	
	def getValue(self):
		return self.resultat
	
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-s", "--source",action="store",help="fex source",required=True)
	parser.add_argument("-d","--destination", action="store",help="fex destination",required=True)
	parser.add_argument("-e", "--etape", action="store",help="fex migré",required=True)
	parser.add_argument("--renew", action="store_true",help="récupére les logs sur le n5k source",required=False)
	parser.add_argument("--onlysource", action="store_true",help="renouvelle que les logs sources",required=False)
	parser.add_argument("--onlydest", action="store_true",help="renouvelle que les logs destinations",required=False)
	args = parser.parse_args()
	
	Channel__cible=ResultCommande(args.source,'PORT-CHANNEL',args,"source")
	Status__cible=ResultCommande(args.source,'STATUS',args,"source")
	Switchport__cible=ResultCommande(args.source,'SWITCHPORT',args,"source")
	
	Channel__dst=ResultCommande(args.destination,'PORT-CHANNEL',args,"destination")
	Status__dst=ResultCommande(args.destination,'STATUS',args,"destination")
	Switchport__dst=ResultCommande(args.destination,'SWITCHPORT',args,"destination")
	
	print("Test des port-channel")
	
	try:
		tagMigFex="MIGFEX_"+args.source.upper()+"_"+args.destination
		infoMigCache=cc.Cache(tagMigFex)
		infoMig=infoMigCache.load()
	except ValueError as e:
		print(e)
		print("Lancer le script MigFex pour récupérer les informations de migrations avec l'option saveinfo ")
		print(" ;) il fallait y penser avant")
	
	pprint(infoMig)
	
	#pprint(Channel__cible.getValue())
	#pprint(Status__cible.getValue())
	#pprint(Switchport__cible.getValue())
	#
	#pprint(Channel__dst.getValue())
	#pprint(Status__dst.getValue())
	#pprint(Switchport__dst.getValue())
	
	idFexSrc=args.etape
	try:
		idFexDst=infoMig['fex'][idFexSrc]
	except KeyError as e:
		print(e)
		print("Vérifier les informatiosn de migrations")
		
	
	print("Vérification des interface STATUS:")	
	diff_status=diff(diffIntStatus.filter_info(Status__cible.getValue(),filter=idFexSrc,replace='s/'+idFexSrc+'/'+idFexDst+'/'),diffIntStatus.filter_info(Status__dst.getValue(),filter=idFexDst))
	pprint(diffIntStatus.print_diff(diff_status))
	
	print("Vérification des interface Switchport:")	
	diff_switchport=diff(diffIntSwitchport.filter_info(Switchport__cible.getValue(),filter=idFexSrc,replace='s/'+idFexSrc+'/'+idFexDst+'/'),diffIntSwitchport.filter_info(Switchport__dst.getValue(),filter=idFexDst))
	pprint(diffIntSwitchport.print_diff(diff_switchport))

	
	print("Vérification des interface port-channel:")	
	diff_channel=diff(diffPortchannel.filter_info(Channel__cible.getValue(),filter=idFexSrc,infoMig=infoMigCache),diffPortchannel.filter_info(Channel__dst.getValue(),filter=idFexDst))
	pprint(diffPortchannel.print_diff(diff_channel))