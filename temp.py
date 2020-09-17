Space=pp.White(ws=' ')
Hostname=pp.LineStart()+(pp.Keyword('hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.LineEnd().suppress()
dc2_b1_str = open('CONFIG/PE/SHRUN/dc2-b1_20170622_15h12m39s.log', 'r').read()
Hostname.scanString(dc2_b1_str)
head_interface=pp.LineStart()+(pp.Keyword('interface').suppress()+Space.suppress()+pp.Word(pp.alphanums+'/.')+pp.LineEnd().suppress()).setResultsName('interface')
Description=((Space+pp.Keyword('description') ).suppress()+pp.Combine( pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space)) +pp.LineEnd().suppress())).setResultsName('description')
Vrf=((Space+pp.Optional(pp.Literal('ip'))+ pp.Literal('vrf forwarding')).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]{}<>*')+pp.LineEnd().suppress()).setResultsName('vrf')
Address=((Space+ pp.Literal('ip address')).suppress()+pp.Combine(ipAddress+Space+Mask)+pp.LineEnd().suppress()).setResultsName('ip')
OtherLine=pp.Combine((Space+pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space))+pp.LineEnd())).suppress()
SectionInterface=head_interface+pp.Optional(pp.SkipTo(Description).suppress()+Description)+pp.Optional(pp.SkipTo(Vrf).suppress()+Vrf)+pp.Optional(pp.SkipTo(Address).suppress()+Address)+pp.OneOrMore(OtherLine)
SectionInterfaces=pp.OneOrMore(SectionInterface)




SectionInterface.parseString(test2)
SectionInterfaces.parseString(test)


Space=pp.OneOrMore(pp.White(ws=' '))
Hostname=pp.LineStart()+(pp.Keyword('hostname')+Space).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.LineEnd().suppress()
octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
LigneNonParagraphe=pp.LineStart()+pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')
ipAddress=pp.Combine(octet + ('.'+octet)*3)
Mask=pp.Combine(octet + ('.'+octet)*3)
head_interface=(pp.LineStart()+pp.Keyword('interface').suppress()+Space.suppress()+pp.Word(pp.alphanums+'/.')+pp.LineEnd().suppress()).setResultsName('interface')
Description=((Space+pp.Keyword('description') ).suppress()+pp.Combine( pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space)) +pp.LineEnd().suppress())).setResultsName('description')
Vrf=((Space+pp.Optional(pp.Literal('ip'))+ pp.Literal('vrf forwarding')).suppress()+pp.Word(pp.alphanums+'()/\:;,-_[]{}<>*')+pp.LineEnd().suppress()).setResultsName('vrf')
Address=((Space+ pp.Literal('ip address')).suppress()+pp.Combine(ipAddress+Space+Mask)+pp.LineEnd().suppress()).setResultsName('ip')
OtherLine=pp.Combine((pp.LineStart()+Space+pp.OneOrMore(pp.Word(pp.alphanums+'()/\:;,-_[]|{}<>*')+pp.Optional(Space))+pp.LineEnd())).suppress()
SectionInterface=head_interface+pp.Optional(pp.SkipTo(Description,failOn=LigneNonParagraphe).suppress()+Description)+pp.Optional(pp.SkipTo(Vrf,failOn=LigneNonParagraphe).suppress()+Vrf)+pp.Optional(pp.SkipTo(Address,failOn=LigneNonParagraphe).suppress()+Address)+pp.ZeroOrMore(OtherLine)


resultat=SectionInterface.scanString(dc2_b1_str)
next(resultat)[0]



resultat=SectionInterface.scanString(dc2_b1_str)
next(resultat)[0]