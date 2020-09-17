import string
import re
import os
import optparse
from ipcalc import * 
import pdb

class prefix(object):
	"definit une route, un prefix"
	def __init__(self,protocole="C",reseau="1.2.3.4/32",gateway="0.0.0.0",ligne="TOBEDEFINED"):
		"Constructeur"
		self.protocole=protocole
		self.reseau=Network(reseau)
		self.nexthop=gateway
		if ligne!="TOBEDEFINED":
			self.init_str(ligne)
		
	def __str__(self):
		"Pour l'affichage"
		return self.protocole+" "+self.reseau.__str__()+" vers:"+self.nexthop
		
	def init_str(self,ligne):
		"initialisation a partir d'une ligne de fichier"
		elements=ligne.split()
		self.protocole=elements[0]
		#print(elements[1])
		try:
			self.reseau=Network(elements[1])
		except ValueError:	
			print ("Erreur :"+elements[1]+" N'est pas une IP")
			print("Ligne:"+ligne)
		self.nexthop=elements[2]
	def test_eq_reseau(self,other):
		return self.reseau.__str__() == other.reseau.__str__() and str(self.reseau.subnet()) == str(other.reseau.subnet())
		
	def __eq__(self,other):
		return self.protocole==other.protocole and self.reseau.__str__() == other.reseau.__str__() and str(self.reseau.subnet()) == str(other.reseau.subnet()) and self.nexthop==other.nexthop
		
	def __contains__(self,other):
		# print(self.nexthop+" "+other.nexthop)
		# print(self.reseau)
		# print(other.reseau)
		# test=self.reseau.__contains__(other.reseau) and self.nexthop==other.nexthop
		# print(test)
		return self.reseau.__contains__(other.reseau) and self.nexthop==other.nexthop
	
	def get_reseau_str(self):
		return self.reseau.__str__()+"/"+str(self.reseau.subnet())
		
class table_routage(object):
	def __init__(self,nom_fichier):
		"Constructeur"
		self.tab_prefix=[]
		try:
			fichier=open(nom_fichier,"r")
			for ligne in fichier:
				self.tab_prefix.append(prefix(ligne=ligne))
				#print("FILE:"+ligne)
				#print(nom_fichier)
		except IOError:
			print("Fichier inaccessible")
			exit()
		else:
			fichier.close()
			
	def __str__(self):
		"Pour l'affichage"
		result=""
		for route in self.tab_prefix:
			result+=route.__str__()+"\n"
		return result
		
	def check_presence(self,other):
		"Verifie la presence dans la table plus globale(la table reelle)"
		Message={}
		test_=False
		for reseau in self.tab_prefix:
			Message[reseau.get_reseau_str()]="/!\/!\/!\ALERTE/!\/!\/!\ ROUTE KO:"
			test_=False
			#pdb.set_trace()
			for other_reseau in other.tab_prefix:
				if other_reseau==reseau:
					Message[reseau.get_reseau_str()]="ROUTE PRESENTE:"+other_reseau.__str__()
					test_=True
					break
			if not test_ :
				for other_reseau in other.tab_prefix:
					if reseau in other_reseau:
						Message[reseau.get_reseau_str()]="!!WARNING!! ROUTE PRESENTE:"+other_reseau.__str__()+" ROUTAGE NON ADEQUAT:"+reseau.__str__()
						test_=True
						break
						#print(Message[reseau.get_reseau_str()])
			if test_:
				pdb.set_trace()
				Message[reseau.get_reseau_str()]+=reseau.__str__()
				
		return Message
					
	def affichage_check_rt(self,messages):
		"Affiche un dictionnaire type message renvoye par check presence"
		for reseau in self.tab_prefix:
			print(messages[reseau.get_reseau_str()])
		
			
if __name__ == '__main__':
	
	parser = optparse.OptionParser()
	parser.add_option('-i','--input-file',help='fichier contenant les routes cibles',dest='CIBLE_FILE', default='ROUTE/dub-b1.cfg',action='store')
	parser.add_option('-e','--existant',help='fichier contenant les routes actuelles',dest='COURANT_FILE', default='ROUTE-RDS-CMC/dub-b1.format.log',action='store')
	(opts, args) = parser.parse_args()
	
	# A=prefix('S','192.168.1.0/24','192.168.1.1')
	# B=prefix('B','192.168.0.0/23','192.168.1.1')
	
	# if A in B:
		# print("route A dans table B") 
	# else:
		# print("route A non present dans B") 
	
	#print(opts.CIBLE_FILE)
	#print(opts.COURANT_FILE)
	#pdb.set_trace()
	CIBLE=table_routage(opts.CIBLE_FILE)
	COURANT=table_routage(opts.COURANT_FILE)
	
	CIBLE.affichage_check_rt(CIBLE.check_presence(COURANT))