#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import pyparsing as pp
import cache as cc
from connexion import *
import checkMigFex as comSbe
import jinja2
import pdb
import pprint

TEMPLATE_DIR="/home/x112097/TEMPLATE/J2"
TEMPLATE_ROLLOUT='NMP Rollout - DMEP N5K Migration Lot 1 v0.1.j2'
TEMPLATE_ROLLBACK='NMP Rollback - DMEP N5K Migration Lot 1 v0.1.j2'
TEMPLATE_ROLLOUT_GENERIQUE='NMP Rollout TAG - DMEP N5K Migration Lot 1 v0.1.j2'
TEMPLATE_ROLLBACK_GENERIQUE='NMP Rollback TAG - DMEP N5K Migration Lot 1 v0.1.j2'

MODEL_FEX={ 'N2K-C2248TP-1GE':'N2K-C2248T' }

def replaceModelFex(fex_model__):
	resultat=""

	for model__ in MODEL_FEX.keys():
		if fex_model__==model__:
			resultat=MODEL_FEX[model__]
		else:
			resultat=fex_model__

	return resultat
	
	
def suppressMinus(nom):
	return nom.replace('-','',1)
	
def getSuffixeN5k(n5k):
	return n5k[:-1]
	
def minDict(dict__):
	return list(dict__.keys())[0]
	
def maxDict(dict__):
	return list(dict__.keys())[-1]

def writeConfig(config_str,fichier):
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
	
def parseFexName(String__):

	return String__.replace("-FEX",' ').replace("\FEX",' ').replace("/FEX",' ').replace('/',' ').split()
	
def replace_id(dict_id):
	def parseAction(s,l,t):
		resultat=t[0]
		dict_id['0']=str(int(dict_id['0'])+1)
		
		return "NOFEXID"+dict_id['0']
		
	return parseAction
	
def readCsvFex(csvFilename,replace=None):
	result={}
	if replace:
		tobereplaced=parseSed(replace)
	with open(csvFilename, newline='') as csvFile:
		spamreader = csv.reader(csvFile, delimiter=';', quotechar='|')
		for row in spamreader:
			try:
				[switch_src_cur,fex_old_cur]=parseFexName(row[1])
				if replace:
					switch_src_cur=switch_src_cur.replace(tobereplaced[0],tobereplaced[1])
				sn_cur=row[2]
				type_cur=row[3]
				fex_port=row[8]
				sw_dest=row[12]
				int_dest=row[19]
				if fex_old_cur in result.keys():
					if switch_src_cur in result[fex_old_cur]:
						result[fex_old_cur][switch_src_cur].append({'oldFex':fex_old_cur,'typeFex':type_cur,'fexPort':fex_port,'switchDst':sw_dest,'ifDst':int_dest,'SN':sn_cur})
					else:
						result[fex_old_cur][switch_src_cur]=[{'oldFex':fex_old_cur,'typeFex':type_cur,'fexPort':fex_port,'switchDst':sw_dest,'ifDst':int_dest,'SN':sn_cur}]
				else:
					result[fex_old_cur]={}
					result[fex_old_cur][switch_src_cur]=[{'oldFex':fex_old_cur,'typeFex':type_cur,'fexPort':fex_port,'switchDst':sw_dest,'ifDst':int_dest,'SN':sn_cur}]
			except ValueError as e:
				pdb.set_trace()
				print(e)
			except IndexError as e:
				pdb.set_trace()
				print(e)
					
	return result
				
				
def parseSed(Str__):
	resultat=[]
	Sed=pp.Literal('s/').suppress()+pp.Word(pp.alphanums+'-_')+pp.Literal('/').suppress()+pp.Word(pp.alphanums+'-_')+pp.Literal('/').suppress()+pp.Optional(pp.Literal('g')).suppress()
	
	try:
		resultat=Sed.parseString(Str__,parseAll=True).asList()
	except pp.ParseException as e:
		print("Erreur parsing l'option replace")
		print("respecter la forme sed pour remplacer s/.../.../")
		sys.exit(1)
	
	return resultat
				
				

COMMANDES={ 'INTERFACE-FEX':{ 'commandes':'sh interface fex-fabric' , 'parserStr':parseShIntFex,'parserFile':parseShIntFexFile } }

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-s","--source",action="append",help="Equipement Source",required=True)
	parser.add_argument("-r","--repertoire",action="store",help="Répertoire contenant le résultat",required=True)
	parser.add_argument("-m","--matrice",action="store",help="matrice csv",required=True)
	parser.add_argument("--renew", action="store_true",help="récupére les logs sur le n5k source",required=False)
	parser.add_argument("--onlysource", action="store_true",help="renouvelle que les logs sources",required=False)
	parser.add_argument("--onlydest", action="store_true",help="renouvelle que les logs destinations",required=False)
	parser.add_argument("--replace-source",dest='replace', action="store",help="Force le n5k source dans la matrice",required=False)
	parser.add_argument("--tag-template",dest='tagtemplate', action="store",help="Tag template",required=False)
	args = parser.parse_args()
	
	IntFexOld={}
	infoMig={}
	if args.replace:
		InfoMatrice=readCsvFex(args.matrice,args.replace)
	else:
		InfoMatrice=readCsvFex(args.matrice)
	
	print("Info Matrice")
	print(str(InfoMatrice))
	
	
	listeInterfaceDest=[]
	FirstEntry=next(iter(next(iter(InfoMatrice.values())).values()))
	
	for switch in FirstEntry:
		if switch not in listeInterfaceDest:
			listeInterfaceDest.append(switch['switchDst'])
		
	listeInterfaceSrc=args.source
	
	for source in args.source:
		IntFexOldCmdObj=comSbe.ResultCommande(source,'INTERFACE-FEX',args)
		IntFexOld[source]=IntFexOldCmdObj.getValue()
		try:
			tagMigFex="MIGFEX_"+source.upper()+"_"+listeInterfaceDest[0].upper()
			infoMigCache=cc.Cache(tagMigFex)
			infoMig[source]=infoMigCache.load()
		except ValueError as e:
			print(e)
			print("Lancer le script MigFex pour récupérer les informations de migrations avec l'option saveinfo ")
			print(" ;) il fallait y penser avant")
			print("TAG:","MIGFEX_"+source.upper()+"_"+listeInterfaceDest[0].upper())
			raise(e)
		
	
	print("Interface Fex source:")
	print(str(IntFexOld))
	
	print()
	print()
	
	newFex={}
	for oldFex in InfoMatrice.keys():
		for switch in InfoMatrice[oldFex].keys():
			newFexIdCur=infoMig[switch]['fex'][oldFex]
			newFex[newFexIdCur]=[InfoMatrice[oldFex][switch],{'oldSwitch':switch}]
		
	loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
	env = jinja2.Environment( loader=loader)
	env.filters['modelfex']=replaceModelFex
	env.filters['suffixen5k']=getSuffixeN5k
	env.filters['supmin']=suppressMinus
	env.filters['mindict']=minDict
	env.filters['maxdict']=maxDict
	if args.tagtemplate:
		TEMPLATE_ROLLOUT_TAG=TEMPLATE_ROLLOUT_GENERIQUE.replace('TAG',args.tagtemplate)
		TEMPLATE_ROLLBACK_TAG=TEMPLATE_ROLLBACK_GENERIQUE.replace('TAG',args.tagtemplate)
	else:
		TEMPLATE_ROLLOUT_TAG=TEMPLATE_ROLLOUT
		TEMPLATE_ROLLBACK_TAG=TEMPLATE_ROLLBACK	
	templates={'rollout':env.get_template(os.path.basename(TEMPLATE_ROLLOUT_TAG)),'rollback':env.get_template(os.path.basename(TEMPLATE_ROLLBACK_TAG))}
	result={}
	
	
	print("info de  Migration")
	pprint.pprint(str(infoMig))
	
	print("New Fex info:")
	pprint.pprint(str(newFex))
	print(str(newFex.keys()))
	
	print('Switch Dest:')
	print(str(listeInterfaceDest))
	for modele in templates.keys():
		result[modele]=templates[modele].render({"infoMatrice":InfoMatrice,"intFexOld":IntFexOld,"SwitchDst":listeInterfaceDest,"SwitchSrc":listeInterfaceSrc,"infoMig":infoMig,"newFex":newFex})
		print(result[modele])
		
	#Engregistrement des config
	
	TEMPLATE={'rollout':TEMPLATE_ROLLOUT_TAG,'rollback':TEMPLATE_ROLLBACK_TAG}
	
	for modele in templates.keys():
		filename=TEMPLATE[modele].replace('N5K',getSuffixeN5k(args.source[0])+" FEX ").replace('j2','TXT')
		writeConfig(result[modele],args.repertoire+'/'+filename)
	