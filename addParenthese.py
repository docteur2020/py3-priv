masks={
	3:[
	'(1*1)+1',
	'1*(1+1)'
	],
	4:['(1*1)+1-1',
	'1*(1+1)-1',
	'1*1+(1-1)',
	'(1*1+1)-1',
	'1*(1+1-1)',
	'(1*1+1)-1',
	'(1*1)+(1-1)'
	],
	5:[
	'(1+1)+1*1-1',
	'1+(1+1)*1-1',
	'1+1+(1*1)-1',
	'1+1+1*(1-1)',
	'(1+1+1)*1-1',
	'1+(1+1*1)-1',
	'1+1+(1*1-1)',
	'1+(1+1*1-1)',
	'(1+1+1*1)-1',
	'(1+1)+(1*1)-1',
	'(1+1)+1*(1-1)',
	'1+(1+1)*(1-1)',
	'(1+1+1)*(1-1)',
	'(1+1)+(1*1-1)',
	]
}

def countNumber(operation):
	return sum(c.isdigit() for c in operation)

def addParenthese(operation):
	result=[]
	if isinstance(operation,str):
		operation_cur=[c for c in operation]
	else:
		operation_cur=operation
	nb_nb=countNumber(operation_cur)
	if nb_nb==2 or nb_nb>5:
		return operation
	for mask in masks[nb_nb]:
		indice=0
		temp_operation=operation_cur.copy()
		for c in mask:
			if c=='(' or c==')':
				temp_operation.insert(indice,c)
			indice+=1
		if isinstance(operation,str):
			result.append("".join(temp_operation))
		else:
			result.append(temp_operation)
		
	return result
	
print(addParenthese(['3','+','9','+','9','+','8']))
print(addParenthese('3+6*6/2-1'))

for op in addParenthese('3/6*6-2-1'):
	print(op,'=',eval(op))