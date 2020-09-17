#!/usr/bin/env python3.7
# -*- coding: utf-8 -*- 

from __future__ import unicode_literals


import argparse
from ipcalc import Network , IP
import pyparsing as pp
import glob
import pdb
import json

class IpError(Exception):
	"Classe Exception pour IP/Network"
	
	def __init__(self,code=0,value1=None,value2=None):
		"Constructeur"
		self.message={}
		
		self.message[0]=u'Erreur inconnue ou non traitee'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un reseau IPV4 valide'
		self.message[3]=u'La valeur:'+value1+u' n\'est pas un NextHop BGP valide'
		super(IpError, self).__init__(self.message[code])
		
class NH(object):
	"Classe NextHop"
	
	def __init__(self,str_IP):
		"Constructeur"
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		suffixe=pp.Group(pp.ZeroOrMore(pp.Literal(':').suppress())+pp.ZeroOrMore(pp.Literal('r'))+pp.ZeroOrMore(pp.Literal('*'))+pp.ZeroOrMore(pp.Literal('>'))+pp.ZeroOrMore(pp.Literal('i')))
		NextHop=ipAddress+pp.Optional(suffixe)
		self.value=[]
		try:
			#pdb.set_trace()
			self.value=NextHop.parseString(str_IP).asList()
		except:
			raise IpError(code=3,value1=str_IP)
	
	def __str__(self):
		"Affichage"
		return str(self.value)
		
	def __ne__(self,other):
		return self.value[0] != other[0]
			
	def __eq__(self,other):
		return self.value[0] == other[0]
			
	def is_eBGP(self):
		result=True
		
		if 'i' in self.value[1]:
			result=False
			
		return result
		
		
class prefix(object):
	"definit un prefix BGP"
	
	def __init__(self,reseau="0.0.0.0",nexthops=[]):
		"Constructeur"
		try:
			self.reseau=Network(reseau)
		except:
			raise IpError(code=2,value1=reseau)
		
		self.nexthops=[]		
		for nexthop in nexthops:
			NH_cur=NH(nexthop)
			self.nexthops.append(NH_cur)
			#print(NH_cur)
	
	def __str__(self):
		"Affichage"
		resultat="P:"+str(self.reseau)+":"
		for NH__ in self.nexthops:
			resultat=resultat+"NH:"+str(NH__)+";"
		
		return resultat

class PE(object):
	"definit un PE"
	def __init__(self,nom,Vrfs=[],Prefixs={}):
		"Constructeur"
		self.nom=nom
		self.Vrfs=Vrfs
		self.Prefixs=Prefixs
		self.Prefixs_dict={}
	
	def __str__(self):
		prefix_str=""
		for Vrf__ in self.Prefixs.keys():
			prefix_str=prefix_str+Vrf__+":"
			for prefix__ in self.Prefixs[Vrf__]:
				prefix_str=prefix_str+str(prefix__)
			prefix_str=prefix_str+'\n'	
			
		return(self.nom+":"+prefix_str)
		
	def addVrf(self,Vrf):
		if Vrf not in self.Vrfs:
			self.Vrfs.append(Vrf)
			
	def addPrefix(self,Vrf,Prefix):
		#pdb.set_trace()
		try:
			self.Prefixs[Vrf].append(Prefix)

		except KeyError:
			self.Prefixs[Vrf]=[]
			self.Prefixs[Vrf].append(Prefix)
			
		try:
			self.Prefixs_dict[Vrf][str(Prefix.reseau)]=Prefix.nexthops
		except KeyError:
			self.Prefixs_dict[Vrf]={}
			self.Prefixs_dict[Vrf][str(Prefix.reseau)]=Prefix.nexthops
			
	def getNH(self,vrf__,nexthop__):
		result=None
		try:
			result=self.Prefixs_dict[vrf__][nexthop__]
		except KeyError:
			result=None
			
		return result
			
		
		
def getPEVrf(str):
	resultat=None
	NomFile=pp.Word(pp.alphanums+'_-')+pp.Literal('[').suppress()+pp.Word(pp.alphanums+'_-')+pp.Literal('].csv').suppress()
	
	resultat=NomFile.parseString(str).asList()
	
	return resultat
	

class MAN(object):
	"definit un ensemble de PE"
	
	def __init__(self,nom_repertoire):
		"instancie les objets PE depuis un repertoire contenant les fichiers BGP Entry csv format Dmo"
		self.PEs_str=[]
		self.PEs={}
		self.Prefixs_str={}
		
		Liste_file_csv=glob.glob(nom_repertoire+'/*.csv')
		
		for file_csv_full in Liste_file_csv:
			file_csv=file_csv_full.split('/')[-1]
			PEVrf_cur=getPEVrf(file_csv)
			PE_str_cur=PEVrf_cur[0]
			Vrf_str_cur=PEVrf_cur[1]
			#pdb.set_trace()
			
			if PE_str_cur not in self.PEs_str:
				self.PEs_str.append(PE_str_cur)
				self.PEs[PE_str_cur]=PE(PE_str_cur)
				
			self.PEs[PE_str_cur].addVrf(Vrf_str_cur)
			
		nb_file=0
		total_nb_file=len(Liste_file_csv)
		for file_csv_full_ in Liste_file_csv:
			nb_file=nb_file+1
			file_csv_=file_csv_full_.split('/')[-1]
			PEVrf_cur=getPEVrf(file_csv_)
			PE_str_cur=PEVrf_cur[0]
			Vrf_str_cur=PEVrf_cur[1]
			print("Traitement du fichier:"+file_csv_+" ("+str(nb_file)+"/"+str(total_nb_file)+")")
			with open(file_csv_full_,'r') as file_netentry_cur:
				for ligne in file_netentry_cur:
					ligne_col=ligne.split(';')
					#pdb.set_trace()
					if  "Prefix" not in ligne_col:
						#print("FILE:"+file_csv_+" LIGNE:"+ligne)
						#pdb.set_trace()
						reseau_cur=ligne_col[2]
						self.addPrefixStr(Vrf_str_cur,reseau_cur)
						NHs_cur=ligne_col[4:]
						Prefix_cur=prefix(reseau_cur,NHs_cur)
						self.PEs[PE_str_cur].addPrefix(Vrf_str_cur,Prefix_cur)
						#pdb.set_trace()
						#print(str(Prefix_cur)+'\n')
					
			
	def __str__(self):
		result=""
		for PE_str__ in self.PEs_str:
			result=result+">"+str(self.PEs[PE_str__])+"\n"
				
		return result
		
	def addPrefixStr(self,Vrf,Prefix):
		"Prefix et Vrf sont des str"
		
		try:
			if Prefix not in self.Prefixs_str[Vrf]:
				self.Prefixs_str[Vrf].append(Prefix)
		except KeyError:
			self.Prefixs_str[Vrf]=[]
			self.Prefixs_str[Vrf].append(Prefix)
			
	def printAllPrefix(self):
		print(str(self.Prefixs_str))
		
	def getNH_AllPE(self,vrf__,reseau__):
		result={}
		NHL=[]
		
		for PE_str__ in self.PEs_str:
			NHL__=self.PEs[PE_str__].getNH(vrf__,reseau__)
			if NHL__ is not None:
				result[PE_str__]=NHL__
		
		return result
		
	def verify_redundancy(self,vrf__,reseau__):
		
		result=True
		liste_NH_dict=self.getNH_AllPE(vrf__,reseau__)
		liste_NH_EBGP={}
		liste_NH_str=[]
		
		#if reseau__=='192.64.108.0/24' and vrf__=='HCOM':
			#print(liste_NH_dict)
			#pdb.set_trace()

		
		for PE__ in liste_NH_dict.keys():
			for NH__ in liste_NH_dict[PE__]:
				if NH__.is_eBGP():
					if NH__ not in liste_NH_str:
						liste_NH_EBGP[PE__]=NH__
						liste_NH_str.append(NH__.value[0])
						#print("eBGP P:"+vrf__+":"+reseau__+"=>"+PE__+":"+str(NH__))

		if len(liste_NH_EBGP) == 1:
			result=False
		
		#print("VRF:"+vrf__+":"+reseau__+"=>"+str(result))
		
		return result
		
	def verify_redundancy_all(self):
	
		result=[]
				
		for VRF__ in self.Prefixs_str.keys():
			for RESEAU__ in self.Prefixs_str[VRF__]:
				if not	man.verify_redundancy(VRF__,RESEAU__):
					result.append((VRF__,RESEAU__))
					
		return result
	
class CONFIG(object):
	"definit un ensemble de configuration de PE"
	
	def __init__(self,nom_repertoire):
		"repertoire contenant toutes les configurations"
		self.repertoire=nom_repertoire
		self.interface=self.extract_static_route()
		self.route=self.extract_interface()
	
	def extract_static_route(self):
		resultat={}
		return resultat	
		
	def extract_interface(self):
	
		result={}
		Space=pp.OneOrMore(pp.White(ws=' '))
		Hostname=pp.LineStart()+(pp.Keyword('hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.LineEnd().suppress()
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		LigneNonParagraphe=pp.LineStart()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		Mask=pp.Combine(octet + ('.'+octet)*3)
		head_interface=(pp.LineStart()+pp.Keyword('interface').suppress()+Space.suppress()+pp.Word(pp.alphanums+'/.-')+pp.LineEnd().suppress()).setResultsName('interface')
		Description=((Space+pp.Keyword('description') ).suppress()+pp.Combine( pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space)) +pp.LineEnd().suppress())).setResultsName('description')
		Vrf=((Space+pp.Optional(pp.Literal('ip'))+ pp.Literal('vrf forwarding')).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]{}<>*')+pp.LineEnd().suppress()).setResultsName('vrf')
		Address=((Space+ pp.Literal('ip address')).suppress()+pp.Combine(ipAddress+Space+Mask)+pp.LineEnd().suppress()).setResultsName('ip')
		OtherLine=pp.Combine((pp.LineStart()+Space+pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space))+pp.LineEnd())).suppress()
		SectionInterface=head_interface+pp.Optional(pp.SkipTo(Description,failOn=LigneNonParagraphe).suppress()+Description)+pp.Optional(pp.SkipTo(Vrf,failOn=LigneNonParagraphe).suppress()+Vrf)+pp.Optional(pp.SkipTo(Address,failOn=LigneNonParagraphe).suppress()+Address)+pp.ZeroOrMore(OtherLine)
	
		for file__ in glob.glob(self.repertoire+'/*.*'):
			with open(file__,'r') as fich__:
				file_str=fich__.read()
			hostname_cur=next(Hostname.scanString(file_str))[0][0]
			temp_list_interfaces=[]
			for parsingInterface in SectionInterface.scanString(file_str):
				temp_list_interfaces.append(parsingInterface[0].asDict())
			#print(hostname_cur)
			#print(str(temp_list_interfaces))
			result[hostname_cur]=temp_list_interfaces
			
		return result
		
	def isPrefixConnected(self,vrf,route):
	
		result=False
		Network_toTest=Network(route)
		
		for PE__ in self.route.keys():
			for INT__ in self.route[PE__]:
				try:
					prefix_str=INT__['ip'][0].split()
	
					ip__=prefix_str[0]
					mask__=prefix_str[1]
					
					# print(PE__)
					# print(INT__['interface'][0])
					# print(ip__)
									
					Network_Interface=Network(ip__+"/"+mask__)
					# if ip__ == '192.0.21.66':
						# pdb.set_trace()
				except KeyError:
					continue		
				try:
					VRF_cur=INT__['vrf'][0]
				except KeyError:
					VRF_cur='GRT'
				
				try:
					if vrf == VRF_cur and Network_Interface.netmask()== Network_toTest.netmask() and Network_Interface.network()== Network_toTest.network():
						result=True
				except KeyError:
					pass
					
		return result
		
	def SuppressConnected(self,tuple_vrf_reseau_list):
		result=[]
		for (VRF__,RESEAU__) in tuple_vrf_reseau_list:
			if not self.isPrefixConnected(VRF__,RESEAU__):
				result.append( (VRF__,RESEAU__) )
				
		return result

class jsonFile(object):
	def __init__(self,nom_fichier):
		self.fichier=nom_fichier
		
	def save(self,data):
		with open(self.fichier,'w') as file:
			json.dump(data,file)
			
	def load(self):
		data=None
		with open(self.fichier,'r') as file:
			data=json.load(file)
			
		return data
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--repertoire",action="store",help="Repertoire contenant les fichiers Net Entry DMO",required=True)
	parser.add_argument("-c", "--configrep",action="store",help="Repertoire contenant les configurations",required=True)
	parser.add_argument("-s", "--save",action="store",help="Sauvegarde du resultat dans un fichier format json",required=False)
	args = parser.parse_args()
	
	if args.configrep:
		print("Load des configurations...")
		config_man=CONFIG(args.configrep)
		config_man.extract_interface()
		#print(config_man.isPrefixConnected('RVP_NOOBA','192.0.21.66/255.255.255.224'))
		#print(config_man.isPrefixConnected('NSAL2P', '192.4.130.171/32'))
		
	if args.repertoire:
		man=MAN(args.repertoire)
		#pdb.set_trace()
		#print(str(man))
		
		#man.printAllPrefix()
		
		#for NH__ in man.PEs['DC2-B2'].getNH('CAZA','192.64.6.0/24'):
		#	print(NH__)
			
		#temp=man.getNH_AllPE('CAZA','192.64.6.0/24')
		
		# for PE__ in temp.keys():
			# print(PE__+":")
			# for NH__ in temp[PE__]:
				# print("   "+str(NH__)+str(NH__.is_eBGP()))
			
		test=man.verify_redundancy('HCOM','192.64.108.0/24')
		liste_non_redundant=config_man.SuppressConnected(man.verify_redundancy_all())
		
		
		for non_redundant in liste_non_redundant:
			print(non_redundant)
		
		if args.save:
			jsonFile(args.save).save(liste_non_redundant)
		

			
	