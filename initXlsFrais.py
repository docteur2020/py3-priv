# -*- coding: utf-8 -*-
"""
Created on Thu May  2 11:01:37 2019

@author: abdallah
"""



from datetime import date , timedelta
import calendar
import xlsxwriter
import re
import pdb
from jours_feries_france  import JoursFeries



class dateFr(object):
    def __init__(self):
        self.semaine=[None,"Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
        self.mois=[None,"Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
            
            
def datetimeIterator(from_date=None, to_date=None, delta=timedelta(days=1)):
    from_date = from_date or datetime.now()
    while to_date is None or from_date <= to_date:
        yield from_date
        from_date = from_date + delta
    return

def getLastDayMonth(Month,Year):
    return calendar.monthrange(Year,Month)[1]
    
def initMonthYear(year,month):
    resultat=[]
    firstDay=date(year,month,1)
    lastDay=date(year,month,getLastDayMonth(month,year))
    monthDayIter=datetimeIterator(from_date=firstDay,to_date=lastDay)
    for day__ in monthDayIter:
        resultat.append({"date":day__.strftime("%d/%m/%Y"),"day":day__.strftime("%A")})
        
    return resultat
    
class FraisXls(object):
    def __init__(self,mois_debut,annee_debut,mois_fin,annee_fin,societe="BESTECH",nom="BERNIS"):
        self.firstdate=date(annee_debut,mois_debut,1)
        self.lastdate=date(annee_fin,mois_fin,1)
        self.datefr=dateFr()
        self.months=self.getMonth()
        self.years=self.getYear(annee_debut,annee_fin)
        self.init_jour_ferie()
        self.societe=societe
        self.nom=nom
        self.namefile=str(annee_fin)+" "+societe+" V0.1.xlsx"
        print(self.months)
        self.excel=xlsxwriter.Workbook(self.namefile)
        self.bold = self.excel.add_format({'bold': True})
        self.bold_underline = self.excel.add_format({'bold': True,'underline':True})
        self.header=['Date','Déplacement (client ou motif)','Lieu','Nombre km','Parking' ,'Péages HT','Resto HT','Autres','Libellé','TVA']
        self.default_day1=['Date','I-SUPPLIER','Bussy-Saint-Georges',46,'' ,'',0,'','Panier repas','']
        self.default_day2=['Date','I-SUPPLIER','Bussy-Saint-Georges',46,'' ,'',0,'','Panier repas','']
        self.default_we=['Date','','','','','','','','','']
        self.trailer1=['Sous-total','','','=SUM(D8:D43)','=SUM(E8:E43)','=SUM(F8:F43)','=SUM(G8:G43)','=SUM(H8:H43)','','=SUM(J8:J43)']
        self.trailer2=['Barême','','',0.303]
        self.trailer3=['Total en euros','','','=+D45*D46+98.5','=E45','=F45','=G45','=H45',0,'=J45']
        self.trailer4=['Total frais mois annee','','','=SUM(D47:J47)']
        self.widths= [15,25,20,12,10,10,10,10,10,10]
        self.cell_format_header=self.excel.add_format()
        self.cell_format_header.set_pattern(1)
        self.cell_format_header.set_bg_color('yellow')
        self.cell_format_default=self.excel.add_format()
        self.cell_format_we=self.excel.add_format()
        self.cell_format_we.set_bg_color('gray')
        self.initXlsWorksheet()
        
    def getMonth(self):
        resultat=[]
        monthIter=datetimeIterator(from_date=self.firstdate,to_date=self.lastdate,delta=timedelta(days=31))
        for month__ in monthIter:
            resultat.append((self.datefr.mois[month__.month],month__.year))
            
        return resultat
        
    def getYear(self,year1,year2):
        return [ y for y in range(year1,year2+1)]
    
    def init_jour_ferie(self):
        
        self.joursferies=[]
        for  year__ in self.years:
            jf_cur=JoursFeries.for_year(year__)
            self.joursferies+=list(jf_cur.values())
            
    def isJourFerie(self,day):
        return day in self.joursferies
        
    def setWsWidth(self,ws):
        column=0
        for width__ in self.widths:
            ws.set_column(column, column,width__)
            column+=1            
            
    def getContentDay(self,date__,day__):
        resultat=[]
        date_element=date__.split("/")
        
        date__datetime=date(int(date_element[2]),int(date_element[1]),int(date_element[0]))
        
        
        if not self.isJourFerie(date__datetime):
            if day__ in ['Monday','Wednesday','Friday']:
                resultat=[self.default_day1,self.cell_format_default]
            elif day__ in ['Tuesday','Thursday']:
                resultat=[ self.default_day2,self.cell_format_default ]
            elif day__ in ['Saturday','Sunday']:
                resultat=[ self.default_we,self.cell_format_we]
            
            if resultat:
                resultat[0][0]=date__
            else:
                print("Jour non pris en compte:"+day__)
        else:
            resultat=[ self.default_we,self.cell_format_we]
            resultat[0][0]=date__
        
        return resultat
        
    def writeBodyWs(self,ws,mois,annee):
        ws.write('A1','NOM:')
        ws.write('B1',self.nom)
        ws.write(1,0,'FICHE DE FRAIS',self.bold_underline)
        ws.write(2,0,'MOIS:')
        ws.write(2,1,mois.lower()+"-"+annee[2:4])
        
    def writeContentWs(self,ws,mois,annee):
        liste_date__=initMonthYear(int(annee),self.datefr.mois.index(mois))
        self.index_line=7
    
        for date__ in liste_date__:
            content_cur=self.getContentDay(date__['date'],date__['day'])
            self.writeLine(ws,content_cur[0],self.index_line,content_cur[1])
            self.index_line+=1
            
    def writeTrailerWs(self,ws,mois,annee):
        self.index_line=44
        self.writeLine(ws,self.trailer1,self.index_line,self.cell_format_default)
        self.index_line+=1
        self.writeLine(ws,self.trailer2,self.index_line,self.cell_format_default)
        self.index_line+=1
        self.writeLine(ws,self.trailer3,self.index_line,self.cell_format_default)
        self.index_line+=3
        cur_trailer4=self.trailer4
        cur_trailer4[0]='Total frais '+mois+' '+annee
        self.writeLine(ws,cur_trailer4,self.index_line,self.cell_format_default)
        self.index_line+=1
        
    def initXlsWorksheet(self):
        
        self.worksheet={}
        for month__ in self.months:
            
            nom_ws_cur=month__[0]+"_"+str(month__[1])
            self.worksheet[nom_ws_cur]=self.excel.add_worksheet(month__[0]+"_"+str(month__[1]))
            self.setWsWidth(self.worksheet[nom_ws_cur])
            self.writeBodyWs(self.worksheet[nom_ws_cur],month__[0],str(month__[1]))
            "Ecriture de l'entête"
            self.writeLine(self.worksheet[nom_ws_cur],self.header,6,self.cell_format_header)
            self.writeContentWs(self.worksheet[nom_ws_cur],month__[0],str(month__[1]))
            self.writeTrailerWs(self.worksheet[nom_ws_cur],month__[0],str(month__[1]))
            
    def writeLine(self,ws,liste_str,line,style):
        index=0
        for element in liste_str:
            if re.search('^=',str(element)):
                ws.write_formula(line,index,element,style)
            else:
                 ws.write(line,index,element,style)
            index+=1
            
    def close(self):
        self.excel.close()
        

        
        
test=FraisXls(4,2021,4,2022)
test.close()
