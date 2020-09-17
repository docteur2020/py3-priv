# -*- coding: utf-8 -*- #!/usr/bin/env python3.7
# coding: utf-8
#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import pdb
import argparse
import re
from ParsingShow import writeCsv

def test_uplink(str):
	return re.search('[Cc][Ff][Dd]|[Cc][Ll][Ss]|[nN]7[Kk]',str)

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--fichier",action="store",help="Contient le fichier",required=True)
	parser.add_argument("-c", "--csv",action="store",help="Contient le fichier resultat en csv",required=False)
	args = parser.parse_args()
	
	info_ip_unknown=[]
	
	resultat=[]
	
	if args.fichier:
		with open(args.fichier,'r') as fich__:
			for ligne in fich__:
			
				datas_line=ligne.replace('\"','').split(';')
				try:
					equipement=datas_line[0]
					if equipement=="EQUIPMENT":
						continue
					interface=datas_line[1]
					description=datas_line[2]
					ips=eval(datas_line[4])
					macs_liste=eval(str(datas_line[3]))
				except NameError:
					continue
				except TypeError:
					pdb.set_trace()
				
				if test_uplink(description) or (re.search('[Cc][Ff][Dd]',equipement) and description == 'None'):
					continue
				
				if macs_liste and macs_liste!="MAC" and macs_liste!="None":
					#pdb.set_trace()
					for mac in macs_liste:
						try:
							ip_liste=ips[0][mac[1]]
						except KeyError:
							ip_liste=[]
						except IndexError:
							ip_liste=[]
						if ip_liste:
							for ip in ip_liste:
								if ip[2]=="Vlan"+mac[0] or not re.search('Vlan',ip[2]):
									info_ligne=[mac,equipement,interface,description,ip[1:4]]
									if info_ligne not in resultat:
										resultat.append(info_ligne)
								else:
									info_ligne=[mac,equipement,interface,description,None]
									if info_ligne not in resultat:
										resultat.append(info_ligne)
						else:
							info_ligne=[mac,equipement,interface,description,None]
							if info_ligne not in resultat:
								resultat.append(info_ligne)
				else:
					info_ligne=[None,equipement,interface,description,None]
					if info_ligne not in resultat:
						resultat.append(info_ligne)
				
				print(str(info_ligne))
						
		for line in resultat:
			print(str(line))
						
	if args.csv:
		writeCsv(resultat,args.csv)
