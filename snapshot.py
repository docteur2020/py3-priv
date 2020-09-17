#!/usr/bin/env python3.7
# coding: utf-8

import time
import yaml
import sys
import argparse
from connexion import *
from ParsingShow import *
import aci.Fabric as ACISbe


CMD_YAML='/home/x112097/yaml/commandes_base.yml'

class snapshot(object):
	
	def __init__(self,hostnames):
		self.hostnames=hostnames
		self.equipements_db=equipement_connus()
		for host in self.hostnames.keys():
			self.hostnames[host]['commandes']=[]
		
	def get_vrf(self,equipement__):
		resultat_vrf=[]
		try:
			equipement_cur=self.equipements_db[equipement__]
		except KeyError as e:
			try:
				equipement_cur=self.equipements_db[equipement__.lower()]
			except KeyError as e:
				print(e)
				print("equipement "+equipement__+" inconnus")
				print("(1) Il faut renseigner la db avec connexion.py")
				sys.exit(2)

		OS_cur=equipement_cur[0]
		type_cur=equipement_cur[2]

		if OS_cur=='IOS' or OS_cur=="OLD-IOS":
			tentative=1
			while tentative <=3:
				try:
					con_get_vrf_cur=connexion(equipement(equipement__),None,None,None,type_cur,"TMP/"+"getallvrf_"+equipement__.lower()+".log","TMP","show ip vrf",timeout=300,verbose=False)
					resultat_vrf=con_get_vrf_cur.launch_withParser(ParseVrf)
					break;
				except ErrorNeedRetry as error_retry:
					tentative=tentative+1
					print(error_retry)
					print("Tentative:"+str(tentative))
					pass
		elif OS_cur=="Nexus":
			tentative=1
			while tentative <=3:
				try:
					con_get_vrf_cur=connexion(equipement(equipement__),None,None,None,type_cur,"TMP/"+"getallvrf_"+equipement__.lower()+".log","TMP","show vrf",timeout=300,verbose=False)
					resultat_vrf=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
					break;
				except ErrorNeedRetry as error_retry:
					tentative=tentative+1
					print(error_retry)
					print("Tentative:"+str(tentative))
					pass
		else:
			pass
		
		return resultat_vrf
		
	def get_bgp_neigh(self,equipement__,vrfs__):
		dict_neighbor={}
		try:
			equipement_cur=self.equipements_db[equipement__]
		except KeyError as e:
				try:
					equipement_cur=self.equipements_db[host.lower()]
				except KeyError as e:	
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(2) Il faut renseigner la db avec connexion.py")
					sys.exit(2)

		OS_cur=equipement_cur[0]
		type_cur=equipement_cur[2]
		

		if OS_cur=='IOS' or OS_cur=="OLD-IOS":
			tentative=1
			commande_bgp_sum=[ "sh ip bgp vpnv4 vrf "+Vrf__ + " summary" for Vrf__ in  vrfs__ ]
			commande_bgp_sum.append("sh ip bgp summary")
			while tentative <=3:
				try:
					con_get_neigh_cur=connexion(equipement(equipement__),None,None,None,type_cur,"TMP/"+"getallvrf_"+equipement__.lower()+".log","TMP",commande_bgp_sum,timeout=300,verbose=False)
					dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
					break;
				except ErrorNeedRetry as error_retry:
					tentative=tentative+1
					print(error_retry)
					print("Tentative:"+str(tentative))
					pass
		elif OS_cur=="Nexus":
			tentative=1
			commande_bgp_sum=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  vrfs__  ]
			while tentative <=3:
				try:
					con_get_neigh_cur=connexion(equipement(equipement__),None,None,None,type_cur,"TMP/"+"getallvrf_"+equipement__.lower()+".log","TMP",commande_bgp_sum,timeout=300,verbose=False)
					dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
					break;
				except ErrorNeedRetry as error_retry:
					tentative=tentative+1
					print(error_retry)
					print("Tentative:"+str(tentative))
					pass
		else:
			tentative=1
			commande_bgp_sum='sh bgp vrf all summary'
			while tentative <=3:
				try:
					con_get_neigh_cur=connexion(equipement(equipement__),None,None,None,type_cur,"TMP/"+"getallvrf_"+equipement__.lower()+".log","TMP",commande_bgp_sum,timeout=300,verbose=False)
					dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
					break;
				except ErrorNeedRetry as error_retry:
					tentative=tentative+1
					print(error_retry)
					print("Tentative:"+str(tentative))
					pass
		
		return dict_neighbor
		
	def init_vrf(self):
		for equipement__ in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[equipement__]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[equipement__.lower()]
				except KeyError as e:	
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(3) Il faut renseigner la db avec connexion.py")
					sys.exit(2)
			
			OS_cur=equipement_cur[0]

			try:
				if ( self.hostnames[equipement__]['BGP'] == 'ALL' or self.hostnames[equipement__]['VRF'] == 'ALL') and OS_cur!="XR" :
					print("il est nécessaire de récupérer les VRF pour l'équipement "+equipement__)
					Vrf_cur=self.get_vrf(equipement__)
					if self.hostnames[equipement__]['BGP'] == 'ALL':
						self.hostnames[equipement__]['BGP']=Vrf_cur
					if self.hostnames[equipement__]['VRF'] == 'ALL':
						self.hostnames[equipement__]['VRF']=Vrf_cur
			except KeyError:
				try:
					if self.hostnames[equipement__]['VRF'] == 'ALL' and OS_cur!="XR":
						print("il est nécessaire de récupérer les VRF pour l'équipement "+equipement__)
						Vrf_cur=self.get_vrf(equipement__)
						if self.hostnames[equipement__]['VRF'] == 'ALL':
							self.hostnames[equipement__]['VRF']=Vrf_cur
				except KeyError:
					pass
					
			try:
				if ( self.hostnames[equipement__]['BGP_Light'] == 'ALL' or self.hostnames[equipement__]['VRF'] == 'ALL') and OS_cur!="XR" :
					print("il est nécessaire de récupérer les VRF pour l'équipement "+equipement__)
					Vrf_cur=self.get_vrf(equipement__)
					if self.hostnames[equipement__]['BGP_Light'] == 'ALL':
						self.hostnames[equipement__]['BGP_Light']=Vrf_cur
					if self.hostnames[equipement__]['VRF'] == 'ALL':
						self.hostnames[equipement__]['VRF']=Vrf_cur
			except KeyError:
				try:
					if self.hostnames[equipement__]['VRF'] == 'ALL' and OS_cur!="XR":
						print("il est nécessaire de récupérer les VRF pour l'équipement "+equipement__)
						Vrf_cur=self.get_vrf(equipement__)
						if self.hostnames[equipement__]['VRF'] == 'ALL':
							self.hostnames[equipement__]['VRF']=Vrf_cur
				except KeyError:
					pass
				
		return
						

					
	def init_bgp_neigh(self):
		for equipement__ in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[equipement__]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[equipement__.lower()]
				except KeyError as e:
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(4) Il faut renseigner la db avec connexion.py")
					sys.exit(2)
			
			#pdb.set_trace()
			OS_cur=equipement_cur[0]
			if 'BGP' in self.hostnames[equipement__].keys():
				print("il est nécessaire de récupérer les Neighbor pour l'équipement "+equipement__)
				Neigh_cur=self.get_bgp_neigh(equipement__,self.hostnames[equipement__]['BGP'] )
				self.hostnames[equipement__]['BGP_Neighbor']=Neigh_cur
			elif 'BGP_Light' in self.hostnames[equipement__].keys():
				self.hostnames[equipement__]['BGP_Sum']=True	
				

	
	def init_commandes_global(self):
		with open(CMD_YAML, 'r') as model_yml:
			commandes_bases = yaml.load(model_yml,Loader=yaml.SafeLoader)
			
		self.commandes_spec={}
		for other_type_commande in commandes_bases.keys():
			if other_type_commande != 'commandes':
				self.commandes_spec[other_type_commande]=commandes_bases[other_type_commande]

			
		for host in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[host]
				OS_cur=equipement_cur[0]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[host.lower()]
					OS_cur=equipement_cur[0]
				except KeyError as e:	
					print(e)
					print("equipment "+host+" unknown")
					print("(5) Please update db with connexion.py")
					sys.exit(2)

				
			try:			
				self.hostnames[host]['commandes']+=commandes_bases['commandes'][OS_cur]
				
			except KeyError as e:
				print("KeyError:"+str(e))
				print('OS non connu')
				sys.exit(4)
				
			for other_type_commande in self.commandes_spec.keys():
				if other_type_commande.upper() in self.hostnames[host].keys():
					self.hostnames[host]['commandes']+=self.commandes_spec[other_type_commande]
				
		
				
	def init_commandes_arp(self):
			
		commande_arp=[]
		for host in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[host]
				OS_cur=equipement_cur[0]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[host.lower()]
					OS_cur=equipement_cur[0]
				except KeyError as e:	
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(6) Il faut renseigner la db avec connexion.py")
					sys.exit(2)
				
			for action in self.hostnames[host]:
				if action=='VRF':
	
					if OS_cur=='IOS' or OS_cur=="OLD-IOS" or OS_cur=='Nexus': 
						commande_arp=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['VRF'] ]
						commande_arp.append("sh ip arp")
						
		
					elif OS_cur=='XR':
						if self.hostnames[host]['VRF']=='ALL':
							commande_arp=['sh arp vrf all']
						else:
							commande_arp=[ "sh arp vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['VRF'] ]
							commande_arp.append("sh arp")
	
					try:			
						self.hostnames[host]['commandes']+=commande_arp
						commande_arp=[]
						
					except KeyError as e:
						print("KeyError:"+str(e))
						print('OS non connu')
						sys.exit(4)
				
	def init_commandes_routes(self):
			
		commande_route=[]
		for host in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[host]
				OS_cur=equipement_cur[0]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[host.lower()]
					OS_cur=equipement_cur[0]
				except KeyError as e:	
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(7) Il faut renseigner la db avec connexion.py")
					sys.exit(2)
				
			for action in self.hostnames[host]:
				if action=='VRF':
	
					if OS_cur=='IOS' or OS_cur=="OLD-IOS" or OS_cur=='Nexus': 
						commande_route=[ "sh ip route vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['VRF'] ]
						commande_route.append("sh ip route")
						
		
					elif OS_cur=='XR':
						if self.hostnames[host]['VRF']=='ALL':
							commande_route=['sh route vrf all']
						else:
							commande_route=[ "sh route vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['VRF'] ]
							commande_route.append("sh route")
	
			try:			
				self.hostnames[host]['commandes']+=commande_route
				commande_route=[]
				
			except KeyError as e:
				print("KeyError:"+str(e))
				print('OS non connu')
				sys.exit(4)
				
	def init_commandes_ospf(self):
			
		commande_ospf=[]
		for host in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[host]
				OS_cur=equipement_cur[0]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[host.lower()]
					OS_cur=equipement_cur[0]
				except KeyError as e:	
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(8) Il faut renseigner la db avec connexion.py")
					sys.exit(2)
		
				
				
			for action in self.hostnames[host]:
				if action=='OSPF':
	
					if OS_cur=='IOS' or OS_cur=="OLD-IOS" or OS_cur=='Nexus': 
						commande_ospf=[ "sh ip ospf vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf+=[ "sh ip ospf database vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf+=[ "sh ip ospf interface vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf+=[ "sh ip ospf interface brief vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf.append("sh ip ospf")
						commande_ospf.append("sh ip ospf database")
						commande_ospf.append("sh ip ospf interface")
						commande_ospf.append("sh ip ospf interface brief")
						
					if OS_cur=='IOS' or OS_cur=="OLD-IOS": 
						commande_ospf=[ "sh ip ospf " ]
						commande_ospf+=[ "sh ip ospf database "]
						commande_ospf+=[ "sh ip ospf interface " ]
						commande_ospf+=[ "sh ip ospf interface brief vrf " ]
						commande_ospf.append("sh ip ospf")
		
					elif OS_cur=='XR':
						commande_ospf=[ "sh ospf vrf "+Vrf__ for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf+=[ "sh ospf  vrf "+Vrf__+" database" for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf+=[ "sh ospf  vrf "+Vrf__+" interface" for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf+=[ "sh ospf  vrf "+Vrf__+" interface brief" for Vrf__ in  self.hostnames[host]['OSPF'] ]
						commande_ospf.append("sh ospf")
						commande_ospf.append("sh ospf database")
						commande_ospf.append("sh ospf interface")
						commande_ospf.append("sh ospf interface brief")
	
			try:			
				self.hostnames[host]['commandes']+=commande_ospf
				commande_commande_ospf=[]
				
			except KeyError as e:
				print("KeyError:"+str(e))
				print('OS non connu')
				sys.exit(4)
				
	def init_commandes_bgp(self):
			
		commande_bgp=[]
		for host in self.hostnames.keys():
			try:
				equipement_cur=self.equipements_db[host]
				OS_cur=equipement_cur[0]
			except KeyError as e:
				try:
					equipement_cur=self.equipements_db[host.lower()]
					OS_cur=equipement_cur[0]
				except KeyError as e:	
					print(e)
					print("equipement "+equipement__+" inconnus")
					print("(9) Il faut renseigner la db avec connexion.py")
					sys.exit(2)
			
			commande_bgp=[]
			for action in self.hostnames[host]:
				if action=='BGP_Neighbor':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						commande_bgp+=[ "sh ip bgp vpnv4 vrf "+Vrf__ + " summary" for Vrf__ in  self.hostnames[host]['BGP_Neighbor'].keys() ]
						commande_bgp.append("sh ip bgp summary")
						for Vrf__ in self.hostnames[host]['BGP']:
							if Vrf__ !='GRT':
								commande_bgp.append("sh ip bgp vpnv4 vrf "+Vrf__+" summary")
								commande_bgp.append("sh ip bgp vpnv4 vrf "+Vrf__)
								if self.hostnames[host]['BGP_Neighbor'][Vrf__]:
									for Neigh__ in self.hostnames[host]['BGP_Neighbor'][Vrf__]:
										try:
											if Neigh__[2].isdigit():
												commande_bgp.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
												commande_bgp.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
										except TypeError:
											pass
							else:
								commande_bgp.append("sh ip bgp summary")
								commande_bgp.append("sh ip bgp ")
								if self.hostnames[host]['BGP_Neighbor'][Vrf__]:
									for Neigh__ in self.hostnames[host]['BGP_Neighbor'][Vrf__]:
										try:
											if Neigh__[2].isdigit():
												commande_bgp.append("sh ip bgp  neighbor "+Neigh__[0]+" routes")
												commande_bgp.append("sh ip bgp  neighbor "+Neigh__[0]+" advertised-routes")
										except TypeError:
											pass
						
					elif OS_cur=='Nexus':
						commande_bgp+=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  self.hostnames[host]['BGP_Neighbor'].keys() ]
						for Vrf__ in self.hostnames[host]['BGP']:
							commande_bgp.append("sh ip bgp vrf "+Vrf__+" summary")
							commande_bgp.append("sh ip bgp vrf "+Vrf__)
							if self.hostnames[host]['BGP_Neighbor'][Vrf__]:
								for Neigh__ in self.hostnames[host]['BGP_Neighbor'][Vrf__]:
									try:
										if Neigh__[2].isdigit():
											commande_bgp.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
											commande_bgp.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
									except TypeError:
										pass
					
										
					elif OS_cur=='XR':
						if self.hostnames[host]['VRF']=='ALL':
							for Vrf__ in self.hostnames[host]['BGP_Neighbor'].keys():
								commande_bgp.append("sh bgp vrf "+Vrf__+" summary")
								commande_bgp.append("sh bgp vrf "+Vrf__)
								if self.hostnames[host]['BGP_Neighbor'][Vrf__]:
									for Neigh__ in self.hostnames[host]['BGP_Neighbor'][Vrf__]:
										if Neigh__[2].isdigit():
											commande_bgp.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
											commande_bgp.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
						else:
							for Vrf__ in self.hostnames[host]['BGP']:
								commande_bgp.append("sh bgp vrf "+Vrf__+" summary")
								commande_bgp.append("sh bgp vrf "+Vrf__)
								if self.hostnames[host]['BGP_Neighbor'][Vrf__]:
									for Neigh__ in self.hostnames[host]['BGP_Neighbor'][Vrf__]:
										if Neigh__[2].isdigit():
											commande_bgp.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
											commande_bgp.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
				elif action=='BGP_Sum':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						commande_bgp+=[ "sh ip bgp vpnv4 vrf "+Vrf__ + " summary" for Vrf__ in  self.hostnames[host]['BGP_Light']  ]
						commande_bgp.append("sh ip bgp summary")
						
					elif OS_cur=='Nexus':
						commande_bgp+=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  self.hostnames[host]['BGP_Light']]
				
										
					elif OS_cur=='XR':
						try:
							if self.hostnames[host]['BGP_Light']=='ALL':
								for Vrf__ in self.hostnames[host]['BGP_Light']:
									commande_bgp.append("sh bgp vrf all summary")
	
							else:
								for Vrf__ in self.hostnames[host]['BGP_Light']:
									commande_bgp.append("sh bgp vrf "+Vrf__+" summary")
						except KeyError as e:
							pdb.set_trace()
							print(e)
			try:			
				self.hostnames[host]['commandes']+=commande_bgp
				commande_bgp=[]
				
			except KeyError as e:
				print("KeyError:"+str(e))
				print('OS non connu')
				sys.exit(4)
				
	def init_commandes(self):
		self.init_commandes_global()
		self.init_commandes_arp()
		self.init_commandes_routes()
		self.init_commandes_bgp()
		self.init_commandes_ospf()
		
	def print_commandes(self):
		for host in self.hostnames.keys():
			print(host+";"+",".join(self.hostnames[host]['commandes']))
			
	def save_commandes(self,filename):
		with open(filename,"w+") as file__:
			for host in self.hostnames.keys():
				file__.write(host+";"+",".join(self.hostnames[host]['commandes'])+'\n')

		

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-e", "--equipements", action="store",help="Yaml contenant les équipements à checker et les actions")
	parser.add_argument("-s", "--save", action="store",help="Fichier de commandes",required=False)
	group.add_argument("-f", "--fabric", action="store",help="Aci fabric",required=False)
	parser.add_argument("--site", action="store",help="Aci fabric",required=False)
	args = parser.parse_args()
	
	if args.fabric and not args.site:
		raise argparse.ArgumentError(None,'--site  is manadatory with --fabric ')

	
	if args.equipements:
		with open(args.equipements, 'r' ) as model_yml:
			actions = yaml.load(model_yml,Loader=yaml.SafeLoader)
			print(actions)
			snap__=snapshot(actions)
			snap__.init_vrf()
			snap__.init_bgp_neigh()
			print(snap__.hostnames)
			
			snap__.init_commandes()
			snap__.print_commandes()
		
			if args.save:
				snap__.save_commandes(args.save)
			
	if args.fabric:
		NodeData=ACISbe.Fabric.getNodeFromeCache()
		
		
		if args.fabric not in NodeData:
			print('Fabric unknown',file=sys.stderr)
			print('Known Fabric:',str(list(NodeData.keys())))
			sys.exit(1)
			
		if args.site not in NodeData[args.fabric]:
			print('Site unknown',file=sys.stderr)
			print('Known Site for',args.fabric,'=>',str(list(NodeData[args.fabric].keys())))
			sys.exit(1)
			

		type_OS={'spine':'ACI-SPINE' , 'leaf':'ACI-LEAF' , 'controller':'ACI-APIC' }
		host__ = { NodeData[args.fabric][args.site][node__]['name']: {} for node__,data__ in NodeData[args.fabric][args.site].items()}
		ip__=  { NodeData[args.fabric][args.site][node__]['name']: data__['info']['oob_mgmt_ip']  for node__,data__ in NodeData[args.fabric][args.site].items()}  
		os__=  { NodeData[args.fabric][args.site][node__]['name']: type_OS[data__['info']['role']]  for node__,data__ in NodeData[args.fabric][args.site].items()}
		snap__=snapshot(host__)
		
		
		DB=equipement_connus()
		for host in ip__:
			DB.append(equipement(host.lower(),OS=os__[host],IP=ip__[host]),mode='add')
			DB.append(equipement(host.upper(),OS=os__[host],IP=ip__[host]),mode='add')
			
		snap__.init_commandes_global()
		

			
		snap__.print_commandes()
		
		if args.save:
			snap__.save_commandes(args.save)
			
	


