#!/usr/bin/python


class FilterModule(object):
	def filters(self):
		return { 'get_data_l3out':self.getDataL3out ,'tenant_epgs': self.getTenantEpgs , 'tenant_epgs_from_row': self.getTenantEpgsFromRow , 'set_epgs': self.setEpg ,'set_bds': self.setBd , 'set_subnets': self.setSubnet ,'set_l3out': self.setL3out ,'formatportdata':self.formatportdata }

	
	def getDataL3out(self,l3outs,bds_vrf,subnets_bd):
		resultat=[]
		for l3out in l3outs:
			try:
				tenantCur=l3out['tenant']
				vrfCur=l3out['vrf']
				l3outCur=l3out['l3out']
				bds_cur=bds_vrf[tenantCur][vrfCur]
				bdsCurSubnetList=subnets_bd[tenantCur]
			except KeyError as E:
				print(E)
				continue
			for bd in bds_cur:
				if bd in bdsCurSubnetList:
					resultat.append({'tenant':tenantCur,'l3out':l3outCur,'bd':bd})
		return resultat	
	
	def getTenantEpgs(self, chains):
		resultat=[]
		list_tenant=chains.split('|')
		
		for tenant_epgs in list_tenant:
			data_cur=tenant_epgs.split(':')
			tenant_cur=data_cur[0]
			list_vlans_cur=data_cur[1].split(',')
			
			resultat.append({'tenant': tenant_cur , 'epgs':list_vlans_cur})
			
		return resultat
		
		
	def getTenantEpgsFromRow(self, list_chains):
		resultat=[]
		for chains in list_chains:
			chains['vlans']=self.getTenantEpgs(chains['vlans'])
			
			resultat.append(chains)
				
		return resultat
		
	def setEpg(self, epgs_dict):
		resultat={}
		
		for epgsraw in  epgs_dict['current']:
			dnCur=epgsraw['fvAEPg']['attributes']['dn']
			dnCurList=dnCur.split('/')
			tenantCur=dnCurList[1].replace('tn-','')
			apCur=dnCurList[2].replace('ap-','')
			epgname=dnCurList[3].replace('epg-','')
			
			if tenantCur not in resultat:
				resultat[tenantCur]={epgname:apCur}
			else:
				resultat[tenantCur][epgname]=apCur
		return resultat


	def setSubnet(self, subnets_dict):
		resultat={}
		
		for subnetraw in  subnets_dict['current']:
			dnCur=subnetraw['fvSubnet']['attributes']['dn']
			dnCurList=dnCur.split('/')
			tenantCur=dnCurList[1].replace('tn-','')
			if 'TN_' not in tenantCur:
				continue
			bdCur=dnCurList[2].replace('BD-','')
			subnet=dnCurList[3].replace('subnet-[','').replace(']','')
			
			if tenantCur in resultat:
				if bdCur not in resultat[tenantCur]:	
					resultat[tenantCur].append(bdCur)
			else:
				resultat[tenantCur]=[bdCur]
					
			
		return resultat
		
		
	def setL3out(self, l3out_dict):
		resultat=[]
		
		for l3outraw in  l3out_dict['current']:
			dnCur=l3outraw['l3extOut']['attributes']['dn']
			dnCurList=dnCur.split('/')
			tenantCur=dnCurList[1].replace('tn-','')
			l3outCur=l3outraw['l3extOut']['attributes']['name']
			vrf=None
			for child in l3outraw['l3extOut']['children']:
				if 'l3extRsEctx' in child:
					vrf=child['l3extRsEctx']['attributes']['tnFvCtxName']
					break;
				
			resultat.append({'l3out':l3outCur , 'tenant':tenantCur , 'vrf':vrf })

		return resultat	

		
	def setBd(self, bds_dict):
		resultat={}
		
		for bdraw in  bds_dict['current']:
			dnCur=bdraw['fvBD']['attributes']['dn']
			dnCurList=dnCur.split('/')
			tenantCur=dnCurList[1].replace('tn-','')
			bdCur=bdraw['fvBD']['attributes']['name']
			vrf=None
			for child in bdraw['fvBD']['children']:
				if 'fvRsCtx' in child:
					vrf=child['fvRsCtx']['attributes']['tnFvCtxName']
					break;
				
			
			if tenantCur not in resultat:
				resultat[tenantCur]={vrf:[bdCur]}
			else:
				if vrf in resultat[tenantCur]:
					resultat[tenantCur][vrf].append(bdCur)
				else:
					resultat[tenantCur][vrf]=[bdCur]
		return resultat
		
	def formatportdata(self , datas_raw):
		resultat=[]
		
		for entry in datas_raw:
			data_tenant={}
			tenants_info=entry['vlans'].split('|')
			for tenant_info in tenants_info:
				info_cur_list=tenant_info.split(':')
				tenant_cur=info_cur_list[0]
				vlan_list_cur=info_cur_list[1].split(',')
				for vlan in vlan_list_cur:
					resultat.append({'tenant':tenant_cur,'epg':'EPG_'+vlan,'vlan': vlan , 'mode':entry['mode'],'port': entry['port'] , 'podid':str(entry['leaf'])[0], 'leaf':entry['leaf'] ,'ipg':entry['ipg']})
					
		return resultat