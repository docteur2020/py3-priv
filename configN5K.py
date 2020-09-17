# coding: utf-8

import ipaddress
import xlrd
import re
import io
import argparse
from ipcalc import *
import pdb
import os

SALLE_CORRESPONDANCE={ 'R4' : 'R4000', 'R7': 'R7000', 'ASV':'Asimov'}

MODEL_CONFIG_N5K="""!
version 7.1(4)N1(1)
install feature-set fabricpath
feature-set fabricpath
hostname <HOSTNAME>


feature tacacs+
cfs eth distribute
feature udld
feature interface-vlan
feature lacp
feature vpc
feature lldp
no feature telnet
feature fex

role name default-role
  description This is a system defined role and applies to all users.
username admin password 5 $1$AsdvucaX$E5E3mV6JISb7b9C2oBNJi1  role network-admin
username ciscoworks password 5 $1$A0IdSyOu$6d6uN8a4WP2LHcoW51jBy/  role network-admin
username BackupAdmin password 5 $1$IwqR.N.5$l1f8wWt74Dy0ApK1O7zZW.  role network-admin
no password strength-check

banner motd #

NEXUS 5672UP - Cisco Sytems, Inc.

<HOSTNAME>

*****************************************************************
*              THIS DEVICE IS MONITORED CONTINUOUSLY            *
* SESSIONS AND DATA CAN BE RECORDED FOR FURTHER INVESTIGATION   *
*               UNAUTHORIZED ACCESS IS PROHIBITED               *
*****************************************************************

#
no ip domain-lookup
ip host paer 192.64.10.129
tacacs-server host 192.80.10.160 key 7 "<6kO&Tt4"
tacacs-server host 192.88.10.160 key 7 "<6kO&Tt4"
aaa group server tacacs+ TFO-ACS
  server 192.80.10.160
  server 192.88.10.160
  deadtime 60
  use-vrf management
  source-interface mgmt0
logging event link-status default
logging event trunk-status default
ip access-list 1
  10 permit ip 192.64.10.145/32 any
  20 permit ip 172.17.10.145/32 any
  30 permit ip 192.64.101.3/32 any
ip access-list 100
  10 remark DMZ ADMIN TIG
  20 permit ip 192.64.10.128/26 any
  30 remark DMZ ADMIN SC2
  40 permit ip 192.80.10.128/26 any
  50 remark DMZ ADMIN DC2
  60 permit ip 192.88.10.128/26 any
ip access-list 90
  10 permit ip 192.80.20.2/32 any
  20 permit ip 192.83.99.60/32 any
  30 permit ip 192.64.101.3/32 any
  40 permit ip 192.64.10.128/26 any
  50 permit ip 172.17.10.128/26 any
  60 permit ip 192.80.10.128/26 any
  70 permit ip 192.88.10.128/26 any
ip access-list 95
  10 permit ip 192.64.101.230/32 any
  20 permit ip 192.64.4.1/32 any
  30 permit ip 192.2.0.71/32 any
  40 permit ip 192.80.4.1/32 any
  50 permit ip 192.83.99.60/32 any
  60 permit ip 192.64.10.128/26 any
  70 permit ip 172.17.10.128/26 any
  80 permit ip 192.80.10.128/26 any
  92 permit ip 192.88.10.128/26 any
ip access-list 96
  10 remark DMZ-ADMIN-TIG
  20 permit ip 192.64.10.128/26 any
  30 remark DMZ-ADMIN-SC2
  40 permit ip 192.80.10.128/26 any
  50 remark DMZ-ADMIN-DC2
  60 permit ip 192.88.10.128/26 any
ip access-list 97
  10 permit ip 192.80.20.2/32 any
  20 permit ip 192.64.101.3/32 any
  30 permit ip 192.64.10.128/26 any
  40 permit ip 172.17.10.128/26 any
  50 permit ip 192.80.10.128/26 any
  60 permit ip 192.88.10.128/26 any
policy-map type network-qos jumbo
  class type network-qos class-default
    mtu 9216
system qos
  service-policy type network-qos jumbo 
  
<FEXS>

snmp-server location PAR|TIGERY|ODIN|PROD|LAN_DC|CLS|RDC|<SALLE>|
snmp-server source-interface traps mgmt0
snmp-server user admin network-admin auth md5 0x34d1de94adf1043bd09943502475ce28 priv 0x34d1de94adf1043bd09943502475ce28 localizedkey
snmp-server user ciscoworks network-admin auth md5 0x728a77cbe491c1389d34b9e7c83b8078 priv 0x728a77cbe491c1389d34b9e7c83b8078 localizedkey
snmp-server user BackupAdmin network-admin auth md5 0x192aa207453cbeb3e3f183f1d4210a23 priv 0x192aa207453cbeb3e3f183f1d4210a23 localizedkey
!
snmp-server community AKe8Tp4 group network-operator
snmp-server community BKe8Tp4 group network-admin
snmp-server community AKe8Tp4 use-acl 96
snmp-server community BKe8Tp4 use-acl 96
!
snmp-server host 192.64.10.135 traps version 2c AKe8Tp4
snmp-server host 192.80.10.135 traps version 2c AKe8Tp4
snmp-server host 192.80.10.182 traps version 2c Netsh01

snmp-server source-interface traps mgmt0
!
snmp-server enable traps entity
snmp-server enable traps bridge newroot
snmp-server enable traps bridge topologychange
snmp-server enable traps config
snmp-server enable traps license
snmp-server enable traps rf
snmp-server enable traps snmp
snmp-server enable traps stpx inconsistency
snmp-server enable traps stpx root-inconsistency
snmp-server enable traps stpx loop-inconsistency
snmp-server enable traps sysmgr

ntp server 192.64.10.129 prefer use-vrf management key 1002
ntp server 192.80.10.129 use-vrf management key 1002
ntp source-interface mgmt0
ntp authenticate
ntp authentication-key 1002 md5 vagwwt1002 7
ntp trusted-key 1002
ntp logging
ntp access-group peer 100
aaa authentication login default group TFO-ACS local
aaa authentication login console group TFO-ACS local
aaa authorization config-commands default group TFO-ACS local
aaa authorization commands default group TFO-ACS  local
aaa accounting default group TFO-ACS
aaa authentication login error-enable
tacacs-server directed-request

<VLAN_LIST>
spanning-tree mode rapid-pvst
spanning-tree pathcost method long
spanning-tree port type edge bpduguard default

spanning-tree domain <SPT_DOMAIN>
spanning-tree pseudo-information
  vlan 1-3900 root priority 0
vrf context management
  ip route 0.0.0.0/0 192.0.6.3
vpc domain <VPC_DOMAIN>
  role priority <VPC_PRIORITY>
  peer-keepalive destination <IP_OTHER_MEMBER_VPC> source <IP_MGMT>
  peer-config-check-bypass
  delay restore 150
  fabricpath switch-id <FABRICPATH_SW_ID>
  auto-recovery

port-channel load-balance ethernet source-dest-port

interface port-channel10
  description <> vPC-PeerLink
  switchport mode fabricpath
  vpc peer-link
  fabricpath isis metric 10000


interface Ethernet1/47
  description <> <NOM_PEER> - Eth1/47
  switchport mode fabricpath
  channel-group 10 mode active

interface Ethernet1/48
  description <> <NOM_PEER> - Eth1/48
  switchport mode fabricpath
  channel-group 10 mode active



interface Ethernet2/1
  description <*> TIGR4-ODIN-CFD-vdc2 - <INT_CFDR4>
  switchport mode fabricpath

interface Ethernet2/2
  shutdown

interface Ethernet2/3
  description <*> TIGR7-ODIN-CFD-vdc2 - <INT_CFDR7>
  switchport mode fabricpath

interface Ethernet2/4
  shutdown
  
  
<INTERFACES_FEX>

interface mgmt0
  description <> <PORT_ADMIN>
  vrf member management
  ip address <IP_MGMT>/24
cli alias name wr copy run start
cli alias name shAdj source shAdj.py
cli alias name shMtrees show fabricpath isis trees 
cli alias name shMtopo show fabricpath isis topology summary
cli alias name shConflict show fabricpath conflict link detail
cli alias name shAffinity sh fabricpath  isis database detail | inc Host|Affin|Numg
cli alias name shNextId source shNextId.py
cli alias name shNextPo source shNextPo.py
cli alias name shHostname source shHostname.py
line console
line vty
 access-class 96 in
boot kickstart bootflash:/n6000-uk9-kickstart.7.1.4.N1.1.bin
boot system bootflash:/n6000-uk9.7.1.4.N1.1.bin
fabricpath domain default
  spf-interval 50 50 50
  lsp-gen-interval 50 50 50
fabricpath switch-id <FABRICPATH_ID>
logging server 192.80.10.175 6 use-vrf management facility local7
logging timestamp milliseconds
logging monitor 3
no logging console"""


class configTemplate(object):
	"Classe template de configuration"
	def __init__(self,str):
		self.template=str
		
	def replace(self,liste_parametre):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		
		resultat=self.template
		for (param,valeur) in liste_parametre:
			#print("PARAM:{0} VALEUR:{1}".format(param,valeur))
			try:
				resultat=resultat.replace("<"+param+">",valeur)
			except:
				#pass
				pdb.set_trace()
			
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
		
		
class n5kCouple(object):
	def __init__(self,nom="TBD",ip_mgnt='255.255.255.255/30|',acces_console1='255.255.255.255:23',acces_console2='255.255.255.255:23',fex_liste=[],vpc_id="100",uplinks="eX/X,eX,Y",port_admin="giX/X,giY/Y",vlan_liste=""):
		"Constructeur "
		
		self.nom=nom
		self.nom1=nom+"1"
		self.nom2=nom+"2"
		self.ip_mgnt1=self.init_ip(ip_mgnt)
		self.ip_mgnt2=self.ip_mgnt1+1
		self.acces_console1=acces_console1
		self.acces_console1=acces_console2
		self.vpc_id=str(int(vpc_id))
		self.k_value=str(int(int(vpc_id)/10-20))
		self.fexs=self.init_liste(fex_liste)
		self.uplinks=uplinks.split(',')
		self.vlans=[]
		self.port_admin=port_admin
		self.vlan_liste=vlan_liste
		
	
		
	def __str__(self):
		"Affichage"
		
		result='#####################################################'+'\n'
		result+='NOMs:'+self.nom1+'/'+self.nom2+'\n'
		result+='VPC ID:'+self.vrf+'\n'
		result+='#####################################################'+'\n\n\n'
		
		return result
		
	def init_ip(self,ip):
		"renvoie un objet IP"
		
		result=None
		try:
			result=ipaddress.ip_address(ip.replace(' ',''))
		except:
			raise ipError(1,ip) 
			
		return(result)

	def init_liste(self,liste):
		"supprime les listes sans informations"
		
		result=[]
		if liste !=[''] and liste!=['\n']:
			result=liste
		return(result)  		

	def init_network(self,network_):
		"renvoie un objet Network"
		
		result=None
		try:
			result=Network(network_.replace(' ',''))
		except:
			raise ipError(code=2,value1=network_)
			
		return(result) 
		
	def init_vlans(self,vlans_str):
		"renvoie un objet str"

		return(vlans_str) 
		
	def init_fex_config(self,peer):
		
		resultat=io.StringIO()
		

			
		port_id=1
		for fex__ in self.fexs:
			resultat.write('interface Ethernet1/'+str(port_id)+'\n')
			port_id+=1
			resultat.write('  description TO '+(self.nom+str(peer)+'-FEX'+fex__ ).upper() +'\n')
			resultat.write('  logging event port link-status\n')
			resultat.write('  switchport mode fex-fabric\n')
			resultat.write('  fex associate '+fex__+'\n')
			resultat.write('  logging event port link-status\n')
			resultat.write('  logging event port trunk-status\n')
			resultat.write('  storm-control broadcast level 1.00\n')
			resultat.write('  channel-group '+fex__+'\n\n')
			
			resultat.write('interface Ethernet1/'+str(port_id)+'\n')
			port_id+=1
			resultat.write('  description <*> TO '+(self.nom+str(peer)+'FEX'+fex__ ).upper() +'\n')
			resultat.write('  logging event port link-status\n')
			resultat.write('  switchport mode fex-fabric\n')
			resultat.write('  fex associate '+fex__+'\n')
			resultat.write('  logging event port link-status\n')
			resultat.write('  logging event port trunk-status\n')
			resultat.write('  storm-control broadcast level 1.00\n')
			resultat.write('  channel-group '+fex__+'\n')
	
		for fex__ in self.fexs:
			resultat.write('interface port-channel'+fex__+'\n')
			resultat.write('  description <*> TO '+(self.nom+str(peer)+'-FEX'+fex__ ).upper() +'\n')
			resultat.write('  switchport\n')
			resultat.write('  switchport mode fex-fabric\n')
			resultat.write('  fex associate '+fex__ +'\n')
			resultat.write('  logging event port link-status\n')
			resultat.write('  logging event port trunk-status\n')
			resultat.write('  storm-control broadcast level 1.00\n\n')
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	def init_fex_vlan(self,peer):
		
		resultat=io.StringIO()
		
		for fex__ in self.fexs:
			resultat.write('fex '+fex__+'\n')
			resultat.write('  pinning max-links 1\n')
			resultat.write('  description \"'+ ("FEX"+fex__ ).upper() +'\"\n\n')
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	def init_config(self,peer):
	
		HOSTNAME=self.nom+str(peer)
		salle=self.nom1.split('-')[0][3:]
		SALLE=SALLE_CORRESPONDANCE[salle]
		FEXS=self.init_fex_vlan(peer)
		INTERFACES_FEX=self.init_fex_config(peer)
		VLAN_LIST=self.vlan_liste
		SPT_DOMAIN=self.k_value
		VPC_DOMAIN=self.vpc_id
		VPC_PRIORITY=str(1000*peer)
		if peer==1:
			IP_OTHER_MEMBER_VPC=str(self.ip_mgnt2)
			IP_MGMT=str(self.ip_mgnt1)
			PORT_ADMIN=self.port_admin[0]+'_'+self.port_admin[1]
			NOM_PEER=self.nom+str(2)
			FABRICPATH_ID=str(int(self.vpc_id)+1)
			INT_CFDR4=self.uplinks[0]
			INT_CFDR7=self.uplinks[0]
		else:
			IP_OTHER_MEMBER_VPC=str(self.ip_mgnt1)
			IP_MGMT=str(self.ip_mgnt2)
			PORT_ADMIN=self.port_admin[0]+'_'+self.port_admin[2]
			NOM_PEER=self.nom+str(1)
			FABRICPATH_ID=str(int(self.vpc_id)+2)
			INT_CFDR4=self.uplinks[1]
			INT_CFDR7=self.uplinks[1]
		FABRICPATH_SW_ID=self.vpc_id
		
		LISTE_PARAM_N5K=(('HOSTNAME',HOSTNAME),
						('SALLE',SALLE),
						('FEXS',FEXS),
						('VLAN_LIST',VLAN_LIST),
						('INTERFACES_FEX',INTERFACES_FEX),
						('SPT_DOMAIN',SPT_DOMAIN),
						('VPC_DOMAIN',VPC_DOMAIN),
						('VPC_PRIORITY',VPC_PRIORITY),
						('IP_OTHER_MEMBER_VPC',IP_OTHER_MEMBER_VPC),
						('IP_MGMT',IP_MGMT),
						('FABRICPATH_ID',FABRICPATH_ID),
						('FABRICPATH_SW_ID',FABRICPATH_SW_ID),
						('INT_CFDR4',INT_CFDR4),
						('INT_CFDR7',INT_CFDR7),
						('NOM_PEER',NOM_PEER),
						('PORT_ADMIN',PORT_ADMIN))
		
		return configTemplate(MODEL_CONFIG_N5K).replace(LISTE_PARAM_N5K)
	
class n5kCouples(object):	
	def __init__(self,excel_file,vlan_liste):
		self.liste_n5kCouple=[]
		wb=xlrd.open_workbook(excel_file)
		sh = wb.sheet_by_name(u'N5K')
		for rownum in range(1,sh.nrows):
			self.liste_n5kCouple.append(n5kCouple(nom=sh.row_values(rownum)[0],ip_mgnt=sh.row_values(rownum)[1],acces_console1=sh.row_values(rownum)[2],acces_console2=sh.row_values(rownum)[3],vpc_id=sh.row_values(rownum)[4],fex_liste=sh.row_values(rownum)[5].split(','),uplinks=sh.row_values(rownum)[6],port_admin=tuple(sh.row_values(rownum)[7].split(',')),vlan_liste=vlan_liste))
		self.configs={}
	def __str__(self):
		resultat=""
		for n5ks in self.liste_n5kCouple:
			resultat+=n5ks.__str__()
			
		return resultat
		
	def init_config_all(self):
	
		for n5ks in self.liste_n5kCouple:
			self.configs[n5ks.nom1]=n5ks.init_config(1)
			self.configs[n5ks.nom2]=n5ks.init_config(2)
			
	def print_all_config(self):
		for n5ks in self.liste_n5kCouple:
			print('configuration:'+n5ks.nom1.upper())
			print('\n\n')
			print(self.configs[n5ks.nom1])
			
			print('configuration:'+n5ks.nom2.upper())
			print('\n\n')
			print(self.configs[n5ks.nom2])
	
	def save_config(self,repertoire):
	
		if not os.path.exists(repertoire):
				os.makedirs(repertoire)
			
		for n5ks__ in self.liste_n5kCouple:
			fichier_sauvegarde1=n5ks__.nom1+'.cfg'
			fichier_sauvegarde2=n5ks__.nom2+'.cfg'
			with open(repertoire+'/'+fichier_sauvegarde1,'w') as file1:
				file1.write(self.configs[n5ks__.nom1])
			with open(repertoire+'/'+fichier_sauvegarde2,'w') as file2:
				file2.write(self.configs[n5ks__.nom2])
				
		
if __name__ == '__main__':
	"Fonction principale"	
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	parser.add_argument("-e", "--excel",action="store",help="Excel File",required=True)
	group1.add_argument("-i", "--init_vlan",action="store",help="Recupere les vlans")
	group1.add_argument("-v", "--vlans",action="store",help="Fichier contenant la confiugration des vlans")
	parser.add_argument("-r", "--repertoire",action="store",help="Repertoire ou sauvegarder les configurations",required=False)
	args = parser.parse_args()
	
	if args.excel and args.vlans:
		with open(args.vlans,'r') as file_vlans:
			vlans_str=file_vlans.read()
		N5KS__=n5kCouples(args.excel,vlans_str)
		N5KS__.init_config_all()
		N5KS__.print_all_config()
		
		if args.repertoire:
			N5KS__.save_config(args.repertoire)
	
	