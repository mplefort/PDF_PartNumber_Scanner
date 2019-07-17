import os
import indentbomextract
import xlsxwriter
import schempnextract

'''
indentbomextract.py
	1. create pandas data frame from indented BOM


pn_check_process:
	
'''

def check(bomdf, schempn, outputdir):
	'''
		Compares each P/N in schempn to bomdf and marks up outputfile .xlsx:
			Green: P/N and quantity match on schematics and indented bills
			Yellow: more on BOM then schematic
			Orange: shortage - more on schematic than BOMs
			Red: Neg driving
		Checks if any op seq on BOM is <0 qty, otherwise sums all pns in diff op seq.

		outputfile:
		p/n, schem qty, BOM total qty, Note (if op: x qty < 0), Hightlight

		input:
			bomdf: (pandas df): indented BOM
			schempn (dict): {p/n: qty} on schematics
			outputfile (str): path to output file to write .xlsx sheet of colorcoding
								
	'''

	# Create excel sheet in output file location
	os.chdir(outputdir)
	workbook = xlsxwriter.Workbook('Schem_BOM_Checked.xlsx')
	worksheet = workbook.add_worksheet()
	
	# Create Titles - format column widths
	worksheet.write(0, 0, 'Part Num')
	worksheet.set_column(0, 0, 18.0)

	worksheet.write(0, 1, 'Schem Qty')
	worksheet.set_column(1, 1, 10.0)

	worksheet.write(0, 2, 'BOMs Qty')
	worksheet.set_column(2, 2, 10.0)

	worksheet.write(0, 3, 'Note')
	worksheet.set_column(3, 3, 48.0)

	worksheet.set_column(4,4, 24.0)

	# highlight spreadsheet:
	red_format = workbook.add_format()
	red_format.set_pattern(1)
	red_format.set_bg_color('red')

	org_format = workbook.add_format()
	org_format.set_pattern(1)
	org_format.set_bg_color('orange')

	yel_format = workbook.add_format()
	yel_format.set_pattern(1)
	yel_format.set_bg_color('yellow')

	grn_format = workbook.add_format()
	grn_format.set_pattern(1)
	grn_format.set_bg_color('green')

	pur_format = workbook.add_format()
	pur_format.set_pattern(1)
	pur_format.set_bg_color('purple')


	# Make Key
	worksheet.write(0, 4, 'red - Neg qty on BOM', red_format)
	worksheet.write(1, 4, 'Org - Schem Qty > BOM Qty', org_format)
	worksheet.write(2, 4, 'Yel - Schem Qty < BOM Qty', yel_format)
	worksheet.write(3, 4, 'Grn - Schem Qty = BOM Qty', grn_format)
	worksheet.write(4, 4, 'Pur - No Idea what happened', pur_format)

	
	# Apply process to : 
	row = 1
	for key, value in schempn.items():
		# get dict{op: qty} total p/n in each op seq from bomdf
		bompn = pn_indented_bom_lookup(key, bomdf)
		# print(str(key) + ': ' + str(value) + ' || ', end='')
		# print(bompn, end='')

		# Sum bom qty from each op sequence
		bomqty = 0
		if bompn:
			for op, bomvalue in bompn.items():
				bomqty += bomvalue
		else:
			bomqty = 0

		# print to excel the following:
		# schem pn, qty on schem, for each op seq in bomdf (op, qty)
		worksheet.write(row, 0, key)
		worksheet.write(row, 1, value)
		# print(value)
		worksheet.write(row, 2, bomqty)

		# if bompn(value) < 0: red
		if bomqty == 0:
			worksheet.write(row, 0, key, red_format)
		# elif: sum bomdf dict(qty) < schem pn qty -> orange
		elif bomqty < schempn[key]:
			worksheet.write(row, 0, key, org_format)

		# elif: sum bomdf dict(qty) > schem pn qty -> yellow
		elif bomqty > schempn[key]:
			worksheet.write(row, 0, key, yel_format)
		# elif: sum bomdf dict(qty) == schem pn qty -> green
		elif bomqty == schempn[key]:
			worksheet.write(row, 0, key, grn_format)
		# else: purple (idk what happened)
		else:
			worksheet.write(row, 0, key, pur_format)
		# if any bomdf dict {op, qty} < 0, -Red
		for op, qty in bompn.items():
			if qty < 0:
				worksheet.write(row, 0, key, red_format)

		row += 1


	workbook.close()
	

def pn_indented_bom_lookup(partnum, bomdf):

	'''
		input:
			partnum (string): partnumber to look up
			bomdf (pands df):  bom with index and columns ('Level', 'Item', 'Description', 'Type', 'Op Seq', 'Quantity')
		
		output:
			dict{op: qty}
	'''


	currentrow = 0
	qty = {}
	#  process sum all p/n with same op seq
	for item in bomdf['Item']:
		upsearchqty = {}  #### Making a list of dictionarys
		if str(item) == str(partnum):
			# print(item + ' == ' + partnum)
			
			upsearchqty[int(bomdf.at[currentrow,'Op Seq'])] = float(bomdf.at[currentrow, 'Quantity'])
			# print('Upsearch Qty: ' + str(upsearchqty))

			nextlev = int(bomdf.at[currentrow, 'Level']) - 1
			# print('nextLev: ' + str(nextlev))

			# if BOM level > 1: search up BOM level 
			upsearchrow = currentrow - 1
			while nextlev > 0:
				# print('upsearchrow: ' + str(upsearchrow) + ' | Level: ' + str(df.at[upsearchrow,'Level']))
				# print('upsearchrow: ' + str(upsearchrow) + ' | nextLev: ' + str(nextlev))

				if nextlev == int(bomdf.at[upsearchrow, 'Level']):
					upsearchqty[bomdf.at[currentrow,'Op Seq']] = upsearchqty[bomdf.at[currentrow,'Op Seq']] * int(bomdf.at[upsearchrow,'Quantity'])
					nextlev = int(bomdf.at[upsearchrow, 'Level']) - 1
					# print('Found next level P/N: ' + str(bomdf.at[upsearchrow, 'Item']) + ' | Bom Level: ' + str(bomdf.at[upsearchrow, 'Level']) + ' | nextlev: ' + str(nextlev) )

				upsearchrow -= 1

	# print qty(op: qty) to screem from bom
	# Need Op Seq check
		for op, value in upsearchqty.items():
			if op in qty:
				qty[op] = qty[op] + upsearchqty[op]
			else:
				qty[op] = upsearchqty[op]

		currentrow += 1

	return qty


if __name__ == "__main__":

	os.chdir('/home/matthewlefort/Documents/Projects/Python/PDF_PartNumberCheck/Data')
	cwd = os.getcwd()
	outputdir = cwd

	elecfile = os.path.join(cwd,'990653411-A.pdf')
	hydfile = os.path.join(cwd, '990653414-A.pdf ')

	elec_pn = schempnextract.pdf_extract(elecfile)
	hyd_pn = schempnextract.pdf_extract(hydfile)
	schem_pns = schempnextract.combine(elec_pn, hyd_pn)


	unitfile = os.path.join(cwd,'unitLevel.xlsx')
	topfile = os.path.join(cwd, 'topLevel.xlsx')

	topleveldf = indentbomextract.load_bom(topfile)
	unitleveldf = indentbomextract.load_bom(unitfile)
	bomdf = indentbomextract.combinedf(topleveldf, unitleveldf)

	# Test this for various p/n confirm accurate findings in p/n qtys to op seqs
	# pntest = pn_indented_bom_lookup('070420353', topleveldf)

	check(bomdf, schem_pns, outputdir)

