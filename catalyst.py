ID_CE={'DUN-A10' : '143', 'DUN-A20' : '144'}

class catalyst(object):
	def __init__(self,nom="TBD",vrf="RVP_TBD",loopback="0.0.0.0",interco_PE={"PE":"NOM","NET":"192.2.2.0/30","SOO":"192.6.6.6:64666","INTERFACE_SRC":"EthX/X","TAG":"666","INTERFACE_DST":"EthX/X"},interco_CE={"CE":"NOM","NET":"192.2.2.0/30","INTERFACE_SRC":"EthX/X","INTERFACE_SRC":"EthX/X","TAG":"666"},bgpAs="64666",idVrf="",env="PROD"):
		"Constructeur "
		
		self.nom=nom
		self.vrf=vrf
		self.interco_CE=interco_CE
		self.interco_PE=interco_PE
		self.bgpAs=bgpAs
		self.parity=self.getParity()
		self.intParity=self.getintParity()
		self.vrfObj=VRF(vrf,idVrf,self.env,"0.0.0."+ID_CE[nom])
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
		
		if int(self.nom[-1]) % 2 == 0:
			result="PAIR"
		elif int(self.nom[-1]) % 2 == 1:
			result="IMPAIR"
			
		return result
		
	def getintParity(self):
		result=0
		
		if int(self.nom[-1]) % 2 == 0:
			result=1
		elif int(self.nom[-1]) % 2 == 1:
			result=2
			
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
		if self.parity
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
			
			resultat=configTemplate(MODEL_INTERFACE_IOS).replace(LISTE_PARAM_INT_PE_CE)
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
			resultat=configTemplate(MODEL_INTERFACE_IOS).replace(LISTE_PARAM_INT_CE_CE)
							
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