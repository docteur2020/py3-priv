#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-


import pexpect
import io
import dns.resolver
import os
import threading
from pexpect import pxssh
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect , exceptions
import sys
import re

def get_type_oob(nom__):
	#pdb.set_trace()
	resultat="DIRECT"
	fichier_liste_rebond="/home/x112097/LISTE/LISTE_REBOND.TXT"
	
	with open(fichier_liste_rebond,'r') as file_rebond:
		for line in file_rebond:
			mots=line.split()
			if mots[0]==nom__:
				resultat=mots[1]
				break
	
	return resultat
	
def getIP(nom):
		
		IP_1=None
		IP_2=None
		dns_requete1=dns.query.udp(dns.message.make_query(nom+'.dns63.socgen', dns.rdatatype.A, use_edns=0),'192.16.207.80')
		dns_requete2=dns.query.udp(dns.message.make_query(nom+'fr.world.socgen', dns.rdatatype.A, use_edns=0),'192.16.207.80')
		
		if dns_requete1.rcode()==0:
			IP_1=dns_requete1.answer[0].__str__().split()[4]
			
		if dns_requete2.rcode()==0:
			IP_2=dns_requete2.answer[0].__str__().split()[4]
			
		return IP_1 or IP_2 or nom.lower()
		
class consoleOob(object):	
	def __init__(self,nom='TBD',ip='0.0.0.0',fileConnection='CONNEXION/default.txt',bastion='paer'):
		self.nom=nom
		self.ip=getIP(nom)
		self.fileConnection=fileConnection
		self.bastion=bastion
		
		
	def __str__(self):
		resultat=io.StringIO()
		resultat.write('NOM:'+self.nom+'\n')
		resultat.write('IP:'+self.ip+'\n')
		resultat.write('BASTION:'+self.bastion+'\n')
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str

		
class customTelnet(threading.Thread):
	def __init__(self,nom='TBD',port='23',bastion='paer',verbose=False):
		threading.Thread.__init__(self)
		self.nom=nom.upper()
		self.ip=getIP(nom)
		self.port=port
		self.bastion=bastion
		self.type=get_type_oob(nom)
		self.proxy=pxssh.pxssh()
		self.verbose=verbose
		self.regex_match=regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\r[a-zA-Z]\\S+>','\n[a-zA-Z]\\S+>']
		self.hostname='UNKNOWN'
		
	def __str__(self):
		resultat=io.StringIO()
		resultat.write('NOM:'+self.nom+'\n')
		resultat.write('IP:'+self.ip+'\n')
		resultat.write('PORT:'+self.port+'\n')
		resultat.write('BASTION:'+self.bastion+'\n')
		resultat.write('TYPE:'+self.type+'\n')
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	def run(self):
		#pdb.set_trace()
		print("Starting connexion vers "+ self.nom)	
		
		self.connexion_bastion()
		self.connexion_oob()
		self.hostname=self.get_hostname()
		self.close_connexion()
		
	def connexion_bastion(self):
		
		if(self.bastion=='paer'):
			try:
				regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']
				if self.verbose:
					self.proxy.logfile = sys.stdout.buffer
				self.proxy.login("192.64.10.129",'x112097','B2rn1s12345!')
			except pxssh.ExceptionPxssh as e:
				print("pxssh failed on login:")
				self.status="FAILED:"+str(e)
				print(str(e))
		else:
			print('Rebond non supporte')
			os.exit(10)
	
	
	def connexion_oob(self):
	
		try:
			self.proxy.logfile = sys.stdout.buffer
			if(self.type=='DIRECT'):
				self.proxy.sendline ('telnet '+self.ip+' '+self.port)
				expect_value=self.proxy.expect(['sername','\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','Escape character'])
				if expect_value==0:
					self.proxy.sendline('BackupAdmin')
					self.proxy.expect('password')
					self.proxy.sendline('n0acsLogin')
					self.proxy.expect(self.regex_match)
				elif expect_value==1 or expect_value==2:
					self.proxy.sendline("\n")
					self.proxy.expect(self.regex_match)
				elif expect_value==3:
					self.proxy.sendline("\n")
					expect_value1=self.proxy.expect(['sername|login','\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','Escape character'])
					if expect_value1==0:
						self.proxy.sendline('BackupAdmin')
						self.proxy.expect('[Pp]assword')
						self.proxy.sendline('n0acsLogin')
						self.proxy.expect(self.regex_match)
					elif expect_value1==1 or expect_value1==2:
						self.proxy.sendline("\n")
						self.proxy.expect(self.regex_match)
								
					
				else:
					os.exit(10)
			else:
				print("Type de connexion inconnu:"+self.type)
				
		except ExceptionPexpect as ep:
			print("pexpect failed on telnet OOB")
			self.status="FAILED TELNET OOB:"+str(e)+'=='+self.ip+':'+self.port
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED TELNET OOB:"+"TIMEOUT"+'=='+self.ip+':'+self.port
			
	def get_hostname(self):
		
		hostname='UNKNOWN'
		try:
			#self.proxy.logfile = sys.stdout.buffer
			if(self.type=='DIRECT'):
				self.proxy.sendline ('sh start | i ^hostname')
				expect_value=self.proxy.expect(['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\r[a-zA-Z]\\S+','\n[a-zA-Z]\\S+>'])
				if expect_value in [ i for i in range(0,4)]:
					hostname_raw=self.proxy.before
					print('TYPE:'+str(type(hostname_raw)))
				else:
					os.exit(10)
			else:
				print("Type de connexion inconnu:"+self.type)
				
		except ExceptionPexpect as ep:
			print("pexpect failed on telnet OOB")
			self.status="FAILED TELNET OOB:"+str(e)+'=='+self.ip+':'+self.port
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED TELNET OOB:"+"TIMEOUT"+'=='+self.ip+':'+self.port	
		
		print('HOSTNAME:'+str(hostname))
		
		hostname=self.parseHostname(hostname_raw.decode("utf-8") )
		
		print('HOSTNAME:'+hostname)
		
		return hostname
		
	def close_connexion(self):
		
		hostname='UNKNOWN'
		try:
			self.proxy.sendline('exit')
			self.proxy.close()	
		except ExceptionPexpect as ep:
			print("pexpect failed on close connexion")
			self.status="FAILED EXIT:"+str(e)+'=='+self.ip+':'+self.port
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED EXIT:"+"TIMEOUT"+'=='+self.ip+':'+self.port	

	def parseHostname(self,output_str):
		hostname=''
		#print('output str:')
		#print(output_str)
		for line in output_str.split('\n'):
			#print("LINE:"+line)
			try:
				mots=line.split()
				#print('MOTS:')
				#print(mots)
				if mots[0]=='hostname':
					hostname=mots[1]
					break;
			except:
				hostname='UNKNOWN'
		return hostname
		
class bastion(object):
	def __init__(self,nom):
		self.nom=nom
		
if __name__ == '__main__':
	"Fonction principale"
	
	print(consoleOob('TigCtxPax-p2'))
	print(customTelnet('SC1JVE-OOB-CTX-05'))
	A=customTelnet('OOB-TIGR4K-06',port='7031',verbose=True)
	A.start()
	A.join()
	print(A.hostname)
	
	

