class chiffre(object):
	def __init__(self,numero):
		self.numero=numero
	
	def __str__(self):
		return self.numero.__str__()
		
if __name__ == '__main__':
	"Fonction principale"
	A=[]
	A.append(chiffre(1))
	A.append(chiffre(2))
	A.append(chiffre(3))
	A.append(chiffre(4))
	A.append(chiffre(5))
	for element in A:
		print(element)
		
	B=chiffre(3)
	A.remove(A[3])
	
	for element in A:
		print(element)
		
	print(A.index(B).__str__())
		