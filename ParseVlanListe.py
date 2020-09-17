#!/usr/bin/env python3.7
# coding: utf-8


import argparse
import re
import pdb
import sys

class vlan:
	"Classe vlan, nom et id"
	def __init__(self,id,name="NONAME"):
		"Constructeur"
		self.id = id
		self.name=name

	def __str__(self):
		"Affichage"
		return "Vl:"+self.id.__str__()+" name :"+self.name
 
class liste_vlans:	
	"Liste de vlan, attention de sont des str"
	def __init__(self,liste_vlan_str):
		"constructeur"
		if liste_vlan_str=="ALL" or liste_vlan_str=="all":
			self.liste = "1-4094"
		else:
			self.liste = liste_vlan_str
				
	def __str__(self):
		"Affichage"
		return self.liste
		
	def __iter__(self):
		"Iteration"
		return iter(self.explode())
		
	def __contains__(self, vlan_item_):
		if isinstance(vlan_item_,str):
			vlan_item=vlan(int(vlan_item_),name="")
		else:
			vlan_item=vlan_item_
		result=False
		liste_vlan_list=[ t.strip() for t in self.liste.split(",") ]
		dash=re.compile("-")
		for vlan__ in liste_vlan_list:
			if dash.search(vlan__):
				vl=vlan__.split("-")
				vl_min=int(vl[0])
				vl_max=int(vl[1])
				
				if vlan_item.id >= vl_min and vlan_item.id <= vl_max:
					result=True
			else:
				try:
					if vlan_item.id == int(vlan__):
						result=True
				except ValueError:
					if vlan__=="none":
						pass

		return(result)
	
	def explode(self):
		result=[]
		i=""
		liste_vlan_list=[ t.strip() for t in self.liste.split(",") ]
		dash=re.compile("-")
		for vlan in liste_vlan_list:
			temp_list=[]
			if dash.search(vlan):
				vl=vlan.split("-")
				vl_min=int(vl[0])
				vl_max=int(vl[1])
				for vl in range(vl_min,vl_max):
					result.append(vl.__str__())
				result.append(vl_max.__str__())
			else:
				result.append(vlan)
		#print(result)
		return result
		
	def get_missing_vlan(self,liste_vlan,verbose=False):
		result=[]
		present=[]
		liste_explode=self.explode()
		for vlan in liste_vlan:
			if vlan not in liste_explode:
				result.append(vlan)
			else:
				present.append(vlan)
				
		result.sort(key=int)
		present.sort(key=int)
		virgule=","
		
		if not verbose:
			print(virgule.join(result))
		else:
			print('Missing:',virgule.join(result))
			print('Present:',virgule.join(present))
		

		
		return result
		
	def translate(self,translation__):
		resultat=None
		
		return resultat
			

class interface:
	"une interface avec info sh interface trunk"
	def __init__(self,nom_,type_,liste_vlans_):
		"constructeur"
		self.nom=nom_
		self.type=type_
		self.vlans_autorise=liste_vlans_
		
	def __str__(self):
		"Affichage"
		affiche="\nInterface:"+self.nom+" "+self.type+":\n"+"\tVlan(s):"+self.vlans_autorise.__str__()
		return affiche
	
	def __contains__(self, vlan_item):
		return vlan_item in liste_vlans(self.vlans_autorise)
	
class extract_info_l2_fich:
	"extrait les informations d'un fichier type show interface trunk"
	def __init__(self,nom_fichier_):
		"constructeur"
		self.nom_fichier=nom_fichier_
		fichier=open(self.nom_fichier,'r')
		self.liste_interface=[]
		liste_interface_nom_traite=[]
		nom_courant="N/A"
		type_courant="N/A"
		vlans_liste_courant="N/A"
		for ligne in fichier.readlines():
			line=ligne.split()
			if re.search('sh interface',ligne):
				nom_show=line[len(line)-2]
			elif re.search('^Invalid',ligne):
				nom_courant=nom_show
				type_courant="NON-EXISTENT if"
				vlans_courant="N/A"
				self.liste_interface.append(interface(nom_courant,type_courant,vlans_liste_courant))
			elif re.search('Access Mode VLAN:',ligne):
				vlans_access=line[len(line)-2]
			elif re.search('^Name',ligne):
				nom_courant=line[len(line)-1]
			elif re.search('Operational Mode',ligne):
				type_courant=line[len(line)-1]
			elif re.search('Trunking VLANs Allowed',ligne):
				#print (ligne)
				vlans_liste_courant=line[len(line)-1]
			#print("TYPE:"+type_courant*2)
			if nom_courant not in liste_interface_nom_traite and re.search('Unknown multicast blocked:',ligne): 
				if type_courant == "access":
					self.liste_interface.append(interface(nom_courant,type_courant,vlans_access))
					liste_interface_nom_traite.append(nom_courant)
				else:
					self.liste_interface.append(interface(nom_courant,type_courant,vlans_liste_courant))
					liste_interface_nom_traite.append(nom_courant)
	def __str__(self):
		"Affichage"
		result=""
		for interface in self.liste_interface:
			result+=interface.__str__()
		return result
	
	def affiche_presence_vlan(self,vlan_id,type_affichage):
		"Affichage"
		result=""
		for interface in self.liste_interface:
			if type_affichage == "short":
				if vlan_id in interface:
					print (interface.nom+" OK")
				else:
					print (interface.nom+" KO")
			elif type_affichage == "long":
				if vlan_id in interface:
					print (interface)
					print ("Vl:"+vlan_id.id.__str__()+" is present in "+interface.nom)
				else:
					print (interface)
					print ("Vl:"+vlan_id.id.__str__()+" is NOT present in "+interface.nom)

	def get_presence_vlans(self,Liste_vlan):
		resultat_dict={}
		#pdb.set_trace()
		for vlan_id in Liste_vlan:
			for interface in self.liste_interface:
				if vlan(int(vlan_id)) in interface:
					if interface.nom in resultat_dict:
						resultat_dict[interface.nom].append(vlan_id)
					else:
						resultat_dict[interface.nom]=[vlan_id]
		return resultat_dict
	
def initVlanNat(fichier):
	resultat={}
	with open(fichier,'r') as file__:
		for ligne in file__:
			ligne_col=ligne.split()
			try:
				resultat[ligne_col[0]]=ligne_col[1]
			except ValueError:
				pass
			except KeyError:
				pass

	return resultat
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-l", "--liste",action="store",type=str, help="Liste de vlan - Format Cisco")
	group.add_argument("-f", "--fichier",action="store",help="Analyse un fichier show interface trunk")
	parser.add_argument("-s", "--short",action="store_true",help="affiche resultat OK KO")
	parser.add_argument("-v", "--vlan",action="store",type=str, help="vlan a rechercher dans la liste")
	parser.add_argument("-c", "--compare",action="store",type=str,help="Verifie que la liste de vlan 2 est presente dans 1")
	parser.add_argument("-e", "--explode",action="store_true",help="detaille la liste de vlan")
	parser.add_argument("-t", "--translation",action="store",help="fichier contenant les translations")
	parser.add_argument("--verbose",action="store_true",default=False,help="fichier contenant les translations")
	args = parser.parse_args()
	
	if args.vlan:
		if re.search('[-,]',args.vlan):
			Liste_Entree=liste_vlans(args.vlan)
			resultat=[]
			resultat_dict={}
			if not args.fichier or not args.short:	
				for vlan__ in Liste_Entree.explode():
					try:
						A=vlan(int(vlan__))
					except ValueError:
						print("Merci de rentrer un entier (int) ou une liste type cisco")
						sys.exit(2)
						
					if args.liste:
						Liste_A=liste_vlans(args.liste)
						if A in Liste_A:
							if args.short:
								resultat.append(A.id)
							else:
								resultat.append(A)
					
					elif args.fichier:		
						shint=extract_info_l2_fich(args.fichier)
						if args.short:
							shint.affiche_presence_vlan(A,"short")
						else:
							shint.affiche_presence_vlan(A,"long")
				"Affichage du resultat"
				if args.liste:
					if args.short:
						print(str(resultat))
					else:
						print("Vlan(s) present(s) dans la liste:")
						for vl__ in resultat:
							print(vl__)
					
				elif args.fichier:		
					shint=extract_info_l2_fich(args.fichier)
					if args.short:
						shint.affiche_presence_vlan(A,"dict")
					else:
						shint.affiche_presence_vlan(A,"long")
			else:
				"option short et fichier"
				Liste_Entree__B=liste_vlans(args.vlan)
				#pdb.set_trace()
				shint__=extract_info_l2_fich(args.fichier)
				resultat_dict=shint__.get_presence_vlans(Liste_Entree__B)
				print(str(resultat_dict))
				
		else:
			try:
				A=vlan(int(args.vlan))
			except ValueError:
				print("Merci de rentrer un entier (int) ou une liste type cisco")
				sys.exit(2)
			if args.liste:
				Liste_A=liste_vlans(args.liste)
				if args.short:
					if A in Liste_A:
						print ("OK")
					else:
						print ("KO")
				else:
					print (A)
					print (Liste_A)
					if A in Liste_A:
						print ("Vlan present in list")
					else:
						print ("Vlan not present in list")
			
			elif args.fichier:		
				shint=extract_info_l2_fich(args.fichier)
				if args.short:
					shint.affiche_presence_vlan(A,"short")
				else:
					shint.affiche_presence_vlan(A,"long")
		
	elif args.compare:
		if args.liste:
			Liste_A=liste_vlans(args.liste)
			Liste_A.get_missing_vlan(liste_vlans(args.compare),verbose=args.verbose)
		
		elif args.fichier:		
			print("Option non prise en compte")
			
	elif args.explode:
		if args.liste:
			Liste_A=liste_vlans(args.liste)
			print(",".join(Liste_A.explode()))
		elif args.fichier:		
			print("Option non prise en compte")
		
		if args.translation:
			vlan_t=initVlanNat(args.translation)
			
			for vlan__ in Liste_A:
				if vlan__ in vlan_t.keys():
					print("TRANSLATION:"+vlan__+"=>"+vlan_t[vlan__])
				else:
					print("PAS DE TRANSLATION:"+vlan__+"=="+vlan__)

			
