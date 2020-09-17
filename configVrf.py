#!/usr/bin/env python3.7
# coding: utf-8

import ipaddress
import xlrd
import re
import io
import argparse
from ipcalc import *
import pdb
import os
from parseTemplate import *

ID_PE={'TIG-D4' : '180' , 'TIG-D7' : '181' , 'TIG-D0':  '190','SC2-A1' : '134', 'SC2-A2' : '135' , 'SC2-A0':'192' , 'DC2-B1' : '45', 'DC2-B2' : '46' , 'DC2-B0' : '193' ,'ORI-A0':'191','DUN-T1':'141','DUN-U1':'142','SEC-B1':'161'}
ID_CE={'DUN-A10' : '143', 'DUN-A20' : '144','DUN-U10' : '157', 'DUN-U20' : '158','SC2ASV-CDN-CFD-VDC02':'158','SC1STX-CDN-CFD-VDC02':'159','DC2A1-SVC-CFD-A1':'96','DC2A2-SVC-CFD-A2':'97'}
PARITY_SPEC={'DUN-T1':1,'DUN-U1':2,'DUN-A10':1,'DUN-A20':2,'DUN-U10':1,'DUN-U20':2,'SEC-B1':1,'SC2-A1':2}

RR_MAN={'DC2-B0':'IOS','ORI-A0':'IOS','SC2-A0':'IOS','TIG-D0':'IOS'}
COUPLE_CE={ 'TIGR4-SANA-CFD-A1':'TIGR7-SANA-CFD-A2',
			'TIGR7-SANA-CFD-A2':'TIGR4-SANA-CFD-A1',
			'DC2A1-SANA-CFD-A1':'DC2A2-SANA-CFD-A2',
			'DC2A2-SANA-CFD-A2':'DC2A1-SANA-CFD-A1',
			'SC2ASV-SANA-CFD-A1':'SC2CLK-SANA-CFD-A2',
			'SC2CLK-SANA-CFD-A2':'SC2ASV-SANA-CFD-A1',
			'TIGR4-CAZA-CFD-A1':'TIGR7-CAZA-CFD-A2',
			'TIGR7-CAZA-CFD-A2':'TIGR4-CAZA-CFD-A1',
			'DC2A1-CAZA-CFD-A1':'DC2A2-CAZA-CFD-A2',
			'DC2A2-CAZA-CFD-A2':'DC2A1-CAZA-CFD-A1',
			'DC2A1-SVC-CFD-A1':'DC2A2-SVC-CFD-A2',
			'DC2A2-SVC-CFD-A2':'DC2A1-SVC-CFD-A1',
			'SC2ASV-CAZA-CFD-A1':'SC2CLK-CAZA-CFD-A2',
			'SC2CLK-CAZA-CFD-A2':'SC2ASV-CAZA-CFD-A1',
			'SC2ASV-CDN-CFD-VDC02':'SC1STX-CDN-CFD-VDC02',
			'SC1STX-CDN-CFD-VDC02':'SC2ASV-CDN-CFD-VDC02',
			'DUN-A10':'DUN-A20',
			'DUN-A20':'DUN-A10',
			'DUN-U10':'DUN-U20',
			'DUN-U20':'DUN-U10',}
			
			
CODE_ENV={'DEV':'1','HOMO':'2','PROD':'3','DR':'4'}
CODE_COLOR={'IMPAIR':'BLUE','PAIR':'RED'}
PATH_CONFIG='RUN/PE/30072018'

MODEL_CONFIG_PE="""!
!
vrf <VRF>
 address-family ipv4 unicast
  import route-target
   <RT>
  !
  export route-target
   <RT>
  !
 !

!
<CONFIG_INTERCO_PE_CE>
!
router bgp 64911
 vrf <VRF>
  rd <RD>
  bgp router-id <ROUTER_ID>
  address-family ipv4 unicast
   maximum-paths ibgp 4
   redistribute connected
  !
  neighbor <IP_CE>
   remote-as <REMOTE_AS>
   bfd fast-detect
   bfd multiplier 3
   bfd minimum-interval 500
   password <PASSWORD>
   description Peer eBGP <VRF> <CE>
   address-family ipv4 unicast
    send-community-ebgp
    route-policy <ROUTE_POLICY_IN> in
    route-policy <ROUTE_POLICY_OUT> out
    as-override
    send-extended-community-ebgp
  { if default soft-reconfiguration inbound
    
	 default-originate route-policy <ROUTE_POLICY_DEFAULT_ORIGINATE> }
    site-of-origin <SOO>
   !
  !
 !
!


"""

MODEL_CONFIG_CE_NEXUS="""!

vrf context <VRF>

route-map <VRF>:DIRECT->BGP permit 100

route-map <VRF>:STATIC->BGP permit 100

router bgp <AS_BGP>
  vrf <VRF>
    router-id <ROUTER_ID>
    address-family ipv4 unicast
      redistribute direct route-map <VRF>:DIRECT->BGP
      redistribute static route-map <VRF>:STATIC->BGP
    neighbor <IP_PE> remote-as 64911
      bfd
      description Peer eBGP <VRF> <PE>
      password <PASSWORD>
      timers 5 15
      address-family ipv4 unicast
        send-community both
        default-originate
        soft-reconfiguration inbound
    neighbor <IP_CE_OTHER> remote-as <AS_BGP>
      bfd
      description Peer iBGP <VRF> <OTHER_CE>
      password <PASSWORD>
      timers 5 15
      address-family ipv4 unicast
        send-community both
        next-hop-self
        soft-reconfiguration inbound

"""

MODEL_CONFIG_CE_IOS="""!

ip vrf <VRF>
  rd <RD>

route-map <VRF>:CONNECTED->BGP permit 100

route-map <VRF>:STATIC->BGP permit 100

router bgp <AS_BGP>
 address-family ipv4 vrf <VRF>
  bgp router-id <ROUTER_ID>
  redistribute connected route-map <VRF>:CONNECTED->BGP
  redistribute static route-map <VRF>:STATIC->BGP
  neighbor <IP_PE> remote-as 64911
  neighbor <IP_PE> description Peer eBGP <VRF> <PE>
  neighbor <IP_PE> password <PASSWORD>
  neighbor <IP_PE> activate
  neighbor <IP_PE> send-community both
  neighbor <IP_PE> soft-reconfiguration inbound
  neighbor <IP_CE_OTHER> remote-as <AS_BGP>
  neighbor <IP_CE_OTHER> description Peer iBGP <VRF> <OTHER_CE>
  neighbor <IP_CE_OTHER> password <PASSWORD>
  neighbor <IP_CE_OTHER> activate
  neighbor <IP_CE_OTHER> send-community both
  neighbor <IP_CE_OTHER> next-hop-self
  neighbor <IP_CE_OTHER> soft-reconfiguration inbound
 exit-address-family

"""

MODEL_CONFIG_CE_NEXUS_PEER_PE="""!
    neighbor <IP_PE> remote-as 64911
      bfd
      description Peer eBGP <VRF> <PE>
      password <PASSWORD>
      timers 5 15
      address-family ipv4 unicast
        send-community both
        soft-reconfiguration inbound
!
"""

MODEL_CONFIG_CE_IOS_PEER_PE="""!
     neighbor <IP_PE> remote-as 64911
     neighbor <IP_PE> description Peer eBGP <VRF> <PE>
     neighbor <IP_PE> password <PASSWORD>
     neighbor <IP_PE> activate
     neighbor <IP_PE> send-community both
     neighbor <IP_PE> soft-reconfiguration inbound
!
"""

MODEL_HEADER_BGP_VRF_IOS="""
 address-family ipv4 vrf <VRF>
  bgp router-id <ROUTER_ID>
  redistribute connected route-map <VRF>:CONNECTED->BGP
  redistribute static route-map <VRF>:STATIC->BGP
"""

MODEL_HEADER_BGP_VRF_NX="""
  vrf <VRF>
    router-id <ROUTER_ID>
    address-family ipv4 unicast
      redistribute direct route-map <VRF>:DIRECT->BGP
      redistribute static route-map <VRF>:STATIC->BGP
"""

MODEL_CONFIG_CE_NEXUS_PEER_CE="""!
    neighbor <IP_CE_OTHER> remote-as <AS_BGP>
      bfd
      description Peer iBGP <VRF> <OTHER_CE>
      password <PASSWORD>
      timers 5 15
      address-family ipv4 unicast
        send-community both
        next-hop-self
        soft-reconfiguration inbound
!
"""

MODEL_CONFIG_CE_IOS_PEER_CE="""!
     neighbor <IP_CE_OTHER> remote-as <AS_BGP>
     neighbor <IP_CE_OTHER> description Peer iBGP <VRF> <OTHER_CE>
     neighbor <IP_CE_OTHER> password <PASSWORD>
     neighbor <IP_CE_OTHER> activate
     neighbor <IP_CE_OTHER> send-community both
     neighbor <IP_CE_OTHER> next-hop-self
     neighbor <IP_CE_OTHER> soft-reconfiguration inbound
   exit-address-family
!
"""

MODEL_CONFIG_RR="""!
vrf <VRF>
 address-family ipv4 unicast
  import route-target
   <RT>
  !
 !
router bgp 64911
 vrf <VRF>
  rd <RD>
  address-family ipv4 unicast
  !
!
"""

MODEL_INTERFACE_XR="""!
interface <INTERFACE>.<TAG>
 description <> BBN_<CE>_<INTERFACE_CE>
 vrf <VRF>
 ipv4 address <IP> 255.255.255.252
 arp timeout 180
 encapsulation dot1q <TAG>

!
"""

MODEL_INTERFACE_NX="""!
interface <INTERFACE>.<VLAN>
  bfd interval 500 min_rx 500 multiplier 3
  description <> FED_<NEIGHBOR>_<INTERFACE_NEIGHBOR>
  encapsulation dot1q <TAG>
  logging event port link-status
  vrf member <VRF>
  no ip redirects
  ip address <IP>/30
  no ipv6 redirects
  no shutdown
!
"""
MODEL_INTERFACE_IOS_PE_CE="""!
interface <INTERFACE>.<VLAN>
  description <> FED_<NEIGHBOR>_<INTERFACE_NEIGHBOR>
  ip vrf forwarding <VRF>
  ip address <IP> 255.255.255.252
  bfd interval 500 min_rx 500 multiplier 3
  arp timeout 3600
  no shutdown
!
"""
MODEL_INTERFACE_IOS_CE_CE="""!
interface Vlan<VLAN>
  description <> FED_<NEIGHBOR>_<INTERFACE_NEIGHBOR>
  logging event port link-status
  ip vrf forwarding <VRF>
  ip address <IP> 255.255.255.252
  no ip redirects
  no ip proxy-arp
  arp timeout 3600
  no shutdown
!
"""

MODEL_INTERFACE_LOOPBACK_XR="""!
interface Loopback<ID_VRF>
 description LBK_<VRF>_<PE>
 vrf <VRF>
 ipv4 address <IP_LOOPBACK> 255.255.255.255
 """
 
MODEL_INTERFACE_LOOPBACK_NX="""!
interface Loopback<ID_VRF>
 description LBK_<VRF>_<CE>
 vrf member <VRF>
 ip address <IP_LOOPBACK> 255.255.255.255
"""

MODEL_INTERFACE_LOOPBACK_IOS="""!
interface Loopback<ID_VRF>
 description LBK_<VRF>_<CE>
 ip vrf forwarding <VRF>
 ip address <IP_LOOPBACK> 255.255.255.255
"""
 
MODEL_BGP_PEER_XR="""! 
  vrf <VRF>
  rd <RD>
  bgp router-id <ROUTER_ID>
  address-family ipv4 unicast
   maximum-paths ibgp 4
   redistribute connected
  !
  neighbor <IP_CE>
   remote-as <REMOTE_AS>
   bfd fast-detect
   bfd multiplier 3
   bfd minimum-interval 500
   password <PASSWORD>
   description Peer eBGP <VRF> <CE>
   address-family ipv4 unicast
    send-community-ebgp
    route-policy <ROUTE_POLICY_IN> in
    route-policy <ROUTE_POLICY_OUT> out
    as-override
    send-extended-community-ebgp
    soft-reconfiguration inbound
	{ if default default-originate route-policy <ROUTE_POLICY_DEFAULT_ORIGINATE> }
    site-of-origin <SOO>
   !
  !
 !
!
"""


MODEL_CONFIG_VRF_PE="""!
!
vrf <VRF>
 address-family ipv4 unicast
  import route-target
   <RT>
  !
  export route-target
   <RT>
  !
 !
 """
 
MODEL_CONFIG_VRF_NX="""!
!
vrf context <VRF>
!
"""

MODEL_CONFIG_VRF_IOS="""!
!
ip vrf <VRF>
  rd <RD>
!
"""
 

MODEL_PO_NX="""

feature bgp
feature bfd
feature lacp
 
cli alias name wr copy run start

interface eth2/1-2
  description <> <NEIGHBOR>
  channel-group 10 mode active

interface po10
 description <> <NEIGHBOR>
 no shut
"""

MODEL_PO_IOS="""


interface <INTERFACE_SRC>
 switchport trunk allowed vlan add <VLAN>
"""


MODEL_INT_PHYSIQUE="""
!
interface <INTERFACE_SRC>
 description <> <VRF>_<NEIGHBOR>_<INTERFACE_DST>
 cdp
 service-policy input 10GE_PMAP_IN
 service-policy output 10GE_PMAP_OUT
 ethernet udld
  mode aggressive
!
"""

def compZero(min,id):
	return (min-len(id))*'0'+id

class intercoIP(Network):
	def __init__(self,net__):
		try:
			Network.__init__(self,net__)
		except:
			pdb.set_trace()
		
	def __add__(self,incr):
		return str(self.network()+incr)
	
class VRF(object):
	def __init__(self,nom="RVP_TBD",id='0',env="PROD",loopback="0.0.0.0",asCE="64919",type_ce="NEXUS"):
		self.nom=nom
		self.id=id
		self.env=env
		self.loopback=loopback
		self.type_ce=type_ce
		self.asCe=asCE
		
	def getRD(self):
		octet=self.loopback.split('.')
		return "64911:"+CODE_ENV[self.env]+compZero(3,self.id)+octet[1][-1]+octet[2][-1]+compZero(3,octet[3])
		
	def getRD_CE(self,asCE):
		octet=self.loopback.split('.')
		return self.asCe+":"+CODE_ENV[self.env]+compZero(3,self.id)+octet[1][-1]+octet[2][-1]+compZero(3,octet[3])
		
	def getRT(self):
		octet=self.loopback.split('.')
		return "64911:"+CODE_ENV[self.env]+compZero(3,self.id)+"00000"
		
	def getConf_PE(self):
		VRF=self.nom
		RT=self.getRT()
		LISTE_PARAM_VRF=(('VRF',VRF),('RT',RT))
		return configTemplate(MODEL_CONFIG_VRF_PE).replace(LISTE_PARAM_VRF)

	def getConf_CE(self):
		VRF_=self.nom
		
		if self.type_ce=="NEXUS":
			LISTE_PARAM_VRF=(('VRF',VRF_),('VRF',VRF_))
			return configTemplate(MODEL_CONFIG_VRF_NX).replace(LISTE_PARAM_VRF)
		elif self.type_ce=="IOS":
			RD=self.getRD_CE(self.asCe)	
			LISTE_PARAM_VRF=(('VRF',VRF_),('RD',RD))
			return configTemplate(MODEL_CONFIG_VRF_IOS).replace(LISTE_PARAM_VRF)
			
class routePolicy(object):
	def __init__(self,parity="IMPAIR",ce="RtrEnv-01"):
		self.color=CODE_COLOR[parity]
		self.parity=parity
		self.ce=ce
		self.nom_in=self.getName('IN')
		self.nom_out=self.getName('OUT')
		self.nom_default=self.getName('DEFAULT-ORIGINATE')
			
	
	def init_rp_type(self,type="IN"):
		resultat=io.StringIO()
		if type=='IN':
			self.nom="eBGP:"+self.color+"-PLAN-FROM-"+self.ce+":IN"
			resultat.write("route-policy "+self.nom_in+"\n")
			if self.color=="BLUE":
				resultat.write("  pass\n")		
				resultat.write("end-policy\n")
			elif self.color=="RED":
				resultat.write("  set local-preference 50\n")
				resultat.write("end-policy\n")
		elif type=='OUT':
			self.nom="eBGP:"+self.color+"-PLAN-TO-"+self.ce+":OUT"
			resultat.write("route-policy "+self.nom_out+"\n")
			if self.color=="BLUE":
				resultat.write("  pass\n")
				resultat.write("end-policy\n")
			elif self.color=="RED":
				resultat.write("  prepend as-path 64911 5\n")
				resultat.write("end-policy\n")
		elif type=='DEFAULT-ORIGINATE':
			self.nom="Prepend:"+self.color+"-PLAN-TO-"+self.ce
			resultat.write("route-policy "+self.nom_default+"\n")
			if self.color=="BLUE":
				resultat.write("  pass\n")
				resultat.write("end-policy\n")
			elif self.color=="RED":
				resultat.write("  prepend as-path 64911 5\n")
				resultat.write("end-policy\n")

				
		resultat_str=resultat.getvalue()
		resultat.close()

		return resultat_str
		
	def init_rp(self):
		resultat=io.StringIO()
		for type__ in [ 'IN' , 'OUT' , 'DEFAULT-ORIGINATE' ]:
			resultat.write(self.init_rp_type(type__))
		
		#pdb.set_trace()
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
	
	def getName(self,type):
		resultat=""
		if type=='IN':
			resultat="eBGP:"+self.color+"-PLAN-FROM-"+self.ce+":IN"
		elif type=='OUT':
			resultat="eBGP:"+self.color+"-PLAN-TO-"+self.ce+":OUT"
		elif type=='DEFAULT-ORIGINATE':
			resultat="Prepend:"+self.color+"-PLAN-TO-"+self.ce
		
		return resultat
			
class configTemplate(object):
	"Classe template de configuration"
	def __init__(self,str):
		self.template=str
		
	def replace(self,liste_parametre):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		
		resultat=ParseTemplate(self.template,liste_parametre)
		
		#resultat=self.template
        #
		#for (param,valeur) in liste_parametre:
		#	#print("PARAM:{0} VALEUR:{1}".format(param,valeur))
		#	try:
		#		resultat=resultat.replace("<"+param+">",valeur)
		#	except:
		#		#pass
		#		pdb.set_trace()
		#	
		return resultat
		
class ipError(Exception):
	"Classe Exception pour IP"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		

		self.message[0]=u'Erreur inconnue ou non traitee'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un reseau IPV4 valide'
		self.message[3]=u'Le reseau d\'interconnection:'+value1+u' n\'est trop petit,valeur max:\\'+value2.__str__()
		self.message[4]='uformat attendu pour les interconnexions VL1800:192.168.10.128/25. La valeur '+value1.__str__()+u' n\'est pas conforme'
		super(ipError, self).__init__(self.message[code])
		
		
class nxk(object):
	def __init__(self,nom="TBD",vrf="RVP_TBD",loopback="0.0.0.0",interco_PE={"PE":"NOM","NET":"192.2.2.0/30","SOO":"192.6.6.6:64666","INTERFACE_SRC":"EthX/X","TAG":"666","INTERFACE_DST":"EthX/X"},interco_CE={"CE":"NOM","NET":"192.2.2.0/30","INTERFACE_SRC":"EthX/X","INTERFACE_SRC":"EthX/X","TAG":"666"},bgpAs="64666"):
		"Constructeur "
		
		self.nom=nom
		self.vrf=vrf
		self.interco_CE=interco_CE
		self.interco_PE=interco_PE
		self.bgpAs=bgpAs
		self.parity=self.getParity()		
	
		
	def __str__(self):
		"Affichage"
		
		result='#####################################################'+'\n'
		result+='NOMs:'+self.nom+'\n'
		result+='VRF:'+self.vrf+'\n'
		result+='#####################################################'+'\n\n\n'
		
		return result
	
	def getParity(self):
		result=""
		
		
		if self.nom not in PARITY_SPEC.keys():
			if int(self.nom[-1]) % 2 == 0:
				result="PAIR"
			elif int(self.nom[-1]) % 2 == 1:
				result="IMPAIR"
		else:
			if PARITY_SPEC[self.nom]==1:
				result="IMPAIR"
			elif PARITY_SPEC[self.nom]==2:
				result="PAIR"
			else:
				raise ValueError('Parité non prise en compte')
			
			
		return result	
	
	def init_config(self):
		
		VRF=self.vrf
		AS_BGP=self.bgpAs
		IP_PE=intercoIP(self.interco_PE['INTER'])+1
		PE=self.interco_PE['PE']
		PASSWORD="INTERCO_RCSG_"+self.vrf
		OTHER_CE=interco_CE["CE"]
		LISTE_PARAM_NXK=(('VRF',VRF),
						('AS_BGP',AS_BGP),
						('IP_PE',IP_PE),
						('PE',PE),
						('PASSWORD',PASSWORD),
						('OTHER_CE',OTHER_CE))

		#Config interface PE-CE
		INTERFACE=self.interco_PE['INTERFACE_SRC']
		INTERFACE_NEIGHBOR=self.interco_PE['INTERFACE_DST']
		NEIGHBOR=self.interco_PE['PE']
		IP=intercoIP(self.interco_PE['NET'])+2
		TAG=(int(self.interco_PE['TAG'])%3000).__str__()
		
		LISTE_PARAM_INT_PE_CE=(('INTERFACE',INTERFACE),
						 ('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
						 ('NEIGHBOR',NEIGHBOR),
						 ('IP',IP),
						 ('VRF',VRF),
						 ('TAG',TAG))
		
		#Config interface CE-CE
		INTERFACE=self.interco_CE['INTERFACE_SRC']
		INTERFACE_NEIGHBOR=self.interco_CE['INTERFACE_DST']
		NEIGHBOR=self.interco_CE['CE']
		if self.parity == "IMPAIR":
			IP=intercoIP(self.interco_CE['NET'])+1
		elif self.parity == "IMPAIR":
			IP=intercoIP(self.interco_CE['NET'])+2
		TAG=self.interco_CE['TAG']
		
		LISTE_PARAM_INT_PE_CE=(('INTERFACE',INTERFACE),
						 ('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
						 ('NEIGHBOR',NEIGHBOR),
						 ('IP',IP),
						 ('VRF',VRF),
						 ('TAG',TAG))
						 
		return configTemplate(MODEL_INTERFACE_NX).replace(LISTE_PARAM_INT_PE_CE)+"\n"+configTemplate(MODEL_INTERFACE_NX).replace(LISTE_PARAM_INT_CE_CE)+"\n"+configTemplate(MODEL_CONFIG_N5K).replace(LISTE_PARAM_N5K)
		
	def init_config_interface(self):
		
		VRF=self.vrf
		
		resultat=""
		
		if self.interco_PE and not self.interco_CE:

			#Config interface PE-CE
			INTERFACE=self.interco_PE['INTERFACE_SRC']
			INTERFACE_NEIGHBOR=self.interco_PE['INTERFACE_DST']
			NEIGHBOR=self.interco_PE['PE']
			IP=intercoIP(self.interco_PE['NET'])+2
			TAG=self.interco_PE['TAG']
			VLAN=(int(self.interco_PE['TAG'])%1000).__str__()
			
			LISTE_PARAM_INT_PE_CE=(('INTERFACE',INTERFACE),
							('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
							('NEIGHBOR',NEIGHBOR),
							('IP',IP),
							('VRF',VRF),
							('VLAN',VLAN),
							('TAG',TAG))
			
			resultat=configTemplate(MODEL_INTERFACE_NX).replace(LISTE_PARAM_INT_PE_CE)
			print(INTERFACE)
			
		elif self.interco_CE and not self.interco_PE:
			#Config interface CE-CE
			INTERFACE=self.interco_CE['INTERFACE_SRC']
			INTERFACE_NEIGHBOR=self.interco_CE['INTERFACE_DST']
			NEIGHBOR=self.interco_CE['CE']
			IP=None
			if self.parity == "IMPAIR":
				IP=intercoIP(self.interco_CE['NET'])+1
			elif self.parity == "PAIR":
				IP=intercoIP(self.interco_CE['NET'])+2
			TAG=self.interco_CE['TAG']
			VLAN=TAG
			
			LISTE_PARAM_INT_CE_CE=(('INTERFACE',INTERFACE),
							('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
							('NEIGHBOR',NEIGHBOR),
							('IP',IP),
							('VRF',VRF),
							('VLAN',VLAN),
							('TAG',TAG))
			resultat=configTemplate(MODEL_INTERFACE_NX).replace(LISTE_PARAM_INT_CE_CE)
							
		return resultat
		
	def init_config_bgp(self):
		
		VRF=self.vrf
		AS_BGP=self.bgpAs
		PASSWORD="INTERCO_RCSG_"+self.vrf
		resultat=""
		
		
		if self.interco_PE and not self.interco_CE:
			IP_PE=intercoIP(self.interco_PE['NET'])+1
			PE=self.interco_PE['PE']
			PASSWORD="INTERCO_RCSG_"+self.vrf
			LISTE_PARAM_NXK=(('VRF',VRF),
							('IP_PE',IP_PE),
							('PE',PE),
							('PASSWORD',PASSWORD))
	
			resultat=configTemplate(MODEL_CONFIG_CE_NEXUS_PEER_PE).replace(LISTE_PARAM_NXK)
			
		elif self.interco_CE and not self.interco_PE:
			OTHER_CE=self.interco_CE['CE']
			IP_CE_OTHER=None
			if self.parity == "IMPAIR":
				IP_CE_OTHER=intercoIP(self.interco_CE['NET'])+2
			elif self.parity == "PAIR":
				IP_CE_OTHER=intercoIP(self.interco_CE['NET'])+1
			
			LISTE_PARAM_NXK=(('VRF',VRF),
						('AS_BGP',AS_BGP),
						('PASSWORD',PASSWORD),
						('IP_CE_OTHER',IP_CE_OTHER),
						('OTHER_CE',OTHER_CE))
						
			resultat=configTemplate(MODEL_CONFIG_CE_NEXUS_PEER_CE).replace(LISTE_PARAM_NXK)
							
		return resultat
		
class catalyst(object):
	def __init__(self,nom="TBD",vrf="RVP_TBD",loopback="0.0.0.0",interco_PE={"PE":"NOM","NET":"192.2.2.0/30","SOO":"192.6.6.6:64666","INTERFACE_SRC":"EthX/X","TAG":"666","INTERFACE_DST":"EthX/X"},interco_CE={"CE":"NOM","NET":"192.2.2.0/30","INTERFACE_SRC":"EthX/X","INTERFACE_SRC":"EthX/X","TAG":"666"},bgpAs="64666",idVrf="",env="PROD"):
		"Constructeur "
		
		self.nom=nom
		self.vrf=vrf
		self.interco_CE=interco_CE
		self.interco_PE=interco_PE
		self.bgpAs=bgpAs
		self.env=env
		self.parity=self.getParity()
		self.intParity=self.getintParity()
		self.vrfObj=VRF(vrf,idVrf,self.env,loopback,self.bgpAs)
		self.rd=self.vrfObj.getRD()
		
	
		
	def __str__(self):
		"Affichage"
		
		result='#####################################################'+'\n'
		result+='NOMs:'+self.nom+'\n'
		result+='VRF:'+self.vrf+'\n'
		result+='#####################################################'+'\n\n\n'
		
		return result
	
	def getParity(self):
		result=""
		
		if self.nom not in PARITY_SPEC.keys():
			if int(self.nom[-1]) % 2 == 0:
				result="PAIR"
			elif int(self.nom[-1]) % 2 == 1:
				result="IMPAIR"
		else:
			if PARITY_SPEC[self.nom]==1:
				result="IMPAIR"
			elif PARITY_SPEC[self.nom]==2:
				result="PAIR"
			else:
				raise ValueError('Parité non prise en compte')
				
		return result
		

		
	def getintParity(self):
		result=0
		
		if self.nom not in PARITY_SPEC.keys():
			if int(self.nom[-1]) % 2 == 0:
				result=1
			elif int(self.nom[-1]) % 2 == 1:
				result=2
		else:
			result=PARITY_SPEC[self.nom]
			
		return result	
	
	def init_config(self):
		
		VRF=self.vrf
		AS_BGP=self.bgpAs
		IP_PE=intercoIP(self.interco_PE['INTER'])+1
		PE=self.interco_PE['PE']
		PASSWORD="INTERCO_RCSG_"+self.vrf
		RD=self.rd
		OTHER_CE=interco_CE["CE"]
		LISTE_PARAM_CAT=(('VRF',VRF),
						('AS_BGP',AS_BGP),
						('IP_PE',IP_PE),
						('PE',PE),
						('PASSWORD',PASSWORD),
						('RD',RD),
						('OTHER_CE',OTHER_CE))

		#Config interface PE-CE
		INTERFACE=self.interco_PE['INTERFACE_SRC']
		INTERFACE_NEIGHBOR=self.interco_PE['INTERFACE_DST']
		NEIGHBOR=self.interco_PE['PE']
		IP=intercoIP(self.interco_PE['NET'])+2
		TAG=(int(self.interco_PE['TAG'])+(self.intParity-1)).__str__()
		TAG_CE_CE=(int(self.interco_PE['TAG'])+2).__str__()
		LISTE_PARAM_INT_PE_CE=(('INTERFACE',INTERFACE),
						 ('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
						 ('NEIGHBOR',NEIGHBOR),
						 ('IP',IP),
						 ('VRF',VRF),
						 ('TAG',TAG))
		
		#Config interface CE-CE
		INTERFACE=self.interco_CE['INTERFACE_SRC']
		INTERFACE_NEIGHBOR=self.interco_CE['INTERFACE_DST']
		NEIGHBOR=self.interco_CE['CE']
		if self.parity == "IMPAIR":
			IP=intercoIP(self.interco_CE['NET'])+1
		elif self.parity == "IMPAIR":
			IP=intercoIP(self.interco_CE['NET'])+2
			
		TAG=TAG_CE_CE
		
		LISTE_PARAM_INT_PE_CE=(('INTERFACE',INTERFACE),
						 ('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
						 ('NEIGHBOR',NEIGHBOR),
						 ('IP',IP),
						 ('VRF',VRF),
						 ('TAG',TAG))
						 
		return configTemplate(MODEL_INTERFACE_NX).replace(MODEL_INTERFACE_IOS_CE_CE)+"\n"+configTemplate(MODEL_INTERFACE_IOS_PE_CE).replace(LISTE_PARAM_INT_CE_CE)+"\n"+configTemplate(MODEL_CONFIG_CAT).replace(LISTE_PARAM_CAT)
		
	def init_config_interface(self):
		
		VRF=self.vrf
		
		resultat=""
		
		if self.interco_PE and not self.interco_CE:

			#Config interface PE-CE
			INTERFACE=self.interco_PE['INTERFACE_SRC']
			INTERFACE_NEIGHBOR=self.interco_PE['INTERFACE_DST']
			NEIGHBOR=self.interco_PE['PE']
			IP=intercoIP(self.interco_PE['NET'])+2
			TAG=self.interco_PE['TAG']
			VLAN=(int(self.interco_PE['TAG'])+(self.intParity-1)).__str__()
			LISTE_PARAM_INT_PE_CE=(('INTERFACE',INTERFACE),
							('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
							('NEIGHBOR',NEIGHBOR),
							('IP',IP),
							('VRF',VRF),
							('VLAN',VLAN),
							('TAG',TAG))
			
			resultat=configTemplate(MODEL_INTERFACE_IOS_PE_CE).replace(LISTE_PARAM_INT_PE_CE)
			print(INTERFACE)
			
		elif self.interco_CE and not self.interco_PE:
			#Config interface CE-CE
			INTERFACE=self.interco_CE['INTERFACE_SRC']
			INTERFACE_NEIGHBOR=self.interco_CE['INTERFACE_DST']
			NEIGHBOR=self.interco_CE['CE']
			IP=None
			if self.parity == "IMPAIR":
				IP=intercoIP(self.interco_CE['NET'])+1
			elif self.parity == "PAIR":
				IP=intercoIP(self.interco_CE['NET'])+2
			TAG=self.interco_CE['TAG']
			VLAN=self.interco_CE['TAG']

			LISTE_PARAM_INT_CE_CE=(('INTERFACE',INTERFACE),
							('INTERFACE_NEIGHBOR',INTERFACE_NEIGHBOR),
							('NEIGHBOR',NEIGHBOR),
							('IP',IP),
							('VRF',VRF),
							('VLAN',VLAN),
							('TAG',TAG))
			resultat=configTemplate(MODEL_INTERFACE_IOS_CE_CE).replace(LISTE_PARAM_INT_CE_CE)
							
		return resultat
		
	def init_config_bgp(self):
		
		VRF=self.vrf
		AS_BGP=self.bgpAs
		PASSWORD="INTERCO_RCSG_"+self.vrf
		resultat=""
		
		
		if self.interco_PE and not self.interco_CE:
			IP_PE=intercoIP(self.interco_PE['NET'])+1
			PE=self.interco_PE['PE']
			PASSWORD="INTERCO_RCSG_"+self.vrf
			LISTE_PARAM_CAT=(('VRF',VRF),
							('IP_PE',IP_PE),
							('PE',PE),
							('PASSWORD',PASSWORD))
	
			resultat=configTemplate(MODEL_CONFIG_CE_IOS_PEER_PE).replace(LISTE_PARAM_CAT)
			
		elif self.interco_CE and not self.interco_PE:
			OTHER_CE=self.interco_CE['CE']
			IP_CE_OTHER=None
			if self.parity == "IMPAIR":
				IP_CE_OTHER=intercoIP(self.interco_CE['NET'])+2
			elif self.parity == "PAIR":
				IP_CE_OTHER=intercoIP(self.interco_CE['NET'])+1
			
			LISTE_PARAM_CAT=(('VRF',VRF),
						('AS_BGP',AS_BGP),
						('PASSWORD',PASSWORD),
						('IP_CE_OTHER',IP_CE_OTHER),
						('OTHER_CE',OTHER_CE))
						
			resultat=configTemplate(MODEL_CONFIG_CE_IOS_PEER_CE).replace(LISTE_PARAM_CAT)
							
		return resultat
	
class RR(object):
	def __init__(self,nom="TBD",vrf="RVP_TBD",idVrf="65000",env="PROD"):
		"Constructeur "
		
		self.nom=nom
		self.env=env
		
		self.idVrf=idVrf
		
		self.vrf=VRF(vrf,idVrf,self.env,"0.0.0."+ID_PE[nom])
		self.rd=self.vrf.getRD()
		self.rt=self.vrf.getRT()
		
	
		
	def __str__(self):
		"Affichage"
		
		result='#####################################################'+'\n'
		result+='NOMs:'+self.nom+'\n'
		result+='Type RR:'+self.vrf.nom+' ID:'+self.idVrf+'\n'
		result+='#####################################################'+'\n\n\n'
		

	def init_config(self):
	
		VRF=self.vrf.nom
		RT=self.rt
		RD=self.rd
		
		
		LISTE_PARAM_RR=(('VRF',VRF),
						('RT',RT),
						('RD',RD))
		
		return configTemplate(MODEL_CONFIG_RR).replace(LISTE_PARAM_RR)
		
class PE(object):
	def __init__(self,nom="TBD",vrf="RVP_TBD",idVrf="666",env="PROD",loopback="0.0.0.0",Remote_BgpAs="77777:77777777",interco_CE={"CE":"NOM","NET":"192.2.2.0/30","SOO":"192.6.6.6:64666","VLAN":"666","INTERFACE":"EthX/X","TAG":"666","INTERFACE_CE":"Eth3/3"},default=False):
		"Constructeur "
		
		self.nom=nom
		self.vrf=VRF(vrf,idVrf,env,loopback)
		self.idVrf=idVrf
		self.loopback=loopback
		self.rd=self.vrf.getRD()
		self.rt=self.vrf.getRT()
		self.env=env
		self.interco_CE=interco_CE
		self.parity=self.getParity()
		self.Remote_BgpAs=Remote_BgpAs
		self.default=default
	
		
	def __str__(self):
		"Affichage"
		
		result='#####################################################'+'\n'
		result+='NOMs:'+self.nom+'\n'
		result+='Type PE:'+self.vrf.nom+' Loopback:'+self.loopback+'\n'
		result+='#####################################################'+'\n\n\n'
		
		
	def getParity(self):
		result=""
		if not self.nom in PARITY_SPEC.keys():
			if int(self.nom[-1]) % 2 == 0:
				result="PAIR"
			elif int(self.nom[-1]) % 2 == 1:
				result="IMPAIR"
		else:
			if PARITY_SPEC[self.nom]==1:
				result="IMPAIR"
			elif PARITY_SPEC[self.nom]==2:
				result="PAIR"
			else:
				raise ValueError('Parité non prise en compte')
			
		return result
		
		
		
	def init_config(self):
	
		VRF=self.vrf.nom
		RT=self.rt
		RD=self.rd
		ID_VRF=self.idVrf
		PE=self.nom.upper()
		IP_LOOPBACK=self.loopback
		IP_CE=intercoIP(self.interco_CE['NET'])+2
		ROUTER_ID=self.loopback
		PASSWORD="INTERCO_RCSG_"+self.vrf.nom
		SOO=self.interco_CE["SOO"]
		RP_cur=routePolicy(self.parity,self.interco_CE['CE'])
		ROUTE_POLICY_IN=RP_cur.getName('IN')
		ROUTE_POLICY_OUT=RP_cur.getName('OUT')
		ROUTE_POLICY_DEFAULT_ORIGINATE=RP_cur.getName('DEFAULT-ORIGINATE')
		REMOTE_AS=self.Remote_BgpAs
		LISTE_PARAM_PE=(('VRF',VRF),
						('RT',RT),
						('RD',RD),
						('ID_VRF',ID_VRF),
						('PE',PE),
						('IP_LOOPBACK',IP_LOOPBACK),
						('IP_CE',IP_CE),
						('ROUTER_ID',ROUTER_ID),
						('PASSWORD',PASSWORD),
						('SOO',SOO),
						('REMOTE_AS',REMOTE_AS),
						('ROUTE_POLICY_IN',ROUTE_POLICY_IN),
						('ROUTE_POLICY_OUT',ROUTE_POLICY_OUT),
						('default',self.default),
						('ROUTE_POLICY_DEFAULT_ORIGINATE',ROUTE_POLICY_DEFAULT_ORIGINATE))
						
		
		INTERFACE=self.interco_CE['INTERFACE']
		INTERFACE_CE=self.interco_CE['INTERFACE_CE']
		CE=self.interco_CE['CE']
		IP=intercoIP(self.interco_CE['NET'])+1
		TAG=self.interco_CE['TAG']
		
		LISTE_PARAM_INT=(('INTERFACE',INTERFACE),
						 ('INTERFACE_CE',INTERFACE_CE),
						 ('CE',CE),
						 ('IP',IP),
						 ('VRF',VRF),
						 ('TAG',TAG))
		
		return RP_cur.init_rp()+'\n'+configTemplate(MODEL_INTERFACE_XR).replace(LISTE_PARAM_INT)+"\n"+configTemplate(MODEL_CONFIG_PE).replace(LISTE_PARAM_PE)
		
	def init_config_bgp(self):
	
		VRF=self.vrf.nom
		RD=self.rd
		ID_VRF=self.idVrf
		IP_CE=intercoIP(self.interco_CE['NET'])+2
		ROUTER_ID=self.loopback
		PASSWORD="INTERCO_RCSG_"+self.vrf.nom
		SOO=self.interco_CE["SOO"]
		RP_cur=routePolicy(self.parity,self.interco_CE['CE'])
		ROUTE_POLICY_IN=RP_cur.getName('IN')
		ROUTE_POLICY_OUT=RP_cur.getName('OUT')
		ROUTE_POLICY_DEFAULT_ORIGINATE=RP_cur.getName('DEFAULT-ORIGINATE')
		REMOTE_AS=self.Remote_BgpAs
		CE=self.interco_CE['CE']
		LISTE_PARAM_PE=(('VRF',VRF),
						('RD',RD),
						('ID_VRF',ID_VRF),
						('IP_CE',IP_CE),
						('ROUTER_ID',ROUTER_ID),
						('PASSWORD',PASSWORD),
						('SOO',SOO),
						('REMOTE_AS',REMOTE_AS),
						('ROUTE_POLICY_IN',ROUTE_POLICY_IN),
						('ROUTE_POLICY_OUT',ROUTE_POLICY_OUT),
						('CE',CE),
						('default',self.default),
						('ROUTE_POLICY_DEFAULT_ORIGINATE',ROUTE_POLICY_DEFAULT_ORIGINATE))
		
		
		return configTemplate(MODEL_BGP_PEER_XR).replace(LISTE_PARAM_PE)

	def init_config_interface(self):
		#pdb.set_trace()
		VRF=self.vrf.nom
		INTERFACE=self.interco_CE['INTERFACE']
		INTERFACE_CE=self.interco_CE['INTERFACE_CE']
		CE=self.interco_CE['CE']
		IP=intercoIP(self.interco_CE['NET'])+1
		
		if self.interco_CE['TAG']=="NEXUS":
			TAG=self.interco_CE['TAG']
		else:
			if self.getParity()=="IMPAIR":
				TAG=self.interco_CE['TAG']
			else:
				TAG=str(int(self.interco_CE['TAG'])+1)
				
		LISTE_PARAM_INT=(('INTERFACE',INTERFACE),
						 ('INTERFACE_CE',INTERFACE_CE),
						 ('CE',CE),
						 ('IP',IP),
						 ('VRF',VRF),
						 ('TAG',TAG))
		
		return configTemplate(MODEL_INTERFACE_XR).replace(LISTE_PARAM_INT)
		
class VRFs(object):	
	def __init__(self,excel_file,bgpAs,options=[]):
	
		self.CE=[]
		self.PE=[]
		self.loopback_CE={}
		self.loopback_PE={}
		self.id_loopback={}
		self.id_loopback_ce={}
		self.vrfId={}
		self.vlanId={}
		self.vlanId_CE={}
		self.peers=[]
		self.soo={}
		self.bgpAs=bgpAs
		self.options=options	
		if "DEFAULTROUTE" in self.options:
			self.default=True
			self.type_ce="IOS"
		else:
			self.default=False
			
			
		if "CE_IOS" in self.options:
			self.ceType=catalyst
			self.type_ce="IOS"
		else:
			self.ceType=nxk
			self.type_ce="NEXUS"
			
		wb=xlrd.open_workbook(excel_file)
		sh_int = wb.sheet_by_name(u'INTERCO')
		sh_vrf = wb.sheet_by_name(u'VRF')
		sh_loopback = wb.sheet_by_name(u'LOOPBACK')
		sh_id_loop= wb.sheet_by_name(u'ID_LOOP')
		
		self.configs={}
		self.configsBgp={}
		self.init_id_loopback(sh_id_loop)
		self.init_id_loopback_ce(sh_loopback)
		self.init_loopback_CE()
		self.init_loopback_PE()
		self.init_vrfID(sh_id_loop)

		self.init_vlanID(sh_vrf)
		self.init_peers(sh_int)
		self.init_soo(sh_int)
		
		self.config_vrf()
		self.config_loopback()
		self.config_interface()
		self.config_rp()
		self.config_bgp()

		
	def __str__(self):
		resultat=""
		for pe in self.peers:
			resultat+=pe.__str__()

		return resultat
		
	def get_type_equipement(self,equipement):
		type="CE"
		if  equipement in ID_PE.keys():
			type="PE"
			if equipement[-1]=='0':
				type="RR"
		return type
		
	def get_bck_equipement(self,equipement):
			
		return COUPLE_CE[equipement]
		
	def getParity(self,nom):
		result=""
		
		if nom not in PARITY_SPEC.keys():
			if int(nom[-1]) % 2 == 0:
				result="PAIR"
			elif int(nom[-1]) % 2 == 1:
				result="IMPAIR"
		else:
			if PARITY_SPEC[nom]==1:
				result="IMPAIR"
			elif PARITY_SPEC[nom]==2:
				result="PAIR"
			else:
				raise ValueError('Parité non prise en compte')
			
				
			
		return result
		
	def init_id_loopback(self,worksheet):
		for rownum in range(2,worksheet.nrows):
			#print(worksheet.row_values(rownum))
			self.id_loopback[worksheet.row_values(rownum)[1].strip()]={'1':worksheet.row_values(rownum)[3].__int__().__str__().strip(),'2':worksheet.row_values(rownum)[4].__int__().__str__().strip(),'3':worksheet.row_values(rownum)[5].__int__().__str__().strip()}
		#print(self.id_loopback)

	def init_id_loopback_ce(self,worksheet):
		for rownum in range(2,worksheet.nrows):
			#print(worksheet.row_values(rownum))
			try:
				self.id_loopback_ce[worksheet.row_values(rownum)[1].strip()]={'1':worksheet.row_values(rownum)[3].__int__().__str__().strip(),'2':worksheet.row_values(rownum)[4].__int__().__str__().strip(),'3':worksheet.row_values(rownum)[5].__int__().__str__().strip()}
			except IndexError as e:
				pdb.set_trace()
				print(e)
		#print(self.id_loopback)

		
		
	def init_loopback_PE(self):
		
		for pe__ in ID_PE.keys():
			for vrf__ in self.id_loopback.keys():
				try:
					self.loopback_PE[pe__][vrf__]=self.id_loopback[vrf__]['1']+"."+self.id_loopback[vrf__]['2']+"."+self.id_loopback[vrf__]['3']+"."+ID_PE[pe__]
				except KeyError:
					self.loopback_PE[pe__]={}
					self.loopback_PE[pe__][vrf__]=self.id_loopback[vrf__]['1']+"."+self.id_loopback[vrf__]['2']+"."+self.id_loopback[vrf__]['3']+"."+ID_PE[pe__]
				
	def init_loopback_CE(self):
		
		for ce__ in ID_CE.keys():
			for vrf__ in self.id_loopback_ce.keys():
				try:
					self.loopback_CE[ce__][vrf__]=self.id_loopback_ce[vrf__]['1']+"."+self.id_loopback_ce[vrf__]['2']+"."+self.id_loopback_ce[vrf__]['3']+"."+ID_CE[ce__]
				except KeyError:
					self.loopback_CE[ce__]={}
					self.loopback_CE[ce__][vrf__]=self.id_loopback_ce[vrf__]['1']+"."+self.id_loopback_ce[vrf__]['2']+"."+self.id_loopback_ce[vrf__]['3']+"."+ID_CE[ce__]
		
	def init_vrfID(self,worksheet):
		
		for rownum in range(2,worksheet.nrows):
			#print(worksheet.row_values(rownum))
			self.vrfId[worksheet.row_values(rownum)[1].strip()]=worksheet.row_values(rownum)[0].__int__().__str__().strip()
		#print(self.vrfId)
		
	def init_vlanID(self,worksheet):
		
		for rownum in range(1,worksheet.nrows):
			#print(worksheet.row_values(rownum))
			self.vlanId[worksheet.row_values(rownum)[1].strip()]=worksheet.row_values(rownum)[2].__int__().__str__().strip()
			self.vlanId_CE[worksheet.row_values(rownum)[1].strip()]=worksheet.row_values(rownum)[3].__int__().__str__().strip()
		
	def init_peers(self,worksheet):
		for rownum in range(1,worksheet.nrows):
			#print(worksheet.row_values(rownum))
			self.peers.append({"VRF":worksheet.row_values(rownum)[1].strip(),"NET":worksheet.row_values(rownum)[2].strip(),"NOM":worksheet.row_values(rownum)[3].strip(),"PORT_SRC":worksheet.row_values(rownum)[5].strip(),"NEIGHBOR":worksheet.row_values(rownum)[6].strip(),"PORT_DST":worksheet.row_values(rownum)[8].strip(),"TYPE_CE":self.type_ce})
			self.peers.append({"VRF":worksheet.row_values(rownum)[1].strip(),"NET":worksheet.row_values(rownum)[2].strip(),"NOM":worksheet.row_values(rownum)[6].strip(),"PORT_SRC":worksheet.row_values(rownum)[8].strip(),"NEIGHBOR":worksheet.row_values(rownum)[3].strip(),"PORT_DST":worksheet.row_values(rownum)[5].strip(),"TYPE_CE":self.type_ce})
		#print(self.peers)
		
	def init_soo(self,worksheet):
	
		loopback="INCONNU"
		for rownum in range(1,worksheet.nrows):
			#print(worksheet.row_values(rownum))
			peer=worksheet.row_values(rownum)[3].strip()
			type=self.get_type_equipement(peer)
			if type == "PE":
				vrf=worksheet.row_values(rownum)[1].strip()
				neighbor=worksheet.row_values(rownum)[6].strip()
				parity=self.getParity(neighbor)
				if parity=="PAIR":
					loopback=self.loopback_CE[self.get_bck_equipement(neighbor)][vrf]
				elif parity=="IMPAIR":
					loopback=self.loopback_CE[neighbor][vrf]
					
				else:
					loopback="INCONNU"
			
			try:
				self.soo[peer][vrf]=loopback+":"+self.bgpAs
			except KeyError:
				self.soo[peer]={}
				self.soo[peer][vrf]=loopback+":"+self.bgpAs
			
			
		#print(self.soo)
		
		
	def config_loopback(self):
		for pe__ in self.loopback_PE.keys():
			if self.get_type_equipement(pe__) == "PE":
				for vrf__ in self.loopback_PE[pe__].keys():
					VRF=vrf__
					ID_VRF=self.vrfId[vrf__]
					PE=pe__
					IP_LOOPBACK=self.loopback_PE[pe__][vrf__]
					LISTE_PARAM_LOOPBACK=(('VRF',VRF),
										('ID_VRF',ID_VRF),
										('PE',PE),
										('IP_LOOPBACK',IP_LOOPBACK))
		
					self.write_config(pe__,configTemplate(MODEL_INTERFACE_LOOPBACK_XR).replace(LISTE_PARAM_LOOPBACK))
					
		for ce__ in self.loopback_CE.keys():
			if self.get_type_equipement(ce__) == "CE":
				for vrf__ in self.loopback_CE[ce__].keys():
					VRF=vrf__
					ID_VRF=self.vrfId[vrf__]
					CE=ce__
					IP_LOOPBACK=self.loopback_CE[ce__][vrf__]
					LISTE_PARAM_LOOPBACK=(('VRF',VRF),
										('ID_VRF',ID_VRF),
										('CE',CE),
										('IP_LOOPBACK',IP_LOOPBACK))
					if self.type_ce=="NEXUS":
						self.write_config(ce__,configTemplate(MODEL_INTERFACE_LOOPBACK_NX).replace(LISTE_PARAM_LOOPBACK))
					elif self.type_ce=="IOS":
						self.write_config(ce__,configTemplate(MODEL_INTERFACE_LOOPBACK_IOS).replace(LISTE_PARAM_LOOPBACK))
		#print(self.configs)
		
	def config_interface(self):
	
		for peer__ in self.peers:
			type__=self.get_type_equipement(peer__['NOM'])
			
			if type__=="PE":
				self.write_config(peer__['NOM'],PE(nom=peer__['NOM'],vrf=peer__['VRF'],idVrf=self.vrfId[peer__['VRF']],env="PROD",loopback=self.loopback_PE[peer__['NOM']][peer__['VRF']],Remote_BgpAs=self.bgpAs,interco_CE={"CE":peer__['NEIGHBOR'],"NET":peer__['NET'],"SOO":self.soo[peer__['NOM']][peer__['VRF']],"VLAN":self.vlanId[peer__['VRF']],"INTERFACE":peer__['PORT_SRC'],"TAG":self.vlanId[peer__['VRF']],"INTERFACE_CE":peer__['PORT_DST'],"TYPE_CE":peer__['TYPE_CE']},default=self.default).init_config_interface())
				
			
			if type__=="CE":
				type__neighbor=self.get_type_equipement(peer__['NEIGHBOR'])
				if type__neighbor=="PE":
					try:
						self.write_config(peer__['NOM'],self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={"PE":peer__['NEIGHBOR'],"NET":peer__['NET'],"SOO":self.soo[peer__['NEIGHBOR']][peer__['VRF']],"INTERFACE_SRC":peer__['PORT_SRC'],"TAG":self.vlanId[peer__['VRF']],"INTERFACE_DST":peer__['PORT_DST']},interco_CE={},bgpAs=self.bgpAs).init_config_interface())
					except KeyError:
						pdb.set_trace()
				elif type__neighbor=="CE":
					self.write_config(peer__['NOM'],self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={},interco_CE={"CE":COUPLE_CE[peer__['NOM']],"NET":peer__["NET"],"INTERFACE_SRC":peer__['PORT_SRC'],"INTERFACE_DST":peer__['PORT_DST'],"TAG":self.vlanId_CE[peer__['VRF']]},bgpAs=self.bgpAs).init_config_interface())
			
		#print(self.configs)

	def config_vrf(self):
		
		liste_vrf_done=[]
	
		for peer__ in self.peers:
			
			if (peer__['NOM'],peer__['VRF']) not in liste_vrf_done:
				liste_vrf_done.append((peer__['NOM'],peer__['VRF']))
				type__=self.get_type_equipement(peer__['NOM'])
				
				if type__=="PE":
					#pdb.set_trace()
					self.write_config(peer__['NOM'],VRF(nom=peer__['VRF'],id=self.vrfId[peer__['VRF']],loopback=self.loopback_PE[peer__['NOM']][peer__['VRF']]).getConf_PE())
					
				
				elif type__=="CE":
					self.write_config(peer__['NOM'],VRF(nom=peer__['VRF'],id=self.vrfId[peer__['VRF']],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],asCE=self.bgpAs,type_ce=peer__['TYPE_CE']).getConf_CE())
					
		
		if "ROUTEREFLECTOR" in self.options:
			for rr__ in RR_MAN.keys():
				for vrf__ in self.vrfId.keys():
					self.write_config(rr__,RR(nom=rr__,vrf=vrf__,idVrf=self.vrfId[vrf__],env="PROD").init_config())
				
		#print(self.configs)
		
	def config_rp(self):
		
		neighbor_done=[]
		ce_vrf_done=[]
	
		for peer__ in self.peers:
			type__=self.get_type_equipement(peer__['NOM'])
			parity=self.getParity(peer__['NOM'])
			if type__=="PE" and ( peer__['NEIGHBOR'] not in neighbor_done) :
				neighbor_done.append(peer__['NEIGHBOR'])
				RP_cur=routePolicy(parity,peer__['NEIGHBOR'])
				self.write_config(peer__['NOM'],RP_cur.init_rp())
				
			if type__=="CE" and ( peer__['NOM'],peer__['VRF']) not in ce_vrf_done :
				ce_vrf_done.append((peer__['NOM'],peer__['VRF']))
				if peer__['TYPE_CE']=="NEXUS":
					self.write_config(peer__['NOM'],"!\nroute-map "+peer__['VRF']+":DIRECT->BGP permit 100\n!\n")
					self.write_config(peer__['NOM'],"!\nroute-map "+peer__['VRF']+":STATIC->BGP permit 100\n!\n")
				elif peer__['TYPE_CE']=="IOS":
					self.write_config(peer__['NOM'],"!\nroute-map "+peer__['VRF']+":CONNECTED->BGP permit 100\n!\n")
					self.write_config(peer__['NOM'],"!\nroute-map "+peer__['VRF']+":STATIC->BGP permit 100\n!\n")
				else:
					raise ValueError('TYPE_CE non pris en compte')
		
	def config_bgp(self):
	
		liste_peer_started=[]
		temp_config_ce={}
		for peer__ in self.peers:
			type__=self.get_type_equipement(peer__['NOM'])
			
			if type__=="PE":
				if peer__['NOM'] not in liste_peer_started:
					liste_peer_started.append(peer__['NOM'])
					self.write_config(peer__['NOM'],"\n!\nrouter bgp 64911\n")
				self.write_config(peer__['NOM'],PE(nom=peer__['NOM'],vrf=peer__['VRF'],idVrf=self.vrfId[peer__['VRF']],env="PROD",loopback=self.loopback_PE[peer__['NOM']][peer__['VRF']],Remote_BgpAs=self.bgpAs,interco_CE={"CE":peer__['NEIGHBOR'],"NET":peer__['NET'],"SOO":self.soo[peer__['NOM']][peer__['VRF']],"VLAN":self.vlanId[peer__['VRF']],"INTERFACE":peer__['PORT_SRC'],"TAG":self.vlanId[peer__['VRF']],"INTERFACE_CE":peer__['PORT_DST']},default=self.default).init_config_bgp())
				
			
			if type__=="CE":
				type__neighbor=self.get_type_equipement(peer__['NEIGHBOR'])
				if peer__['NOM'] not in liste_peer_started:
					liste_peer_started.append(peer__['NOM'])
					self.write_config(peer__['NOM'],"\n!\nrouter bgp "+self.bgpAs+"\n")
				if type__neighbor=="PE":
					if peer__['NOM'] not in temp_config_ce.keys():
						temp_config_ce[peer__['NOM']]={}
					#self.write_config(peer__['NOM'],self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={"PE":peer__['NEIGHBOR'],"NET":peer__['NET'],"SOO":self.soo[peer__['NEIGHBOR']][peer__['VRF']],"INTERFACE_SRC":peer__['PORT_SRC'],"TAG":self.vlanId[peer__['VRF']],"INTERFACE_DST":peer__['PORT_DST']},interco_CE={},bgpAs=self.bgpAs).init_config_bgp())
					try:
						temp_config_ce[peer__['NOM']][peer__['VRF']]+=self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={"PE":peer__['NEIGHBOR'],"NET":peer__['NET'],"SOO":self.soo[peer__['NEIGHBOR']][peer__['VRF']],"INTERFACE_SRC":peer__['PORT_SRC'],"TAG":self.vlanId[peer__['VRF']],"INTERFACE_DST":peer__['PORT_DST']},interco_CE={},bgpAs=self.bgpAs).init_config_bgp()
					except KeyError as e:
						#print(e)
						#pdb.set_trace()
						temp_config_ce[peer__['NOM']][peer__['VRF']]=""
						temp_config_ce[peer__['NOM']][peer__['VRF']]+=self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={"PE":peer__['NEIGHBOR'],"NET":peer__['NET'],"SOO":self.soo[peer__['NEIGHBOR']][peer__['VRF']],"INTERFACE_SRC":peer__['PORT_SRC'],"TAG":self.vlanId[peer__['VRF']],"INTERFACE_DST":peer__['PORT_DST']},interco_CE={},bgpAs=self.bgpAs).init_config_bgp()
						
				elif type__neighbor=="CE":
					#self.write_config(peer__['NOM'],self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={},interco_CE={"CE":COUPLE_CE[peer__['NOM']],"NET":peer__["NET"],"INTERFACE_SRC":peer__['PORT_SRC'],"INTERFACE_DST":peer__['PORT_DST'],"TAG":self.vlanId[peer__['VRF']]},bgpAs=self.bgpAs).init_config_bgp())
					if peer__['NOM'] not in temp_config_ce.keys():
						temp_config_ce[peer__['NOM']]={}
					try:
						temp_config_ce[peer__['NOM']][peer__['VRF']]+=self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={},interco_CE={"CE":COUPLE_CE[peer__['NOM']],"NET":peer__["NET"],"INTERFACE_SRC":peer__['PORT_SRC'],"INTERFACE_DST":peer__['PORT_DST'],"TAG":self.vlanId[peer__['VRF']]},bgpAs=self.bgpAs).init_config_bgp()
					except KeyError as e:
						#print(e)
						temp_config_ce[peer__['NOM']][peer__['VRF']]=""
						temp_config_ce[peer__['NOM']][peer__['VRF']]+=self.ceType(nom=peer__['NOM'],vrf=peer__['VRF'],loopback=self.loopback_CE[peer__['NOM']][peer__['VRF']],interco_PE={},interco_CE={"CE":COUPLE_CE[peer__['NOM']],"NET":peer__["NET"],"INTERFACE_SRC":peer__['PORT_SRC'],"INTERFACE_DST":peer__['PORT_DST'],"TAG":self.vlanId[peer__['VRF']]},bgpAs=self.bgpAs).init_config_bgp()
			
		#pdb.set_trace()
		for ce__ in temp_config_ce.keys():
			for vrf__ in temp_config_ce[ce__].keys():
				VRF=vrf__
				ROUTER_ID=self.loopback_CE[ce__][vrf__]
				PARAM_BGP_VRF=(('VRF',VRF),
							('ROUTER_ID',ROUTER_ID))
				if self.type_ce=="NEXUS":
					self.write_config(ce__,configTemplate(MODEL_HEADER_BGP_VRF_NX).replace(PARAM_BGP_VRF))
				elif self.type_ce=="IOS":
					self.write_config(ce__,configTemplate(MODEL_HEADER_BGP_VRF_IOS).replace(PARAM_BGP_VRF))
				self.write_config(ce__,temp_config_ce[ce__][vrf__])
				
		#print(self.configs)

		
	def config_po_ce(self,repertoire):
		
		for pece__ in self.peers:
			if pece__['NOM'] in COUPLE_CE.keys() and pece__['NEIGHBOR'] in COUPLE_CE.keys():
				if pece__['TYPE_CE']=="NEXUS":
					NEIGHBOR=COUPLE_CE[pece__]
					PARAM=(('NEIGHBOR',NEIGHBOR),('NEIGHBOR',NEIGHBOR))
					self.save_file(ce__,configTemplate(MODEL_PO_NX).replace(PARAM),repertoire)
				elif pece__['TYPE_CE']=="IOS":
					PARAM=(('INTERFACE_SRC',pece__['PORT_SRC']),('VLAN',self.vlanId_CE[pece__['VRF']]))
					self.save_file(pece__['NOM'],configTemplate(MODEL_PO_IOS).replace(PARAM),repertoire)
			
	def config_int_phy_pe(self,repertoire):
		
		liste_pe_done=[]
		for peer__ in self.peers:
			type__=self.get_type_equipement(peer__['NOM'])
			if type__=="PE" and (peer__['NOM'],peer__['NEIGHBOR'],peer__['PORT_DST']) not in liste_pe_done:
				liste_pe_done.append((peer__['NOM'],peer__['NEIGHBOR'],peer__['PORT_DST']))
				INTERFACE_SRC=peer__['PORT_SRC']
				INTERFACE_DST=peer__['PORT_DST']
				NEIGHBOR=peer__['NEIGHBOR']
				PARAM=(('INTERFACE_SRC',INTERFACE_SRC),
						('INTERFACE_DST',INTERFACE_DST),
						('NEIGHBOR',NEIGHBOR))
						
				self.save_file(peer__['NOM'],configTemplate(MODEL_INT_PHYSIQUE).replace(PARAM),repertoire)
				
			
	def save_config(self,repertoire):
	
		if not os.path.exists(repertoire):
				os.makedirs(repertoire)
			
		for equipement in self.configs.keys():
			fichier_sauvegarde=equipement+'.cfg'

			with open(repertoire+'/'+fichier_sauvegarde,'w') as file:
				file.write(self.configs[equipement])
				
	def save_file(self,equipement,str,repertoire):
		if not os.path.exists(repertoire):
			os.makedirs(repertoire)
			
		fichier_sauvegarde=equipement+'.cfg'

		with open(repertoire+'/'+fichier_sauvegarde,'w') as file:
			file.write(str)
			
	def write_config(self,equipement,str):
		
		try:
			self.configs[equipement]+=str
		except KeyError:
			self.configs[equipement]=str
			
		
if __name__ == '__main__':
	"Fonction principale"	
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-e", "--excel",action="store",help="Excel File",required=True)
	group1.add_argument("-a", "--asbgp",action="store",help="AS BGP CE")
	parser.add_argument("-c", "--complement",action="store",help="sous repertoire avec configuration complementaire",required=False)
	parser.add_argument("-r", "--repertoire",action="store",help="Repertoire ou sauvegarder les configurations",required=False)
	parser.add_argument("-R", "--routereflector",action="store_true",help="Configuration des routes reflectors",required=False)
	parser.add_argument("-d", "--defaultroute",action="store_true",help="Annonce route par défaut",required=False)
	parser.add_argument("--ios", action="store_true",help="Confiugration type CE IOS",required=False)
	args = parser.parse_args()
	
	options=[]
	if args.routereflector:
		options.append("ROUTEREFLECTOR")
		
	if args.defaultroute:
		options.append("DEFAULTROUTE")
		print(args.defaultroute)
		
	if args.ios:
		options.append("CE_IOS")
		print(args.defaultroute)
	
	if args.excel and args.asbgp:
		vrf__=VRFs(args.excel,args.asbgp,options)


		if args.repertoire:
			vrf__.save_config(args.repertoire)
			
			if args.complement:
				vrf__.config_po_ce(args.repertoire+'/'+args.complement)
				vrf__.config_int_phy_pe(args.repertoire+'/'+args.complement)

	
