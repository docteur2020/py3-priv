#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from ipcalc import *
import ipaddress
import xlrd
import re
import io

MODEL_CONFIG_RTR="""!
ip vrf VPN<VPNID>
 description GDF SUEZ Partner VPN IPSEC - Partner VPN - <NOM>
 <RD>
!
!
crypto keyring CKR_VPN<VPNID>
 pre-shared-key address <GATEWAY> key <PRESHAREDKEY>
!
!
crypto isakmp profile IPF_VPN<VPNID>
 vrf VPN<VPNID>
 keyring CKR_VPN<VPNID>
 match identity address <GATEWAY> 255.255.255.255
!
!
crypto ipsec transform-set CTS_PARTNER-VPN<VPNID> esp-aes 256 esp-sha-hmac
!
!
crypto map CMP_IF_PO14.321-CRYPTO-MAP <VPNID> ipsec-isakmp
 set peer <GATEWAY>
 set transform-set CTS_PARTNER-VPN<VPNID>
 set reverse-route distance 50
 set reverse-route tag <VPNID>
 set isakmp-profile IPF_VPN<VPNID>
 match address ACL_CRYPTO-VPN<VPNID>-PEER_<GATEWAY>
 reverse-route static
!
!
interface Port-channel12.<VLAN>
 description VPN<VPNID> (GDFSUEZ-PartnerVPN-Partner VPN - <NOM>) - AIM ON
 encapsulation dot1Q <VLAN>
 ip vrf forwarding VPN<VPNID>
 ip address <IP_INTERCO> 255.255.255.248
 no ip redirects
 no ip proxy-arp
 standby <HSRP> ip <IP_VIRT>
 standby <HSRP> priority <PRIORITY>
 standby <HSRP> preempt delay minimum 180
 standby <HSRP> authentication vlan<VLAN>
 standby <HSRP> track 2 decrement 20
 logging event subif-link-status
 no cdp enable
!
!
<ROUTE>
!
!
!
ip access-list extended ACL_CRYPTO-VPN<VPNID>-PEER_<GATEWAY>
<CRYPTOACE>
!
!
ip access-list extended ACL_POLICING_VPN<VPNID>_PEER_<GATEWAY>
 permit ip host <GATEWAY>  any
!
class-map match-all CM_POLICING_VPN<VPNID>_PEER_<GATEWAY>
 match access-group name ACL_POLICING_VPN<VPNID>_PEER_<GATEWAY>
!
policy-map PM_POLICING_IPSEC_FROM_INTERNET
 class CM_POLICING_VPN<VPNID>_PEER_<GATEWAY>
  police 5000000 conform-action transmit  exceed-action drop  violate-action drop 
!
"""

MODEL_CONFIG_SW_VLAN="""!
vlan <VLAN>
  name Partner_VPN<VPNID>_AIM_ON
!
"""

MODEL_CONFIG_SW_TRUNK="""
! Add the vlan to the VPCs towards the partner routers :
interface port-channel212
  switchport trunk allowed vlan add <VLANS>
!
"""

MODEL_NO_CONFIG_SW_TRUNK="""
! Add the vlan to the VPCs towards the partner routers :
interface port-channel212
  switchport trunk allowed vlan rem <VLANS>
!
"""

MODEL_NO_CONFIG_RTR="""!
no crypto map CMP_IF_GI0/2.321-CRYPTO-MAP <VPNID> ipsec-isakmp
!
no crypto isakmp profile IPF_VPN<VPNID>
!
no crypto keyring CKR_VPN<VPNID>
!
no crypto ipsec transform-set CTS_PARTNER-VPN<VPNID> esp-aes 256 esp-sha-hmac
!
no interface Port-channel12.<VLAN>
!
no ip vrf VPN<VPNID>
!
!
no ip access-list extended ACL_CRYPTO-VPN<VPNID>-PEER_<GATEWAY>
!
!
policy-map PM_POLICING_IPSEC_FROM_INTERNET
 no class CM_POLICING_VPN<VPNID>_PEER_<GATEWAY>
!
!
no class-map match-all CM_POLICING_VPN<VPNID>_PEER_<GATEWAY>
!
no ip access-list extended ACL_POLICING_VPN<VPNID>_PEER_<GATEWAY>
!
"""


class configTemplate(Exception):
	"Classe template de configuration"
	def __init__(self,str):
		self.template=str
		
	def replace(self,liste_parametre):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		
		resultat=self.template
		for (param,valeur) in liste_parametre:
			#print("PARAM:{0} VALEUR:{1}".format(param,valeur))
			resultat=resultat.replace("<"+param+">",valeur)
			
		return resultat

class ipsecError(Exception):
	"Classe Exception pour IPSEC"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		
		self.message[0]=u'Erreur inconnue ou non traitée'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un réseau IPV4 valide'
		self.message[3]=u'Le réseau d\'interconnection:'+value1+u' n\'est trop petit,valeur max:\\'+value2.__str__()
		self.message[4]=u'format attendu pour les interconnexions VL1800:192.168.10.128/25. La valeur '+value1.__str__()+u' n\'est pas conforme'
		super(ipsecError, self).__init__(self.message[code])
		
class partenaire(object):
	"definit un equipement"
	def __init__(self,nom="TBD",vrf="TBD",interco='VL0:255.255.255.255/32',ipsec_endpoint="0.0.0.0",network_list=[],network_list_distant=[],presharedkey="TBD"):
		"Constructeur"
		
		self.nom=nom
		self.vrf=vrf
		self.ipsec_endpoint=self.init_ip(ipsec_endpoint)
		self.network_list=self.init_network_list(network_list)
		self.network_list_distant=self.init_network_list(network_list_distant)
		self.presharedkey=presharedkey
		self.interco=self.init_interco_vl(interco)
		self.config={}
		self.config=self.init_config()
		
	
	def __str__(self):
		"Affichage"
		
		result='#####################################################'+'\n'
		result+='NOM:'+self.nom+'\n'
		result+='VRF:'+self.vrf+'\n'
		result+='GATEWAY IPSEC:'+self.ipsec_endpoint.__str__()+'\n'
		result+='INTERCO:\n'
		result+='\tVLAN:'+self.interco[0]+'\n'
		result+='\tNET: '+self.interco[1].__str__()+'\n'
		result+='RESEAUX PARTENAIRE:\n'
		for net in self.network_list:
			result+='\t'+net.__str__()+'\n'
		result+='RESSOURCES:\n'
		for net in self.network_list_distant:
			result+='\t'+net.__str__()+'\n'
		result+='#####################################################'+'\n\n\n'
		return result
	
	def init_network_list(self,liste_network):
		"renvoie une liste d'objet IP"
		
		result=[]
		for network in liste_network:
			result.append(self.init_network(network.replace(' ','')))
				
		return result
			
	def init_ip(self,ip):
		"renvoie un objet IP"
		
		result=None
		try:
			result=ipaddress.ip_address(ip.replace(' ',''))
		except:
			raise ipsecError(1,ip) 
			
		return(result)        

	def init_network(self,network_):
		"renvoie un objet Network"
		
		result=None
		try:
			result=Network(network_.replace(' ',''))
		except:
			raise ipsecError(code=2,value1=network_)
			
		return(result)  

	def init_interco_net(self,network_,size_max):
		"renvoie un objet IP"
		
		result=None
		try:
			result=Network(network_.replace(' ',''))
		except:
			raise ipsecError(code=2,value1=network_)
		
		if result.subnet() > size_max:
			raise ipsecError(code=3,value1=network_,value2=size_max)
			
		return(result) 
	
	def init_interco_vl(self,vl_net):
		"traite le format type VL1800:192.168.1.0/24 pour les intercos"
		
		result=(None,None)
		
		vl_net_list=vl_net.split(':')
		
		if re.search("VL",vl_net_list[0]):
			vlan=vl_net_list[0].replace("VL","")
		else:
			raise ipsecError(code=4,value1=vl_net_list[0])
		
		interco=self.init_interco_net(vl_net_list[1],29)
		
		result=(vlan,interco)
		
		return  result
		
	def init_config_rtr_route(self):
		result=""
		for destination in self.network_list_distant:
			result+="ip route vrf "+self.vrf+" "+str(destination.network())+" "+str(destination.netmask())+" Port-channel12."+self.interco[0]+" "+str(self.interco[1].network()+4)+" name"+' \"GDC Partner VPN - '+self.nom+' - FW AIM ON\"\n'
		
		return result
		
	def init_config_rtr_ace(self):
		result=""
		for source in self.network_list_distant:
			for destination in self.network_list:
				result+=re.sub(r"\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s0.0.0.0",r" host \1 "," permit ip "+str(source.network())+" "+self.netmask_to_wildcard(source.netmask())+" "+str(destination.network())+" "+self.netmask_to_wildcard(destination.netmask())+'\n')
		return result
		
	def init_config_rtr(self,hsrp_mode):
		"genere la config du routeur"
		
		NOM=self.nom
		VPNID=self.vrf.replace('VPN','')
		PRESHAREDKEY=self.presharedkey
		GATEWAY=str(self.ipsec_endpoint)
		VLAN=self.interco[0]
		PRIORITY=('120','110')[hsrp_mode=='STANDBY']
		RD=('rd 64730:100282','rd 64730:100281')[hsrp_mode=='STANDBY']+VPNID
		HSRP=str(int(VLAN)%255+1)
		ROUTE=self.init_config_rtr_route()
		CRYPTOACE=self.init_config_rtr_ace()
		IP_INTERCO=str((self.interco[1].network()+3,self.interco[1].network()+2)[hsrp_mode=='STANDBY'])
		IP_VIRT=str(self.interco[1].network()+1)
		
		LISTE_PARAM_RTR=(('NOM',NOM),
						('RD',RD),
						('VPNID',VPNID),
						('PRESHAREDKEY',PRESHAREDKEY),
						('GATEWAY',GATEWAY),
						('PRIORITY',PRIORITY),
						('VLAN',VLAN),
						('HSRP',HSRP),
						('ROUTE',ROUTE),
						('CRYPTOACE',CRYPTOACE),
						('IP_INTERCO',IP_INTERCO),
						('IP_VIRT',IP_VIRT))
						
		return configTemplate(MODEL_CONFIG_RTR).replace(LISTE_PARAM_RTR)
		
	def init_no_config_rtr(self):
		"genere la config du routeur"
		
		VPNID=self.vrf.replace('VPN','')
		GATEWAY=str(self.ipsec_endpoint)
		VLAN=self.interco[0]
		NO_ROUTE=self.init_config_rtr_route()
		
		LISTE_PARAM_RTR=(('VPNID',VPNID),
						('GATEWAY',GATEWAY),
						('VLAN',VLAN))
						
		return configTemplate(MODEL_NO_CONFIG_RTR).replace(LISTE_PARAM_RTR)
		
	def init_config(self):
		"genere la config IPSEC"
		
		result={}
		result
		
		return result
		
	def netmask_to_wildcard(self,netmask):
		# print(str(IP(int(IP('255.255.255.255'))-int(netmask))))
		return str(IP(int(IP('255.255.255.255'))-int(netmask)))
		
class partenaires(object):
	"En cours"
	
	def __init__(self,excel_file):
		self.liste_partenaire=[]
		wb=xlrd.open_workbook(excel_file)
		sh = wb.sheet_by_name(u'Feuil1')
		for rownum in range(1,sh.nrows):
			self.liste_partenaire.append(partenaire(nom=sh.row_values(rownum)[0],vrf=sh.row_values(rownum)[1],interco=sh.row_values(rownum)[2],ipsec_endpoint=sh.row_values(rownum)[3],network_list=sh.row_values(rownum)[4].split('\n'),network_list_distant=sh.row_values(rownum)[5].split('\n'),presharedkey=sh.row_values(rownum)[6]))
	
	def __str__(self):
		resultat=""
		for partenaire in self.liste_partenaire:
			resultat+=partenaire.__str__()
			
		return resultat
		
	def init_config(self):
		resultat=io.StringIO()
		VLANS_=[]
		VLAN_NAME=""
		
		"Configuration commutateur"
		for partenaire_ in self.liste_partenaire:
			VLANS_.append(partenaire_.interco[0])
			VLAN_NAME+="""
vlan {val1}
 name Partner_{val2}_AIM_ON
!
""".format(val1=partenaire_.interco[0],val2=partenaire_.vrf)
		VLANS_.sort(key=int)
		VLANS=','.join(VLANS_)
		
		resultat.write('! GSFRGDCE-SW051/GSFRGDCE-SW052/GSFRDCQ-SW051/GSFRDCQ-SW052\n')
		resultat.write(VLAN_NAME)
		config_l2=configTemplate(MODEL_CONFIG_SW_TRUNK)
		resultat.write(config_l2.replace( [ ('VLANS',VLANS) ] ) )
		resultat.write('\n!GSFRDCE-RO001\n')
		for partenaire in self.liste_partenaire:
			resultat.write('\n!Config for '+partenaire.nom+'\n')
			resultat.write(partenaire.init_config_rtr('STANDBY'))
	
		resultat.write('\n!GSFRDCQ-RO002\n')
		for partenaire in self.liste_partenaire:
			resultat.write('\n!Config for '+partenaire.nom)
			resultat.write(partenaire.init_config_rtr('ACTIVE'))
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	def init_no_config(self):
		resultat=io.StringIO()
		VLANS_=[]
		VLAN_NAME=""
		
		"Configuration commutateur"
		for partenaire_ in self.liste_partenaire:
			VLANS_.append(partenaire_.interco[0])
			VLAN_NAME+="no vlan {val1}\n".format(val1=partenaire_.interco[0])
		VLANS_.sort(key=int)
		VLANS=','.join(VLANS_)
		
		resultat.write('! GSFRGDCE-SW051/GSFRGDCE-SW052/GSFRDCQ-SW051/GSFRDCQ-SW052\n')
		config_l2=configTemplate(MODEL_NO_CONFIG_SW_TRUNK)
		resultat.write(VLAN_NAME)
		resultat.write(config_l2.replace( [ ('VLANS',VLANS) ] ) )
		resultat.write('\n!GSFRDCE-RO001/GSFRDCQ-RO002\n')
		
		for partenaire in self.liste_partenaire:
			resultat.write('\n!Rollback for '+partenaire.nom+'\n')
			resultat.write(partenaire.init_no_config_rtr())
	
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
		
if __name__ == '__main__':
	"Fonction principale"	
	#TEST_PART_A=partenaire(nom="TOTO IPSEC",vrf="VPN6666",interco='VL100:192.168.10.0/29',ipsec_endpoint="4.3.2.100",network_list=['10.0.0.0/8','3.3.3.3','9.9.9.0/24'],network_list_distant=['10.0.0.0/8','3.3.3.3','9.9.9.0/24'],presharedkey="jgifdjgsfjsfoijgKFIGFODSKG@:;")
	#print(TEST_PART_A)
	
	#print(TEST_PART_A.init_config_rtr('STANDBY'))
	
	TEST_LISTE_PART_B=partenaires('EXCEL/GlobalInfo-B2S v0.1.xlsx')
	
	print(TEST_LISTE_PART_B.init_config())
	print(TEST_LISTE_PART_B.init_no_config())
	
	
	
	# C=configTemplate(MODEL_CONFIG_RTR)
	# print(C.replace((('VPNID','8105'),('GATEWAY','3.5.4.67'),('HSRP','255'))))