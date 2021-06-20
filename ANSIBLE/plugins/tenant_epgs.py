#!/usr/bin/python
class FilterModule(object):
	def filters(self):
		return { 'tenant_epgs': self.getTenantEpgs }

	def getTenantEpgs(self, chains):
		resultat=[]
		list_tenant=chains.split('|')
		
		for tenant_epgs in list_tenant:
			data_cur=tenant_epgs.split(':')
			tenant_cur=data_cur[0]
			list_vlans_cur=data_cur[1].split(',')
			
			resulat.append({'tenant': tenant_cur , 'epgs':list_vlans_cur})
			
		return resultat