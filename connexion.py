#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import time
from time import gmtime, strftime , localtime
import threading
import sys
import os
import argparse
import pdb
import re
from io import StringIO 
from io import BytesIO
from pexpect import pxssh
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect , exceptions
import pickle
from ipcalc import *
import dns.resolver
import ipaddress
import random
import queue
import pprint
from ParsingShow import *
sys.path.append('/home/X112097/py')
from ParseVlanListe import vlan , liste_vlans
from getsec import *
from getIPFromPaer import getIPFromtrace

PARSER={'MAC':'ParseMacCisco'  , 'DESC':ParseDescriptionCiscoOrNexus ,'VLAN':ParseVlanRun  , 'GETALLROUTE':ParseIpRouteString,'PORTCHANNEL':ParsePortChannelCisco , 'STATUS':ParseStatusCisco ,'SWITCHPORT':ParseSwitchPortString , 'CDPDETAIL':ParseCdpNeighborDetailString , 'TRANSCEIVER':ParseInterfaceTransceiverString , 'GETALLBGP':ParseBgpTableString  , 'GETBGPTABLE':ParseBgpTableString , 'FEX':ParseShFexString ,'VRF':ParseVrf ,'COUNTERERROR': ParseIntCounterError , 'BGPNEIGHBOR': ParseBgpNeighbor}
TSK="/home/x112097/CONNEXION/pass.db"

def connect_parse_with_retry(connex,fct_parsing,retry):
	resultat=None
	try__id=1
	while try__id <= retry:
		try:
			print("Tentative:"+str(try__id))
			resultat=connex.launch_withParser(fct_parsing)
			break;
		except ErrorNeedRetry as error_retry:
			try__id=try__id+1
			print(error_retry)
			connex.rebond.close()

		
	return resultat


class CommandNotSupported(ValueError):
	def __init__(self, message):
		super(ValueError, self).__init__(message)
		
class ResetError(Exception):
	def __init__(self, message):
		super(ResetError, self).__init__(message)

class ErrorNeedRetry(Exception):
	def __init__(self, message,equipement,commande,repertoire,output,retry,type,commande_en_ligne,status):
		super(ErrorNeedRetry, self).__init__(message)
		self.equipement_to_retry=equipement
		self.commande_to_retry=commande
		self.repertoire_to_retry=repertoire
		self.output_to_retry=output
		self.retry=retry
		self.type_to_retry=type
		self.commande_en_ligne_to_retry=commande_en_ligne
		self.status=status
		#print(self.__str__())
		
	def __str__(self):
		return(self.equipement_to_retry.nom+"=="+self.commande_en_ligne_to_retry+"==RETRY:"+self.retry.__str__())
		
class ErrorNeedRetryConnexion(Exception):
	def __init__(self, message,ErrorLevel2):
		super(ErrorNeedRetryConnexion, self).__init__(message)
		self.errorLevel2=ErrorLevel2

	
class equipement(object):
	"definit un equipement"
	def __init__(self,nom,OS="IOS",IP="0.0.0.0",type="SSH",db='/home/x112097/CONNEXION/Equipement.db'):
		"Constructeur"
		self.nom=nom
		self.OS=OS
		self.IP=IP
		if self.IP=="0.0.0.0":
			self.init_from_db(db)
		self.type=type
		self.Vrfs=[]
		self.Neighbors={}
	
	def __str__(self):
		return(self.nom+",OS:"+self.OS+",IP:"+self.IP+",TYPE:"+self.type)
		
	def __eq__(self,other_equipement):
		return(self.nom==other_equipement.nom and self.OS==other_equipement.OS and self.IP==other_equipement.IP and self.type==other_equipement.type)
		
	def init_from_db(self,db_equipement):
		Liste_db_equipements=equipement_connus(db_equipement)
		
		if self.nom in Liste_db_equipements:
			self.OS=Liste_db_equipements[self.nom][0]
			self.IP=Liste_db_equipements[self.nom][1]
			self.type=Liste_db_equipements[self.nom][2]
		else:
			#pdb.set_trace()
			while self.nom not in Liste_db_equipements:
				Liste_db_equipements.append_read(self.nom)
			self.OS=Liste_db_equipements[self.nom][0]
			self.IP=Liste_db_equipements[self.nom][1]
			self.type=Liste_db_equipements[self.nom][2]

class equipement_connus(object):
	def __init__(self,db="/home/X112097/CONNEXION/Equipement.db"):
		self.liste_equipements={}
		self.db=db
		db_file=open(db,'rb')
		while True:
			try:
				equipement_cur=pickle.load(db_file)
			except EOFError:
				break
			self.liste_equipements[equipement_cur.nom]=((equipement_cur.OS,equipement_cur.IP,equipement_cur.type))
		db_file.close()
		
	def append(self,equipement_,mode=''):

		if equipement_.nom not in self:	
			self.liste_equipements[equipement_.nom]=((equipement_.OS,equipement_.IP,equipement_.type))
			with open(self.db,"a+b") as db_file:
				pickle.dump(equipement_,db_file)
		elif not mode:
			temp_db_r=[]
		
			with open(self.db,'rb') as db_file_r:
				while True:
					try:
						temp_db_r.append(pickle.load(db_file_r))
					except EOFError:
						break
			equipement_to_change=self.get_obj_equipement(equipement_.nom)
			print(equipement_to_change)
			print(equipement_to_change.nom)
			for indice in range(0,len(temp_db_r),1):
				if temp_db_r[indice] == equipement_to_change:
					del temp_db_r[indice]
					break
			self.liste_equipements[equipement_.nom]=((equipement_.OS,equipement_.IP,equipement_.type))
			temp_db_r.append(equipement_)
			
			with open(self.db,'wb') as db_file_w:
				db_file_w.seek(0)
				db_file_w.truncate()
				for element in temp_db_r:
					pickle.dump(element,db_file_w)
	
	def suppress(self,equipement_nom):

		if equipement_nom in self:
			temp_db_r=[]
		
			with open(self.db,'rb') as db_file_r:
				while True:
					try:
						temp_db_r.append(pickle.load(db_file_r))
					except EOFError:
						break
						
			equipement_to_suppress=self.get_obj_equipement(equipement_nom)
			#pdb.set_trace()
			for indice in range(0,len(temp_db_r),1):
				if temp_db_r[indice] == equipement_to_suppress:
					del temp_db_r[indice]
					break
			del self.liste_equipements[equipement_nom]
			
			with open(self.db,'wb') as db_file_w:
				db_file_w.seek(0)
				db_file_w.truncate()
				for element in temp_db_r:
					pickle.dump(element,db_file_w)
		else:
			print(u"L'élément "+equipement_nom+u" n'est pas dans la base et ne peut donc être supprimé")
		

			
	def __contains__(self,nom_equipement):
		#pdb.set_trace()
		resultat=True
		try:
			test=self.liste_equipements[nom_equipement]
		except:
			resultat=False
			
		return resultat
		
	def append_read(self,nom_equipement_):
		OS_="NONE"
		TYPE_="NONE"
		if nom_equipement_ not in self:
			print(u"L'équipement "+nom_equipement_+u" n'est pas connu.")
		else:
			print(u"L'equipement "+nom_equipement_+u" est connu et va être modifier")
		while not ( OS_=="IOS" or OS_=="Nexus" or OS_=="XR" or OS_=="OLD-IOS" or OS_=="ACE" or OS_=="ACI" or OS_=="ACI-APIC"):
			OS_=input("Quel est l'OS [XR|IOS|Nexus|OLD-IOS|ACE|ACI|ACI-APIC](Nexus):")
			if not OS_:
				OS_="Nexus"
		dns_requete=dns.query.udp(dns.message.make_query(nom_equipement_+'.dns63.socgen', dns.rdatatype.A, use_edns=0),'192.16.207.80')
		if dns_requete.rcode()==0:
			IP_DEFAULT=dns_requete.answer[0].__str__().split()[4]
		else:
			IP_from_paer=getIPFromtrace(nom_equipement_)
			if IP_from_paer:
				IP_DEFAULT=IP_from_paer
			else:
				IP_DEFAULT=""
		test_format_IP=False
		#pdb.set_trace()
		while not test_format_IP:
			if IP_DEFAULT:
				IP_=input('Quel est l\'IP('+IP_DEFAULT+'):')
				if IP_=="":
					IP_=IP_DEFAULT
			else:
				IP_=input('Quel est l\'IP:')
			try:
				ipaddress.ip_address(IP_)
				test_format_IP=True
			except:
				pass
								
		while not ( TYPE_=="TELNET" or TYPE_=="SSH"):
			TYPE_=input("Quel est le type de connexion [TELNET|SSH](SSH):")
			if not TYPE_:
				TYPE_="SSH"
		equipement_=equipement(nom_equipement_,OS_,IP_,TYPE_)	
		if nom_equipement_ not in self:
			with open(self.db,"a+b") as db_file:
				pickle.dump(equipement_,db_file)
			self.liste_equipements[equipement_.nom]=((equipement_.OS,equipement_.IP,equipement_.type))

		
	def get_obj_equipement(self,nom_equipement):
		#pdb.set_trace()
		try:
			info_equipement_cur=self.liste_equipements[nom_equipement]
			resultat=equipement(nom_equipement,info_equipement_cur[0],info_equipement_cur[1],info_equipement_cur[2])
		except:
			resultat=None
			
		return resultat
	
	def  __getitem__(self,key):
		return self.liste_equipements[key]
		
	def __str__(self):
		#pdb.set_trace()
		resultat=""
		for nom_equipement,info_equipement in self.liste_equipements.items():
			resultat+=nom_equipement+",OS:"+info_equipement[0]+",IP:"+info_equipement[1]+",TYPE:"+info_equipement[2]+'\n'
			
		return resultat
		
			
class connexion(threading.Thread):
	"lance une connexion automatique avec commande"
	def __init__(self,equipement,queue__,queue_echec,liste_commande,mode="SSH",output="NONE",repertoire="",commande_en_ligne="",retry=0,status="NOT INITIATED",verbose=False,timeout=300):
		threading.Thread.__init__(self)
		self.equipement=equipement
		self.commande=liste_commande
		self.mode=mode
		self.resultat=""
		self.rebond=pxssh.pxssh(timeout=timeout,maxread=1000000,options={"ServerAliveInterval":5},searchwindowsize=10000,env = {"TERM": "dumb"})
		
		if queue__==None:
			self.queue=queue.Queue()
		else:
			self.queue=queue__
			
		if queue_echec==None:
			self.queue_echec=queue.Queue()
		else:
			self.queue_echec=queue_echec
		suffixe_time=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		self.repertoire=repertoire
		self.retry=retry
		self.retry_delay=1.3
		self.status=status
		self.verbose=verbose
		self.timeout=timeout
		self.tsk=secSbe(TSK)
		
		

		#pdb.set_trace()
		if output=="NONE" and repertoire=="":
			self.output="OUTPUT/"+equipement.nom+suffixe_time+".log"
		elif output!="" and output!="NONE":
			self.output=output
		elif repertoire:
			if not os.path.exists(repertoire):
				os.makedirs(repertoire)
			self.output=repertoire+"/"+equipement.nom+suffixe_time+".log"
		else:
			self.output=output
		#pdb.set_trace()
		self.commande_en_ligne=commande_en_ligne
		#print("\n\n"+retry.__str__()+"=="+self.__str__()+"\n\n")*
		
		self.commande_short=""
		if isinstance(self.commande_en_ligne,str):
			self.commande_short=self.commande_en_ligne
		elif isinstance(self.commande_en_ligne,list):
			self.commande_short=self.commande_en_ligne[0]+"..."
	
	def __str__(self):
		resultat=""
		if isinstance(self.commande_en_ligne,str):
			resultat=self.equipement.__str__()+'=='+self.commande_en_ligne
		elif isinstance(self.commande_en_ligne,list):
			resultat=self.equipement.__str__()+'=='+self.commande_en_ligne[0]+"..."
		return resultat
		
	def run(self):
		#pdb.set_trace()
		time.sleep(self.retry*self.retry_delay)
		print("Starting connexion vers "+ self.equipement.nom+" Tentative:"+(self.retry+1).__str__())
		if self.commande_en_ligne:
			#print("ICI")
			try:
				self.launch_commande_en_ligne()
			except ErrorNeedRetry as error_retry:
				#pdb.set_trace()
				print("Error Reset level 2 Ref 10:"+self.__str__())
				print('=='+error_retry.retry.__str__()+'==')
				if error_retry.retry <=3:
					
					self.queue.put(connexion(error_retry.equipement_to_retry,  self.queue,    self.queue_echec,       error_retry.commande_en_ligne_to_retry,  mode=error_retry.type_to_retry,  output=error_retry.output_to_retry          , repertoire=error_retry.repertoire_to_retry       ,commande_en_ligne=error_retry.commande_en_ligne_to_retry,retry=error_retry.retry+1,status="FAILED RETRY:"+error_retry.retry.__str__()+self.__str__(),timeout=self.timeout))
				else:
					#pdb.set_trace()
					print('ECHEC POUR '+self.__str__())
					self.queue_echec.put(connexion(error_retry.equipement_to_retry,self.queue,self.queue_echec,error_retry.commande_en_ligne_to_retry,error_retry.type_to_retry,error_retry.output_to_retry,error_retry.repertoire_to_retry,error_retry.commande_en_ligne_to_retry,retry=error_retry.retry+1,status="FAILED RETRY:"+error_retry.retry.__str__()+self.__str__(),timeout=self.timeout))
					self.status="UNSUCCESS EVEN AFTER MULTIPLE ATTEMPTS:"+self.__str__()
		else:
			#print('LA')
			self.launch_commandes()
		print("Exiting "+ self.__str__())
	
	def launch_commandes(self):
		try:
			print("Debut:")
			#self.rebond.logfile = sys.stdout.buffer
			regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']
			
			self.rebond.login('192.64.10.129','x112097',self.tsk.whs)
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[#$]$"
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.equipement.nom)[0])
			else:
				self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.equipement.nom)[0]+' '+self.equipement.nom )
			expect_value=self.rebond.expect(['assword','yes'])
			print("COUCOU:"+expect_value.__str__())
			if expect_value==0:
				self.rebond.sendline(self.tsk.getMode(self.equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			else:
				os.exit(4)
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			try:
				#pdb.set_trace()
				fichier_commande=open(self.commande,"r")
			except IOError as io_error:
				print(str(io_error))
				sys.exit(1)
			try:
				fichier_output=open(self.output,"w+")
			except IOError as io_error:
				print(str(io_error))
				sys.exit(1)
			for ligne in fichier_commande:
				self.rebond.sendline(ligne)
				self.rebond.expect(regex_match,timeout=self.timeout)
				#print("LIGNE:"+ligne)
				
			fichier_output.write(data_output.getvalue().decode('UTF-8'))
			self.resultat=data_output.getvalue().decode('UTF-8')
			self.rebond.sendline('exit')
			self.rebond.close()
			fichier_output.close()
			self.status="DONE"
			
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			print(str(e))
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED pexpect failed on login:"+str(ep)+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			print(str(ep))
		except ResetError:
			self.status="FAILED:"+"RESET Sent py peer"+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
		except TIMEOUT:
			print("Timeout...")
			self.status="FAILED:"+"TIMEOUT"+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			
	def launch_withParser(self,parser_fct):
		Resultat=None
		
		try:
			print(u"Parsing "+self.equipement.nom+" Method:"+parser_fct.__name__)
			#self.rebond.logfile = sys.stdout.buffer
			regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']
			self.rebond.login('192.64.10.129','x112097',self.tsk.whs)
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[#$]$"
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.equipement.nom)[0])
			else:
				self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.equipement.nom)[0]+' '+self.equipement.nom )
			expect_value=self.rebond.expect(['assword','yes'])
			#print("COUCOU:"+expect_value.__str__())
			if expect_value==0:
				self.rebond.sendline(self.tsk.getMode(self.equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			else:
				os.exit(4)
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			
			if self.commande_en_ligne:
				if isinstance(self.commande_en_ligne,str):
					self.rebond.sendline(self.commande_en_ligne)
					self.rebond.expect(regex_match,timeout=self.timeout)
				elif isinstance(self.commande_en_ligne,list):
					for commande_str in self.commande_en_ligne:
						self.rebond.sendline(commande_str)
						self.rebond.expect(regex_match,timeout=self.timeout)
			else:
				for ligne in fichier_commande:
					self.rebond.sendline(ligne)
					self.rebond.expect(regex_match,timeout=self.timeout)
					#print("LIGNE:"+ligne)
				
			#pdb.set_trace()
			try:
				self.resultat=data_output.getvalue().decode('UTF-8')
				Resultat=parser_fct(data_output.getvalue().decode('UTF-8'))
			except UnicodeDecodeError as e:
				self.resultat=data_output.getvalue().decode('ISO-8859-1')
				Resultat=parser_fct(data_output.getvalue().decode('ISO-8859-1'))
			
			with open(self.output,"w+") as fichier_output:
				try:
					fichier_output.write(data_output.getvalue().decode('UTF-8'))
				except UnicodeDecodeError as e:
					fichier_output.write(data_output.getvalue().decode('ISO-8859-1'))
				
			self.rebond.sendline('exit')
			self.rebond.close()
			
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			print(str(e))
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED pexpect failed on login:"+str(ep)+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			print(str(ep))
		except ResetError:
			self.status="FAILED:"+"RESET Sent py peer"+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
		except TIMEOUT:
			print("Timeout...")
			self.status="FAILED:"+"TIMEOUT"+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError(self.status)
			
		return Resultat
			
	def launch_commande_en_ligne(self):
		
		try:
			#print("Autre début...")
			#self.rebond.logfile = sys.stdout.buffer
			regex_match=["(\n|\r)[^\r\n#$]+[#$]\s*$",'\r\n[^\r\n#$]+[#$]$','\r[a-zA-Z]\\S+#','(\n|\r)[a-zA-Z]\\S+#',"(\n|\r)[a-zA-Z]\\S+#"]
			self.rebond.login('192.64.10.129','x112097',self.tsk.whs)
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[#$]$"
			if self.verbose:
				self.rebond.logfile = sys.stdout.buffer
			if self.equipement.type=="TELNET":
				self.rebond.sendline ('telnet '+self.equipement.nom )
				self.rebond.expect ('sername' )
				self.rebond.sendline (self.tsk.getMode(self.equipement.nom)[0])
			else:
				try:
					self.rebond.sendline ('ssh -l '+self.tsk.getMode(self.equipement.nom)[0]+' '+self.equipement.nom )
				except pxssh.ExceptionPxssh as e:
					print("pxssh failed on login")
					self.status="FAILED SSH:"+str(e)+'=='+self.equipement.__str__()+'=='+self.commande_en_ligne
					print(str(e))
			
				except ExceptionPexpect as ep:
					print("pxssh failed on login")
					self.status="FAILED SSH:"+str(ep)+'=='+self.equipement.__str__()+'=='+self.commande_en_ligne
					print(str(ep))
			
				except pexpect.exceptions.TIMEOUT:
					print("Timeout...")
					self.status="FAILED SSH:"+"TIMEOUT"+'=='+self.equipement.__str__()+'=='+self.commande_en_ligne
			expect_value=self.rebond.expect(['assword','yes','Connection reset by peer'],timeout=self.timeout)
			#print("COUCOU:"+expect_value.__str__())
			if expect_value==0:
				self.rebond.sendline(self.tsk.getMode(self.equipement.nom)[1])
				self.rebond.expect(regex_match)
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==1:
				self.rebond.sendline("yes")
				self.rebond.expect ('assword:' )
				self.rebond.sendline(self.tsk.getMode(self.equipement.nom)[1])
				#print('ici')
				self.rebond.expect(regex_match)
				#print('la')
				self.rebond.sendline("terminal length 0")
				self.rebond.expect(regex_match)
			elif expect_value==2:
				self.rebond.close()
				print("!!! Connection reset by peer !!!")
				raise ResetError("!!! SSH Reset Error !!!")
			else:
				os.exit(4)
				
			data_output = BytesIO()
			self.rebond.logfile_read = data_output
			self.rebond.PROMPT=r"\r\n[^\r\n#$]+[#$]$"
			#print("PROMPT:"+self.rebond.PROMPT)
			try:
				fichier_output=open(self.output,"w+")
			except IOError as io_error:
				print(str(io_error))
				sys.exit(1)
			if isinstance(self.commande_en_ligne,str):
				self.rebond.sendline(self.commande_en_ligne)
				self.rebond.expect(regex_match,timeout=self.timeout)
			elif isinstance(self.commande_en_ligne,list):
				for commande_str in self.commande_en_ligne:
					self.rebond.sendline(commande_str)
					self.rebond.expect(regex_match,timeout=self.timeout)
			else:
				print("Erreur sur la variable commande")
				print(type(self.commande_en_ligne))
				sys.exit(8)
				#print("LIGNE:"+ligne)
			
			
			fichier_output.write(data_output.getvalue().decode('UTF-8'))
			self.resultat=data_output.getvalue().decode('UTF-8')
			self.rebond.sendline('exit')
			self.rebond.close()
			fichier_output.close()
			self.status="DONE"
			
		except pxssh.ExceptionPxssh as e:
			print("pexpect failed on login")
			self.status="FAILED:"+str(e)+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError("Coucou")
			print(str(e))
			
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED:"+str(ep)+'=='+self.equipement.__str__()+'=='+self.commande_short
			print(str(ep))
		except ResetError:
			self.status="FAILED:"+"RESET Sent py peer"+'=='+self.equipement.__str__()+'=='+self.commande_short
			raise ErrorNeedRetry(self.status,self.equipement,self.commande,self.repertoire,self.output,self.retry,self.mode,self.commande_en_ligne,self.status) from ResetError("Coucou")
		except TIMEOUT:
			print("Timeout...")
			self.status="FAILED:"+"TIMEOUT"+'=='+self.equipement.__str__()+'=='+self.commande_short
			
	def print_status(self):
		print(self.status)

class connexions(object):
	"lance une connexion automatique avec commande"
	def __init__(self,fichier_liste_equipement,queue,queue_echec,known_equipments,liste_commandes="shrun.txt",repertoire="",commande_en_ligne="",action="",suffixe="",liste_equipement=None,timeout=300,verbose=False,format=False):
		#pdb.set_trace()
		self.liste_equipement=[]
		self.connexion_liste=[]
		self.known_equipments=known_equipments
		self.commandes=liste_commandes
		self.repertoire=repertoire
		self.commande_en_ligne=commande_en_ligne
		self.action=action
		self.queue=queue
		self.queue_echec=queue_echec
		self.start_test=False
		self.nb_connexion=0
		self.retry_delay=1
		self.lock=threading.Lock()
		self.lock.acquire()
		self.status_all={}
		self.liste_thread_to_wait=[]
		self.suffixe=suffixe
		self.timeout=timeout
		self.verbose=verbose
		self.format=format
		#pdb.set_trace()
		if not self.action:
			if not liste_equipement and self.format is False:
				with open(fichier_liste_equipement,'r') as file_equipements:
					for ligne in file_equipements:
						nom_equipement=ligne.lower().replace('\n',"").replace('\r',"").replace(' ',"")
						#pdb.set_trace()
						if nom_equipement in self.known_equipments:
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						else:
							while nom_equipement not in self.known_equipments:
								self.known_equipments.append_read(nom_equipement)
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						if(commande_en_ligne):
							self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,self.commandes,repertoire=self.repertoire,commande_en_ligne=self.commande_en_ligne,timeout=self.timeout,verbose=self.verbose))
						else:
							self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,self.commandes,repertoire=self.repertoire,timeout=self.timeout,verbose=self.verbose))
			elif not liste_equipement and self.format is True:
				with open(fichier_liste_equipement,'r') as file_equipements_format:
					for ligne in file_equipements_format:
						tab_ligne=ligne.split(';')
						nom_equipement=tab_ligne[0].lower().replace('\n',"").replace('\r',"").replace(' ',"")
						commandes_cur=tab_ligne[1].split(',')
						#pdb.set_trace()
						if nom_equipement in self.known_equipments:
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						else:
							while nom_equipement not in self.known_equipments:
								self.known_equipments.append_read(nom_equipement)
							equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
							self.liste_equipement.append(equipement_cur)
						#pdb.set_trace()
						self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,commandes_cur,repertoire=self.repertoire,commande_en_ligne=commandes_cur,timeout=self.timeout,verbose=self.verbose))
			else:
				for nom_equipement_element in liste_equipement.split(":"):
					nom_equipement=nom_equipement_element.lower().replace('\n',"").replace('\r',"").replace(' ',"")
					#pdb.set_trace()
					if nom_equipement in self.known_equipments:
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					else:
						while nom_equipement not in self.known_equipments:
							self.known_equipments.append_read(nom_equipement)
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					if(commande_en_ligne):
						self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,self.commandes,repertoire=self.repertoire,commande_en_ligne=self.commande_en_ligne,timeout=self.timeout,verbose=self.verbose))
					else:
						self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,self.commandes,repertoire=self.repertoire,timeout=self.timeout,verbose=self.verbose))
				
		elif self.action=='VRF':
			with open(fichier_liste_equipement,'r') as file_equipements_vrf:
				for ligne in file_equipements_vrf:
					tab_ligne=ligne.split()
					nom_equipement=tab_ligne[0]
					OS=tab_ligne[1]
					vrf=tab_ligne[2:]
					#pdb.set_trace()
					if nom_equipement in self.known_equipments:
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					else:
						while nom_equipement not in self.known_equipments:
							self.known_equipments.append_read(nom_equipement)
						equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
						self.liste_equipement.append(equipement_cur)
					OS_cur=self.known_equipments.liste_equipements[nom_equipement][0]
					type_cur=self.known_equipments.liste_equipements[nom_equipement][2]
					for vrf_cur in vrf:
						
						if OS_cur=='IOS' or OS_cur=="OLD-IOS":
							commande_cur='sh ip route vrf '+vrf_cur
						elif OS_cur=='Nexus':
							commande_cur='sh ip route vrf '+vrf_cur
						elif OS_cur=='XR':
							commande_cur='sh route vrf '+vrf_cur
						else:
							sys.stderr.write('type OS '+OS_cur+' non pris en charge')
							os.exit('6')
						repertoire_cur=self.repertoire+'/'+vrf_cur
						if not os.path.exists(repertoire_cur):
							os.makedirs(repertoire_cur)
						if suffixe:
							output_cur=repertoire_cur+"/"+suffixe+nom_equipement.lower()+".log"
						else:
							output_cur=repertoire_cur+"/"+nom_equipement.lower()+".log"
						self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,output_cur,repertoire_cur,commande_cur,timeout=self.timeout,verbose=self.verbose))
			
	
	
		elif self.action=='MAC' or self.action=='DESC' or self.action=='GETALLARP' or re.search('^VLAN:',self.action) or self.action=='PORTCHANNEL' or self.action=='STATUS' or self.action=='SWITCHPORT' or self.action=='GETALLROUTE' or self.action=='CDPDETAIL' or self.action=='TRANSCEIVER' or self.action=='GETALLBGP' or self.action=='GETBGPTABLE' or self.action=='FEX' or self.action=='LLDPDETAIL' or self.action=='COUNTERERROR':
			liste_equipement__=[]
			if not liste_equipement:
				with open(fichier_liste_equipement,'r') as file_equipements:
					liste_equipement__=file_equipements.read().splitlines()
			else:
				liste_equipement__=liste_equipement.split(":")
				
			for ligne in liste_equipement__:
				nom_equipement=ligne.lower().replace('\n',"").replace('\r',"").replace(' ',"")
				#pdb.set_trace()
				if nom_equipement in self.known_equipments:
					equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
					self.liste_equipement.append(equipement_cur)
				else:
					while nom_equipement not in self.known_equipments:
						self.known_equipments.append_read(nom_equipement)
					equipement_cur=equipement(nom_equipement,self.known_equipments.liste_equipements[nom_equipement][0],self.known_equipments.liste_equipements[nom_equipement][1],self.known_equipments.liste_equipements[nom_equipement][2])
					self.liste_equipement.append(equipement_cur)
				OS_cur=self.known_equipments.liste_equipements[nom_equipement][0]
				type_cur=self.known_equipments.liste_equipements[nom_equipement][2]
				if self.action=='MAC':
					if OS_cur=='IOS':
						commande_cur='sh mac address-table'
					elif OS_cur=='Nexus':
						commande_cur='sh mac address-table'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh mac-address-table'
					else:
						sys.stderr.write('type OS '+OS_cur+' non pris en charge')
						os.exit('6')
				elif self.action=='DESC':
					commande_cur='sh interface description'
				
				elif re.search('^VLAN:',self.action):
					liste_vlan=self.action.split(":")[1]
					if OS_cur=='OLD-IOS':
						commande_cur=[]
						liste_vlan_cur=liste_vlans(liste_vlan)
						liste_vlan_cur_long=liste_vlan_cur.explode()
						for vlan_cur in liste_vlan_cur_long:
							commande_cur.append('sh vlan id '+vlan_cur)
					else:
						commande_cur='sh vlan id '+liste_vlan
						
				elif self.action=='GETALLARP':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip arp")
						#pdb.set_trace()
						
					elif OS_cur=='Nexus':
						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur='sh ip arp vrf all'
						commande_cur=[ "sh ip arp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						
					elif OS_cur=='XR':
						commande_cur='sh arp vrf all'
						
				elif self.action=='GETALLROUTE':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":

						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip route vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip route")
						#pdb.set_trace()
					elif OS_cur=='Nexus':
						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip route vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip route")
						#pdb.set_trace()
						
					elif OS_cur=='XR':
						commande_cur=['sh ip route vrf all','sh route']
						
				elif self.action=='GETALLBGP':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						commande_cur=[]
						tentative=1
						while tentative <=3:
							try:
								con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
								equipement_cur.Vrfs=con_get_vrf_cur.launch_withParser(ParseVrf)
								break
							except ErrorNeedRetry as error_retry:
								tentative=tentative+1
								print(error_retry)
								print("Tentative:"+str(tentative))
								pass

								
						commande_bgp_sum=[ "sh ip bgp vpnv4 vrf "+Vrf__ + " summary" for Vrf__ in  equipement_cur.Vrfs ]
						commande_bgp_sum.append("sh ip bgp summary")
						con_get_neigh_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getbgpneigh_"+nom_equipement.lower()+".log","TMP",commande_bgp_sum,timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							if Vrf__ !='GRT':
								commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__+" summary")
								commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__)
								if dict_neighbor[Vrf__]:
									for Neigh__ in dict_neighbor[Vrf__]:
										try:
											if Neigh__[2].isdigit():
												commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
												commande_cur.append("sh ip bgp vpnv4 vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
										except TypeError:
											pass
							else:
								commande_cur.append("sh ip bgp summary")
								commande_cur.append("sh ip bgp ")
								if dict_neighbor[Vrf__]:
									for Neigh__ in dict_neighbor[Vrf__]:
										try:
											if Neigh__[2].isdigit():
												commande_cur.append("sh ip bgp  neighbor "+Neigh__[0]+" routes")
												commande_cur.append("sh ip bgp  neighbor "+Neigh__[0]+" advertised-routes")
										except TypeError:
											pass
						print(commande_cur)
						#pdb.set_trace()	
						
					elif OS_cur=='Nexus':
						commande_cur=[]
						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=con_get_vrf_cur.launch_withParser(ParseVrf)
						commande_bgp_sum=[ "sh ip bgp vrf "+Vrf__ + " summary" for Vrf__ in  equipement_cur.Vrfs ]
						con_get_neigh_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getbgpneigh_"+nom_equipement.lower()+".log","TMP",commande_bgp_sum,timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_neigh_cur.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							commande_cur.append("sh ip bgp vrf "+Vrf__+" summary")
							commande_cur.append("sh ip bgp vrf "+Vrf__)
							if dict_neighbor[Vrf__]:
								for Neigh__ in dict_neighbor[Vrf__]:
									try:
										if Neigh__[2].isdigit():
											commande_cur.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
											commande_cur.append("sh ip bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
									except TypeError:
										pass
						print(commande_cur)
						#pdb.set_trace()				
										
					elif OS_cur=='XR':
						commande_cur=[]
						con_get_all_neighbor=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallneigh_"+nom_equipement.lower()+".log","TMP",'sh bgp vrf all summary',timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_all_neighbor.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							commande_cur.append("sh bgp vrf "+Vrf__+" summary")
							commande_cur.append("sh bgp vrf "+Vrf__)
							if dict_neighbor[Vrf__]:
								for Neigh__ in dict_neighbor[Vrf__]:
									if Neigh__[2].isdigit():
										commande_cur.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" routes")
										commande_cur.append("sh bgp vrf "+Vrf__+" neighbor "+Neigh__[0]+" advertised-routes")
						#print(commande_cur)
						#pdb.set_trace()
						
				elif self.action=='GETBGPTABLE':
					if OS_cur=='IOS' or OS_cur=="OLD-IOS":
						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show ip vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip bgp vpnv4 vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
						commande_cur.append("sh ip bgp")
						
					elif OS_cur=='Nexus':
						con_get_vrf_cur=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallvrf_"+nom_equipement.lower()+".log","TMP","show vrf",timeout=self.timeout,verbose=self.verbose)
						equipement_cur.Vrfs=connect_parse_with_retry(con_get_vrf_cur,ParseVrf,3)
						commande_cur=[ "sh ip bgp vrf "+Vrf__ for Vrf__ in  equipement_cur.Vrfs ]
										
					elif OS_cur=='XR':
						commande_cur=[]
						con_get_all_neighbor=connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,"TMP/"+"_getallneigh_"+nom_equipement.lower()+".log","TMP",'sh bgp vrf all summary',timeout=self.timeout,verbose=self.verbose)
						dict_neighbor=con_get_all_neighbor.launch_withParser(ParseBgpNeighbor)
						for Vrf__ in dict_neighbor.keys():
							commande_cur.append("sh bgp vrf "+Vrf__)
						for str__ in commande_cur:
							print(str__)
						#pdb.set_trace()
							
				elif self.action=='PORTCHANNEL':
					if OS_cur=='IOS':
						commande_cur='sh etherchannel summary'
					elif OS_cur=='Nexus':
						commande_cur='sh port-channel summary'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh etherchannel summary'
					elif OS_cur=='XR':
						commande_cur='sh bundle'
						
				elif self.action=='STATUS':
					if OS_cur=='IOS':
						commande_cur='sh interface status'
					elif OS_cur=='Nexus':
						commande_cur='sh interface status'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh interface status'
					elif OS_cur=='XR':
						commande_cur='sh interface brief'
				
				elif self.action=='SWITCHPORT':
					if OS_cur=='IOS':
						commande_cur='sh interface switchport'
					elif OS_cur=='Nexus':
						commande_cur='sh interface switchport'
					elif OS_cur=='OLD-IOS':
						commande_cur='sh interface switchport'

				elif self.action=='CDPDETAIL':
					commande_cur='sh cdp neighbor detail'
					
				elif self.action=='TRANSCEIVER':
					commande_cur='sh interface transceiver'
				
				elif self.action=='LLDPDETAIL':
					commande_cur='sh lldp neighbor detail'
					
				elif self.action=='COUNTERERROR':
					commande_cur='sh interface counter error'
					
				elif self.action=='FEX':
					if OS_cur=='Nexus':
						commande_cur='sh fex'
						
					else:
						commande_cur='! NON SUPPORTE'
						raise CommandNotSupported("Action:FEX "+nom_equipement+" "+OS_cur) from ValueError(OS_cur)
				
				repertoire_cur=self.repertoire
				if not os.path.exists(repertoire_cur):
					os.makedirs(repertoire_cur)
				if self.suffixe:
					output_cur=repertoire_cur+"/"+self.suffixe+nom_equipement.lower()+".log"
				else:
					output_cur=repertoire_cur+"/"+nom_equipement.lower()+".log"
				self.connexion_liste.append(connexion(equipement_cur,self.queue,self.queue_echec,liste_commandes,type_cur,output_cur,repertoire_cur,commande_cur,timeout=self.timeout,verbose=self.verbose))
				
		random.shuffle(self.connexion_liste)
		self.init_all_status()
		self.thread_retry=threading.Thread(target=self.worker_connexions_failed)	
		self.thread_retry.start()	
		
	def launch_commandes(self):
		equipement_prec="None"
		#pdb.set_trace()
		for connexion_cur in self.connexion_liste:
			if equipement_prec==connexion_cur.equipement.nom and connexion_cur.equipement.OS=='XR':
				time.sleep(0.7)
			else:
				time.sleep(0.3)

			#print("COUCOU5")
			self.nb_connexion+=1
			connexion_cur.start()
			self.liste_thread_to_wait.append(connexion_cur)
			if self.get_status(connexion_cur.equipement.nom,connexion_cur.commande_en_ligne) == "NOT INITIATED":
				self.set_status(connexion_cur.equipement.nom,connexion_cur.commande_en_ligne,"RUNNING")
			equipement_prec=connexion_cur.equipement.nom
			if self.nb_connexion==1:
				self.start_test=True
				self.lock.release()
			
		

				
	def worker_connexions_failed(self):
		"traite la queue des connexion qui nécessite un retry"
		#Traitement éventuel des échecs
		self.lock.acquire()
		equipement_prec=None
		print("WORKER...")
		try:
			while not self.get_fin() or not self.queue.empty():
				if self.isStarted():
					#print("WORKER...2")
					while not self.queue.empty():
						print("WORKER...3")
						connexion_cur_retry=self.queue.get()
						self.set_status(connexion_cur_retry.equipement.nom,connexion_cur_retry.commande_en_ligne,"RUNNING after FAIL "+connexion_cur_retry.retry.__str__()+":"+connexion_cur_retry.__str__())
						if equipement_prec==connexion_cur_retry.equipement.nom and connexion_cur_retry.equipement.OS=='XR':
							time.sleep(connexion_cur_retry.retry*self.retry_delay*0.8)
						else:
							time.sleep(connexion_cur_retry.retry*self.retry_delay*0.3)			
						connexion_cur_retry.start()
						self.liste_thread_to_wait.append(connexion_cur_retry)
						equipement_prec=connexion_cur_retry.equipement.nom
		except Error as e:
			print(e)
		finally:
			self.lock.release()
		
	def get_fin(self):
		result=True
		for connexion_cur in self.connexion_liste:
			if connexion_cur.isAlive():
				result=False
				
		for connexion_cur in self.liste_thread_to_wait:
			if connexion_cur.isAlive():
				result=False
				
		return result
	
	def isStarted(self):
		return self.start_test
			
	def print_status(self):
		for connexion_cur in self.connexion_liste:
			print(connexion_cur.equipement.nom+" "+self.action+":"+connexion_cur.status+" "+connexion_cur.commande_en_ligne)
			
	def print_connexion_echec(self):
		if not self.queue_echec.empty():
			print("Les connexions ci-dessous ont échoué:")
			while not self.queue_echec.empty():
				connexion_cur_retry=self.queue_echec.get()
				print(' - '+connexion_cur_retry.__str__()+'\n')
				
	def attendre_fin(self):
		for connexion_cur in self.connexion_liste:
			connexion_cur.join()
		self.thread_retry.join()
		for connexion_to_wait in self.liste_thread_to_wait:
			connexion_to_wait.join()
			
	def init_all_status(self):
		for connexion_cur in self.connexion_liste:
			if isinstance(connexion_cur.commande_en_ligne,str):
				self.status_all[connexion_cur.equipement.nom,connexion_cur.commande_en_ligne]="NOT INITIATED"
			elif isinstance(connexion_cur.commande_en_ligne,list):
				self.status_all[connexion_cur.equipement.nom,connexion_cur.commande_en_ligne[0]]="NOT INITIATED"
			
	def set_status(self,equipement,commande,status):
		if isinstance(commande,str):
			self.status_all[equipement,commande]=status
		elif isinstance(commande,list):
			self.status_all[equipement,commande[0]]=status
		
	def get_status(self,equipement,commande):
		resultat=""
		if isinstance(commande,str):
			resultat=self.status_all[equipement,commande]
		elif isinstance(commande,list):
			resultat=self.status_all[equipement,commande[0]]
		#print(resultat)
		return resultat
		
	def set_status_final(self):
		for connexion_cur in self.connexion_liste:
			if isinstance(connexion_cur.commande_en_ligne,str):
				commande_to_return=connexion_cur.commande_en_ligne
			elif isinstance(connexion_cur.commande_en_ligne,list):
				commande_to_return=connexion_cur.commande_en_ligne[0]+"..."
			else:
				commande_to_return="Something wrong..."

			if connexion_cur.status=="DONE":
				self.set_status(connexion_cur.equipement.nom,connexion_cur.commande_en_ligne,"DONE:"+connexion_cur.equipement.nom+"=="+commande_to_return)
			elif re.search("UNSUCCESS",connexion_cur.status):
				self.set_status(connexion_cur.equipement.nom,connexion_cur.commande_en_ligne,connexion_cur.status)
			else:
				self.set_status(connexion_cur.equipement.nom,connexion_cur.commande_en_ligne,"UNSUCCESS "+connexion_cur.__str__())
		for connexion_to_wait in self.liste_thread_to_wait:
			if isinstance(connexion_to_wait.commande_en_ligne,str):
				commande_to_return=connexion_to_wait.commande_en_ligne
			elif isinstance(connexion_to_wait.commande_en_ligne,list):
				commande_to_return=connexion_to_wait.commande_en_ligne[0]+"..."
			else:
				commande_to_return="Something wrong..."
				
			if connexion_to_wait.status=="DONE":
				self.set_status(connexion_to_wait.equipement.nom,connexion_to_wait.commande_en_ligne,"DONE:"+connexion_to_wait.equipement.nom+"=="+commande_to_return)	
			elif re.search("UNSUCCESS",connexion_to_wait.status):
				self.set_status(connexion_to_wait.equipement.nom,connexion_to_wait.commande_en_ligne,connexion_to_wait.status)	
			else:
				self.set_status(connexion_to_wait.equipement.nom,connexion_to_wait.commande_en_ligne,"UNSUCCESS "+connexion_to_wait.__str__())				
	def print_status_final(self):
		for connexion_cur in self.connexion_liste:
			try:
				print(self.get_status(connexion_cur.equipement.nom,connexion_cur.commande_en_ligne))
			except:
				print("ERROR GET STATUS")
				
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=True)
	group3=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-e", "--equipement",action="store",type=str, help="Nom de l'equipement")
	group1.add_argument("-f", "--fichier",action="store",help="fichier contenant la liste d'equipement")
	group1.add_argument("-l", "--liste_equipement",action="store",type=str, help=u"Liste d'équipements séparés par des \':\'  ")
	group1.add_argument("-E", "--Editdb",action="store",help="Edition d'une database d'equipement")
	group2.add_argument("-c", "--commandes",action="store",help="fichier contenant les commandes")
	group2.add_argument("-C", "--commande_en_ligne",action="store",help="commdande directement en argument")
	group2.add_argument("-a", "--action",action="store",help=u'Parse les outputs - actions predéfinies - exemple RUN ARP MAC')
	group2.add_argument("-m", "--modifydb_equipement",action="store",help=u'équipement à modifier')
	group2.add_argument("-s", "--suppress_db_equipement",action="store",help=u'équipement à supprimer')
	group2.add_argument("-p", "--printdb",action="store_true",help=u"afficher la base d'équipement")
	group2.add_argument("-F", "--Format",action="store_true",help=u'Fichier avec format spécifque:NOM;commande1,commande2,commande3,...',required=False)
	group3.add_argument("-o", "--output",action="store",type=str, default="NONE", help="fichier output")
	group3.add_argument("-r", "--repertoire",action="store",type=str,default="OUTPUT",help=u"répertoire contenant les outputs")
	parser.add_argument("-d", "--dbliste",action="store",type=str,default="/home/x112097/CONNEXION/Equipement.db",help="Liste des equipements connus",required=False)
	parser.add_argument("-S", "--Suffixe",action="store",type=str,help="Suffixe des fichiers Output",required=False)
	parser.add_argument("-V", "--Verbose",action="store_true",help="Affiche le stdout / Verbose",required=False)
	parser.add_argument("-t", "--timeout",action="store",type=int,default=300,help="timeout expect",required=False)
	parser.add_argument("-P", "--Parsing",action="store",type=str,default=None,help="Mode de parsing: ex VRF, MAC , ARPCISCO",required=False)
	args = parser.parse_args()
	

	#initialisation de la queue de thread en echec
	queue_need_retry=queue.Queue()
	queue_echec_final=queue.Queue()
	
	#print(args.Verbose)
	
	if args.equipement:
		E=equipement(args.equipement)
		if(args.commandes):
			C=connexion(E,queue_need_retry,queue_echec_final,args.commandes,"DEFAULT",output=args.output,repertoire=args.repertoire,verbose=args.Verbose,timeout=args.timeout)
			C.launch_commandes()
		elif(args.commande_en_ligne):
			C=connexion(E,queue_need_retry,queue_echec_final,args.commandes,"DEFAULT",output=args.output,repertoire=args.repertoire,commande_en_ligne=args.commande_en_ligne,verbose=args.Verbose,timeout=args.timeout)
			C.launch_commande_en_ligne()
		elif(args.action):
			if re.search('^ARP:',args.action):
				print("ARP")
			else:
				print ("Action non supportée")
	elif args.fichier or args.liste_equipement or args.Format:
		Liste_db_equipements=equipement_connus(args.dbliste)
		if(args.action):
				if re.search('^ARP:',args.action):
					print("ARP")
				elif args.action=='VRF':
					if args.fichier:
						Liste_E=connexions(args.fichier,queue_need_retry,queue_echec_final,Liste_db_equipements,"",repertoire=args.repertoire,action='VRF')
					elif args.liste_equipement:
						print("Action VRF incompatible avec option -l")
						sys.exit(10)
					Liste_E.launch_commandes()
					Liste_E.attendre_fin()
					Liste_E.set_status_final()
					Liste_E.print_status_final()
				elif args.action=='MAC' or args.action=='DESC' or re.search('^VLAN:',args.action) or args.action=='GETALLARP' or args.action=='GETALLROUTE' or args.action=='PORTCHANNEL' or args.action=='STATUS' or args.action=='SWITCHPORT' or args.action=='CDPDETAIL' or args.action=='TRANSCEIVER' or args.action=='GETALLBGP' or args.action=='GETBGPTABLE' or args.action=='FEX'  or args.action=='LLDPDETAIL' or args.action=='COUNTERERROR':
					#pdb.set_trace()
					if args.fichier:
						Liste_E=connexions(args.fichier,queue_need_retry,queue_echec_final,Liste_db_equipements,"",repertoire=args.repertoire,action=args.action,suffixe=args.Suffixe,verbose=args.Verbose,timeout=args.timeout)
					elif args.liste_equipement:
						Liste_E=connexions("",queue_need_retry,queue_echec_final,Liste_db_equipements,"",repertoire=args.repertoire,action=args.action,suffixe=args.Suffixe,liste_equipement=args.liste_equipement,verbose=args.Verbose,timeout=args.timeout)
					Liste_E.launch_commandes()
					Liste_E.attendre_fin()
					Liste_E.set_status_final()
					Liste_E.print_status_final()
				else:
					print ("Action non supportée")
					sys.exit(40)
				
				if args.Parsing:
					for conn__ in Liste_E.connexion_liste:
						pprint.pprint(PARSER[args.Parsing](conn__.resultat))

		elif(args.commandes):
			if args.fichier:
				Liste_E=connexions(args.fichier,queue_need_retry,queue_echec_final,Liste_db_equipements,args.commandes,repertoire=args.repertoire)
			elif args.liste_equipement:
				Liste_E=connexions("",queue_need_retry,queue_echec_final,Liste_db_equipements,args.commandes,repertoire=args.repertoire,liste_equipement=args.liste_equipement,timeout=args.timeout,verbose=args.Verbose)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()
		elif(args.commande_en_ligne):
			#pdb.set_trace()
			if args.fichier:
				Liste_E=connexions(args.fichier,queue_need_retry,queue_echec_final,Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=args.commande_en_ligne,timeout=args.timeout,verbose=args.Verbose)
			else:
				Liste_E=connexions("",queue_need_retry,queue_echec_final,Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=args.commande_en_ligne,liste_equipement=args.liste_equipement,timeout=args.timeout,verbose=args.Verbose)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()
		elif(args.Format):
			#pdb.set_trace()
			Liste_E=connexions(args.fichier,queue_need_retry,queue_echec_final,Liste_db_equipements,"",repertoire=args.repertoire,commande_en_ligne=None,timeout=args.timeout,verbose=args.Verbose,format=args.Format)
			Liste_E.launch_commandes()
			Liste_E.attendre_fin()
			Liste_E.set_status_final()
			Liste_E.print_status_final()
	elif args.Editdb:
		DB=equipement_connus(args.Editdb)
		if args.modifydb_equipement:
			#equipement__=input(u'Quel équipement doit être modifié ou ajouté:')
			DB.append_read(args.modifydb_equipement)
		elif args.suppress_db_equipement:
			#equipement__=input(u'Quel équipement doit être modifié ou ajouté:')
			DB.suppress(args.suppress_db_equipement)
		elif args.printdb:
			print(DB)		
