[x112097@PAERSC01 dmoScripts]$ more sg_apc_check_epg.py
#!/home/reslocal/dmoScripts/APPLIS/bin/python2.7

from __future__ import print_function
import sys
import argparse
import ipaddress
import smtplib
import pwd
import os
import getpass
from logging import Logger
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import logging
import csv
import re
import atexit
import copy
import csv
import pwd

from dmoPy.aci.apic.socgensite2 import SocgenSite as SocgenSite
import  dmoPy.aci.apic.socgenbase2 as socgenbase2
from cobra.modelimpl.l1.ethif import EthIf

from tabulate import tabulate


def show_faults(site_obj=None,epg_list=None,tenant=None):

    socgenbase2.print_faults(site_obj=site_obj,list_of_obj=epg_list)




def encap_matches_vlan_pool(epg_encap,vlan_pool_blocks):
    epg_encap=re.sub('vlan-','',epg_encap)
    epg_encap=int(epg_encap)

    list_of_vlans=[]

    for block in vlan_pool_blocks:
        from_vlan=getattr(block,'from')
        from_vlan=re.sub('vlan-','',from_vlan)
        from_vlan=int(from_vlan)
        to_vlan=block.to
        to_vlan=re.sub('vlan-','',to_vlan)
        to_vlan=int(to_vlan)+1
        list_of_vlans.extend(list(range(from_vlan,to_vlan)))

    if epg_encap in list_of_vlans:
        return True
    return False

def show_description():
    print('''
TBD
    ''')

def vpc_check(epg,site_obj=None,tenant=None,vpc=None,vrfs=None,prefix=''):
    if vpc.descr:
        descr=' [desc: %s]'%vpc.descr
    else:
        descr=''
    print(prefix+"vpc: %s%s"%(vpc.name,descr))
    generic_intf_check(epg,site_obj=site_obj,tenant=tenant,intf=vpc,vrfs=vrfs,prefix=prefix)

def eth_check(epg,site_obj=None,tenant=None,vrfs=None,eth_sys=None,node_sys=None,prefix=''):
    if eth_sys.descr:
        descr=' [desc: %s]'%eth_sys.descr
    else:
        descr=''
    print(prefix+"Node: %s eth: %s%s"%(node_sys.name,eth_sys.id,descr))
    generic_intf_check(epg,site_obj=site_obj,tenant=tenant,vrfs=vrfs,prefix=prefix,node_sys=node_sys,eth_sys=eth_sys)


def generic_intf_check(epg,site_obj=None,tenant=None,intf=None,vrfs=None,node_sys=None,eth_sys=None,prefix=''):

    orig_prefix=prefix
    prefix=prefix+'  '
    if eth_sys is None:
        aep_relations=site_obj.get_this_intf_aep_relations(intf=intf)
    else:
        aep_relations=site_obj.get_this_intf_sys_aep_relations(intf_sys=eth_sys)

    if not len(aep_relations):
        print(prefix+"\x1b[1m\x1b[5m\x1b[31m/!\\ No AEP/!\\\x1b[0m")
        physicals=None


    physicals=[]
    for aep_relation in aep_relations:
        try:
            aep=site_obj.get_obj_by_dn(dn=aep_relation.tDn)
        except Exception as e:
            print("/!\\ Cannot find AEP: %s /!\\"%aep_relation.tDn)
        print(prefix+"AEP: %s"%aep.name)
        domain_relations=site_obj.get_this_aep_dom_relations(aep=aep)
        if not len(domain_relations):
            print(prefix+'  '+"\x1b[1m\x1b[5m\x1b[31m/!\\ No Physical domain/!\\\x1b[0m")
            continue
        print(prefix+'  '+"Physical domains:")
        for domain_relation in domain_relations:
            try:
                physical=site_obj.get_obj_by_dn(dn=domain_relation.tDn)
                physicals.append(physical)
                print(prefix+'   - %s'%physical.name)
            except:
                print(prefix+"   /!\\ Cannot find physical domain: %s /!\\"%domain_relation.tDn)




    print()
    prefix=orig_prefix
    print(prefix+"EPG: %s"%(epg.name))

    dom_relations=site_obj.get_epg_dom_relations(epg=epg)
    if not len(dom_relations):
        print(prefix+'  \x1b[1m\x1b[5m\x1b[31m/!\\ No Physical domain /!\\\x1b[0m')
        return

    if physicals is not None:
        physicals=set(physicals)
    print(prefix+'  Physical domains:')

    epg_physicals=[]
    for dom_relation in dom_relations:
        try:
            epg_physical=site_obj.get_obj_by_dn(dom_relation.tDn)
            epg_physicals.append(epg_physical)
            print(prefix+'    - %s' %epg_physical.name)
        except:
            print("Pb finding : %s "%dom_relation.tDn)

    epg_physicals=set(epg_physicals)

    prefix=orig_prefix
    print()

    bindings=site_obj.get_this_epg_static_bindings(epg=epg)

    found=False
    for b in bindings:
        try:
            target_obj=site_obj.get_obj_by_dn(dn=b.tDn)
        except:
            print("Cannot find: %s"%b.tDn)

        if node_sys is None and target_obj.name == intf.name:
            print(prefix+"EPG bound to intf. Encapsulation: \x1b[1m\x1b[32m%s\x1b[0m [mode: %s]"%(b.encap,b.mode))
            epg_encap=b.encap
            found=True
            break
        elif node_sys is not None:
            try:
                parent_node=site_obj.get_obj_by_dn(dn=target_obj.parentDn)
            #print("parent_node=%s"%parent_node.__dict__)
            except:
                print("Cannot find: %s"%target_obj.parenDn)
            try:
                parent_ids=[parent_node.nodeId]
            except:
                parent_ids=[parent_node.nodeAId,parent_node.nodeBId]
            if node_sys.id in parent_ids and target_obj.name==eth_sys.id:
                print(prefix+"EPG  bound to intf. Encapsulation: \x1b[1m\x1b[32m%s\x1b[0m"%b.encap)
                epg_encap=b.encap
                found=True
                break


    if not found:
        print(prefix+"EPG is not bound to interface")
        return


    if physicals is not None:
        epg_physicals_names=set([x.name for x in epg_physicals])
        physicals_names=set([x.name for x in physicals])
        matching_pdoms=[x for x in epg_physicals_names.intersection(physicals_names)]
        if not len(matching_pdoms):
            print(prefix+"/!\\ No matching pdoms /!\\")
            return
        print(prefix+"Intf / EPG Matching pdoms: %s"%matching_pdoms)
    else:
        print(prefix+"/!\\ No matching pdoms as Intf has no AEP /!\\")
    vlan_matching=[]
    for epg_physical in epg_physicals:
        vlan_pool_relations=site_obj.get_this_dom_vlan_relations(dom=epg_physical)
        for vlan_pool_relation in vlan_pool_relations:
            try:
                vlan_pool=site_obj.get_obj_by_dn(dn=vlan_pool_relation.tDn)
            except:
                print("Cannot find Vlan pool: %s"%vlan_pool_relation.tDn)
                continue
            vlan_pool_blocks=site_obj.get_this_vlan_pool_blocks(pool=vlan_pool)
            if encap_matches_vlan_pool(epg_encap,vlan_pool_blocks):
                vlan_matching.append(epg_physical)

    if not len(vlan_matching):
        print(prefix+"/!\\ EPG Vlan encap matches no PDOM /!\\")
        return

    vlan_matching_names=[x.name for x in vlan_matching]
    print(prefix+"Encap matches following PDOMs: %s"%vlan_matching_names)

    matching_pdoms=set(matching_pdoms)
    vlan_matching_names=set(vlan_matching_names)

    selected_pdoms=matching_pdoms.intersection(vlan_matching_names)

    print()
    if not len(selected_pdoms):
        print("==> \x1b[1m\x1b[5m\x1b[31m/!\\ No selected PDOM(s) /!\\\x1b[0m")
    else:
        print("==> Selected PDOM(s): \x1b[1m\x1b[32m%s\x1b[0m"%list(selected_pdoms))



def print_contracts(obj=None,site_obj=None,prefix=''):
    contract_relations=site_obj.get_obj_contract_relations(obj=obj)
    consumers=contract_relations['consumer']
    providers=contract_relations['provider']
    if not len(providers):
        print(prefix+"/!\\ Does not provide contracts /!\\")
    else:
        print(prefix+"Provides the following contracts:")
        for provider in providers:
            print(prefix+"  - %s"%provider.tnVzBrCPName)

    if not len(consumers):
        print(prefix+"/!\\ Does not consume contracts /!\\")
    else:
        print(prefix+"Consumes the following contracts:")
        for consumer in consumers:
            print(prefix+"  - %s"%consumer.tnVzBrCPName)



def print_networks(site_obj=None,l3out_relation=None,tenant=None,prefix=''):
    l3out=site_obj.get_this_l3out(tenant=tenant,name=l3out_relation.tnL3extOutName)
    networks=site_obj.get_l3out_networks(l3out=l3out)

    if len(networks)==0:
        print(prefix+"/!\\ No Networks defined /!\\")
        return

    print(prefix+"Networks")
    prefix='  '+prefix

    for network in networks:
        print(prefix+network.name)
        print_contracts(obj=network,site_obj=site_obj,prefix='  '+prefix)

def epg_check(epg,site_obj=None,tenant=None,vrfs={}):
    bd_relations=site_obj.get_epg_bd_relations(epg=epg)
    for bd_relation in bd_relations:
        bd=site_obj.get_this_bd(tenant=tenant,name=bd_relation.tnFvBDName)[0]

        try:
            vrf=vrfs[bd.scope]
        except:
            vrf=site_obj.get_this_vrf(tenant=tenant,scope=bd.scope)[0]
            vrfs[bd.scope]=vrf

        print('- VRF: %s [pcTag: %s][scope: %s]'%(vrf.name,vrf.pcTag,vrf.scope))
        print('  - BD: %s [pcTag: %s][seg: %s][l2stretched: %s][interSiteBum: %s][arpFlood: %s][unicastRoute: %s][ipLearning: %s]'%(bd_relation.tnFvBD
Name,bd.pcTag,bd.seg,bd.intersiteL2Stretch,bd.intersiteBumTrafficAllow,bd.arpFlood,bd.unicastRoute,bd.ipLearning))
        subnets=site_obj.get_bd_subnets(bd=bd)
        if not len(subnets):
            print('      /!\\ No Subnets /!\\')
        else:
            print("      Subnets:")
            for subnet in subnets:
                print("        - %s [scope: %s]"%(subnet.ip,subnet.scope))

        l3out_relations=site_obj.get_bd_l3out_relations(bd=bd)
        if not len(l3out_relations):
            print('      /!\\ No L3out /!\\')
        else:
            print("      L3Outs:")
            for l3out_relation in l3out_relations:
                print("      - %s"%(l3out_relation.tnL3extOutName))
                print_networks(site_obj=site_obj,l3out_relation=l3out_relation,tenant=tenant,prefix='            ')


        print("    - EPG: %s [pcTag: %d (%s)][prefGroup: \x1b[1m\x1b[5m%s\x1b[0m]"%(epg.name,int(epg.pcTag),hex(int(epg.pcTag)),epg.prefGrMemb))

    dom_relations=site_obj.get_epg_dom_relations(epg=epg)
    if not len(dom_relations):
        print("       \x1b[1m\x1b[5m\x1b[31m/!\\ No Physical Domain configured /!\\\x1b[0m")
    else:
        print("       Physical domains:")

    for dom_relation in dom_relations:
        print("         -  %s"%dom_relation.tDn)

    print_contracts(obj=epg,site_obj=site_obj,prefix='       ')





    print()




def show_sclass(options,list_of_sites):

    for site_obj in list_of_sites:
        epg_list=[]

        tenant=site_obj.get_this_tenant(name=options.tenant)
        if tenant.nameAlias:
            tenant_alias=' (%s)'%tenant.nameAlias
        else:
            tenant_alias=''

        print("="*30)
        print("SITE: %s [tenant: %s%s]"%(site_obj.name,tenant.name,tenant_alias))
        print("="*30)
        for epg_name in sorted(options.epg):
            try:
                epg_list.extend(site_obj.get_matching_epgs(tenant=tenant,name=epg_name))
            except Exception as e:
                print("Error retrieving EPG %s: %s"%(epg_name,e),file=sys.stderr)
        for sclass in options.sclass:
            try:
                epg_list.extend(site_obj.get_matching_epgs(tenant=tenant,sclass=sclass))
            except Exception as e:
                print("Error retrieving EPG %s: %s"%(sclass,e),file=sys.stderr)

        to_be_printed=[]
        for epg in sorted(epg_list,key=lambda x: int(x.pcTag)):
            to_be_printed.append([epg.pcTag,epg.name,epg.prefGrMemb])

        print(tabulate(to_be_printed,headers=["Sclass","EPG Name","prefGroup"],tablefmt='psql'))
        print()








def main():
    parser=argparse.ArgumentParser(usage='%(prog)s  --fabric fabricName [options]' )
    parser.add_argument('-f',"--fabric",dest="fabric",default=None,action="store",help=u"Fabric Name")
    parser.add_argument('-s',"--site",dest="site",default=[],action="append",help=u"Site Name. Can be specified multiple times")
    parser.add_argument("--all-sites",dest='all_sites',default=False,action="store_true",help="All sites")
    parser.add_argument('-t',"--tenant",dest="tenant",default=None,action="store",help=u"Tenant Name")
#    parser.add_argument('--search',dest='search',default=False,action="store_true",help="Search EPG")
    parser.add_argument("--epg",dest="epg",default=[],action="append",help=u"EPG Name")
    parser.add_argument("--vlan",dest="vlan",default=None,action="store",help=u"Format: vlan1,vlan2-vlan3 Used to construct EPG name.")
    parser.add_argument("--sclass",dest="sclass",default=[],action="append",help="Search epg by sclass")
    parser.add_argument("--check",dest="check",default=False,action="store_true",help="Check EPG global configuration")
    parser.add_argument("--vpc",dest="vpc",default=None,action="store",help="Check EPG and VPC physical domains")
    parser.add_argument("--nodeid",metavar="nodeid",dest="node",default=None,action="store",help="/!\\ .Node. To be used with '--eth'.")
    parser.add_argument("--eth",dest="eth",default=None,action="store",help="/!\\ Check EPG and Interface physical domains")

    parser.add_argument("--list-tenants",dest="list_tenants",default=False,action="store_true",help="List the tenants")
    parser.add_argument("--list-nodes",dest="list_nodes",default=False,action="store_true",help="List the leaf nodes.")
    parser.add_argument("--list-vpcs",dest="list_vpcs",default=False,action="store_true",help="List vpcs.")
    parser.add_argument("--list-sites",dest="list_sites",default=False,action="store_true",help="List sites.")

    parser.add_argument("--show-sclass",dest="show_sclass",default=False,action="store_true",help="Show Sclass of the EPGs.")



    parser.add_argument("--show-faults",dest="show_faults",default=False,action='store_true',help="Show Faults on the EPG")
    parser.add_argument("--string",dest="string",default=None,action="store",help="Show only vpcs matching this string")

    parser.add_argument('-u','--user',dest='user',default=None,action='store',help='User to be used to connect the APIC. If not specified: use your lo
gin account.')

    parser.add_argument('-p','--password',dest='password',default=None,action='store',help='User passsword')
    parser.add_argument('--logfile',dest="logfile",default=None,action="store",help=u"Where to log. optional")
    parser.add_argument('--disable-stdout',dest="disable_stdout",default=False,action="store_true",help=u"Disable stdout output.")
    parser.add_argument('--debug',dest="debug",default=False,action="store_true",help=u"Enable debug in the libraries.")
#    parser.add_argument('-H',dest="detailed_help",default=False,action="store_true",help=u"Print detailed help.")





    options=parser.parse_args()
    hash_of_password={}


    if options.user is None:
        options.user=pwd.getpwuid(os.getuid()).pw_name

    if options.fabric is None:
        print('/!\ Fabric name is mandatory /!\\',file=sys.stderr)
        sys.exit(1)


    if (options.eth and not options.node) or (options.node and not options.eth):
        print("'--node' and '--eth' must be used together",file=sys.stderr)
        sys.exit(1)

 #   if options.site is None:
 #       print('/!\ Site name is mandatory /!\\',file=sys.stderr)
 #       sys.exit(1)



    if options.vlan:
        temp_list=socgenbase2.vlan_parsing(options.vlan)
        options.epg.extend([socgenbase2.epg_from_vlan(x) for x in temp_list])



    config_file=socgenbase2.get_conf_filename(options.fabric)


    if options.list_sites:
        socgenbase2.print_sites(conf=config_file)
        sys.exit(0)

    if not len(options.site) and not options.all_sites:
        print("/!\\ '--site' is mandatory /!\\",file=sys.stderr)
        sys.exit(1)


    if options.all_sites:
        try:
            options.site=socgenbase2.list_of_site_names(conf=config_file)
        except Exception as e:
            print("Error during '%s' processing: %s"%e,file=sys.stderr)
            sys.exit(1)


    if not options.tenant and not (options.list_tenants or options.list_vpcs or options.list_nodes or options.list_sites):
        options.tenant=socgenbase2.get_default_tenant(config_file)
        print("Using default tenant: '%s'"%options.tenant)

    try:
        log=Logger('dmo.aci.apic')
        log.setLevel(logging.INFO)
        FORMAT="[%(asctime)s][%(levelname)s]  %(message)s"
        formatter=logging.Formatter(fmt=FORMAT)
        if options.logfile is not None:
            handler=WatchedFileHandler(options.logfile,encoding="utf-8")
            handler.setFormatter(formatter)
            log.addHandler(handler)
    except Exception as e:
        print("/!\\ Pb with logfile :'%s' I quit./!\\"%e,file=sys.stderr)
        sys.exit(1)


    if not options.disable_stdout:
        handler_stdout=StreamHandler(stream=sys.stdout)
        handler_stdout.setFormatter(formatter)
        log.addHandler(handler_stdout)


    if not options.password:
        socgenbase2.get_passwd(options)

    if options.debug:
        log.setLevel(logging.DEBUG)


    list_of_sites=[]
    for s in sorted(options.site):
        try:
            log.debug("Creating '%s' site object"%s)
            site_obj=SocgenSite(site=s,conf=config_file,log=log)
            list_of_sites.append(site_obj)
            site_obj.initialize(user=options.user,password=options.password)
        except Exception as e:
            raise Exception("Cannot construct Site Object for site '%s': '%s'"%(s,e))


    for s in list_of_sites:
        atexit.register(socgenbase2.exit_apic_handler,s,log,False)


    log.debug("Login done")



    if options.show_sclass:
        show_sclass(options,list_of_sites)
        sys.exit(0)


    for site_obj in sorted(list_of_sites,key=lambda x: x.name):
        vrfs={}

        if options.list_tenants:
            print("="*30)
            print("SITE: %s"%(site_obj.name))
            print("="*30)
            socgenbase2.print_tenants(site_obj=site_obj)
            continue



        if options.list_vpcs:
            print("="*30)
            print("SITE: %s"%(site_obj.name))
            print("="*30)
            socgenbase2.print_vpcs(site_obj=site_obj,string=options.string)
            continue
        elif options.list_nodes:
            print("="*30)
            print("SITE: %s"%(site_obj.name))
            print("="*30)
            socgenbase2.print_nodes(site_obj=site_obj,role='leaf')
            continue

        tenant=site_obj.get_this_tenant(name=options.tenant)

        if options.vpc:
            vpcs=site_obj.get_vpcs_pg(string=options.vpc)
            if len(vpcs) > 1:
                print("Sorry: '%s' matches more than one VPC in site '%s': %s"%(options.vpc,site_obj.name,vpcs))
                continue
            elif not len(vpcs):
                print("Sorry: '%s' does not match any VPC in site '%s'"%(options.vpc,site_obj.name))
                continue

            vpc=vpcs[0]
        elif options.eth:
            try:
                node_sys=site_obj.get_this_node_sys(nodeid=options.node)
            except Exception as e:
                print("/!\\ Beware: cannot find node '%s': %s /!\\"%(options.node,e))
                sys.exit(1)
            eth_sys=site_obj.get_this_sys_interface(intf_name=options.eth,node_sys=node_sys)




        epg_list=[]
        print()
        print("="*30)
        if tenant.nameAlias:
            tenant_alias=' (%s)'%tenant.nameAlias
        else:
            tenant_alias=''
        print("SITE: %s [tenant: %s%s]"%(site_obj.name,tenant.name,tenant_alias))
        print("="*30)






        for epg_name in sorted(options.epg):
            try:
                epg_list.append(site_obj.get_this_epg(tenant=tenant,name=epg_name))
            except Exception as e:
                print("Error retrieving epg '%s': %s"%(epg_name,e))
        for sclass in options.sclass:
            try:
                epg_list.append(site_obj.get_this_epg(tenant=tenant,sclass=sclass))
            except Exception as e:
                print("Error retrieving epg '%s': %s"%(sclass,e))



        if options.show_faults:
            show_faults(site_obj=site_obj,epg_list=epg_list,tenant=tenant)
            continue


        for epg in epg_list:
            try:
                apn=site_obj.get_obj_by_dn(dn=epg.parentDn)
                apn_name=apn.name
            except Exception as e:
                apn_name='NOT FOUND'
            print('EPG: %s [APN: %s]'%(epg.name,apn_name))
            print('-'*30)
            if options.check:
                epg_check(epg,site_obj=site_obj,tenant=tenant,vrfs=vrfs)
            elif options.vpc:
                vpc_check(epg,site_obj=site_obj,tenant=tenant,vpc=vpc,vrfs=vrfs)
            elif options.eth:
                eth_check(epg,site_obj=site_obj,tenant=tenant,vrfs=vrfs,node_sys=node_sys,eth_sys=eth_sys)

            else:
                print("Missing and option",file=sys.stderr)
                sys.exit(1)

            print()

        print("="*30)






if __name__=='__main__':
    main()
