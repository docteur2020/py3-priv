#!/usr/bin/env python3.7
# coding: utf-8


from __future__ import unicode_literals


import argparse
import pdb
import dns.resolver
import io
from extractMacFromXls import hostnames


def getReverseDns(ListIP):
	resultat=[]
	
	for ip__ in ListIP:
		name_cur=None
		try:
			name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(ip__), dns.rdatatype.PTR, use_edns=0),'192.16.207.80').answer[0].__str__().split()[-1] 
		except IndexError:
			pass
		resultat.append(name_cur)
		
	return resultat
	
def getLigneCsv(ListInfos):
	return ';'.join([ str(info).strip() for info in ListInfos ])
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--fichier",action="store",help="Contient le fichier",required=True)
	parser.add_argument("-i", "--interface",action="store_true",help="Ajout des interfaces",required=False)
	args = parser.parse_args()
	
	resultat=io.StringIO()
	
	ip__traite=[]
	
	if args.fichier:
		with open(args.fichier,'r') as fich__:
			for ligne in fich__:
				column=ligne.split(';')
				try:
					ips_liste=eval(eval(column[4]))
					interface__=eval(column[1]).strip()
					#pdb.set_trace()
					if isinstance(ips_liste, list):     
						if ips_liste:
							if isinstance(ips_liste[0], dict):
								for ips in ips_liste:
									if ips:
										for mac in ips.keys():
											if ips[mac]:
												for ip__ in ips[mac]:
													try:
														description=ip__[1]+':'+ip__[2]
														if ip__[3] not in ip__traite:
															if args.interface:
																resultat.write("192.64.10.129   "+ip__[3]+" 5  5 "+description+"_"+interface__+"\n")
															else:
																resultat.write("192.64.10.129   "+ip__[3]+" 5  5 "+description+"\n")
															ip__traite.append(ip__[3])
													except IndexError as e:
														print(e)
													
												
				except SyntaxError as e:
					print("Syntax Error"+str(e))
					pass
				except NameError as e:
					print("Name Error:"+str(e))
					pass

	print(resultat.getvalue())
						