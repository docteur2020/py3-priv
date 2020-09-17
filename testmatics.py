from random import randint
from asciimatics.screen import Screen
import time

def demo(screen,test):
	count=0
	A=ligneip('10.0.2.3','10.91.2.3','20')
	B=ligneip('10.0.3.3','10.91.2.3','20')
	while count <=1000:
		erase_ligne(screen,5,2000)
		erase_ligne(screen,10,2000)
		A.rtt=str(randint(0,20))
		B.rtt=str(randint(0,20))
		draw_ligne(screen,5,A)
		draw_ligne(screen,10,B)
		screen.refresh()
		count=count+1
		time.sleep(0.1)
		draw_ligne(screen,5,A)
		draw_ligne(screen,10,B)
		ev = screen.get_key()

		if ev in (ord('Q'), ord('q')):
			return


def draw_ligne(screen,posi_v,ligneip__):
	screen.print_at(ligneip__.proxy,
			0, posi_v,
			colour=Screen.COLOUR_BLUE,
			bg=Screen.COLOUR_YELLOW,attr=Screen.A_BOLD)
	screen.print_at( u"\u2588"*int(ligneip__.rtt),
			15, posi_v,
			colour=Screen.COLOUR_BLUE,
			bg=Screen.COLOUR_YELLOW,attr=Screen.A_BOLD)
			
def erase_ligne(screen,posi_v,max):
	screen.print_at(u"\u2588"*max,
			15, posi_v,
			colour=Screen.COLOUR_BLACK,
			bg=Screen.COLOUR_YELLOW,attr=Screen.A_BOLD)
			
class ligneip(object):
	def __init__(self,proxy,ip,rtt):
		self.proxy=proxy
		self.ip=ip
		self.rtt=rtt
		

print('toto')
time.sleep(3)		
Screen.wrapper(demo,arguments=[5])