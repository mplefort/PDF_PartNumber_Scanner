import re, pprint
from pathlib import os
import pdf2txt

import logging
logging.basicConfig(level=logging.CRITICAL, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

SCHEMATIC_PN = []

DO_NOT_COUNT = ['059650057', '059650058', '059650059', '059650050', '059500007', '970111983', '990316230', '123456789']


# To call pdf2text using pdfMiner
# pdf2txt.py <input file> -o <outputfile> -V # -V detect Vertical text
# python3.5 pdf2txt.py 990569773_K.pdf -o 990569773_K_ascii.txt -V


def load_file(inputFileName):
	'''
	loads a .txt file and returns string
	
	input:
		inputFileName (string): file name local directory of text file
	'''
	absworkingdir = os.path.abspath('./Data/')
	txtfn = os.path.join(absworkingdir, inputFileName)

	txtfile = open(txtfn)
	txt = txtfile.read()

	return txt


def is_ascii(txt):
	'''
	Check if txt (string) contains normal text or ascii text (cid:/d)
	
	input:
		txt (string): string containing either (cid:/d) or normal text

	return:
		isascii (Bool): True if ascii in txt

	'''
	isascii = True

	asciiLineSearchregex = re.compile(r'((\(cid:\d*\))+)')
	groups = asciiLineSearchregex.findall(txt)

	if groups:
		isascii = True
	else:
		isascii = False

	return isascii

def ascii_conversion(asciis):
	'''
		Converts a string of asciis (cid:78) to characters
		
	Input:	
		asciis (sting): ascii string of type (cid:78)(cid:23)
	
	Return:
		chars (string): character string of letters
		
	'''

	# matches entire lines of (cid:/d*)(cid:/d*)...
	asciiLineSearchregex = re.compile(r'((\(cid:\d*\))+)')
	# Matches ascii value \d* to convert to char
	asciiValuesRegex = re.compile(r'(cid:(\d*))')

	asciiRun = []
	for groups in asciiLineSearchregex.findall(asciis):
		asciiRun.append(groups[0])

	charRun = []
	charString = ''
	for elem in asciiRun:
		for groups in asciiValuesRegex.findall(elem):
			charString = charString + chr(int(groups[1]))
		charRun.append(charString)
		# textFile.write(charString + '\n')
		charString = ''

	# textFile.close()

	return charRun


# Output file

def pn_extractor(stringList, schempath):
	'''
	Search P/Ns: extract standard p/n and quantity multipliers. Matches p/n of with:
		XXX-XXXXX
		XXXXXXXXX
		
		* use TXT as font to avoid PDFminer finding
		* use NOTE as font to have PDFminer find text
		* if x# add multiple to dictionary
		* ignore if p/n in ()

	input:
		stringList ([string]): list [] of strings with p/n to extract
		schempath (string): string to file path of schem, used to extract shcem pn only oncce

	return:
		pndict (dictionary): dictionary of {PartNumber: qty}

	'''
	# Dict for pn: quantity
	pndict = {}
	# P/N Regex search through list of PDF text
	pnRegex = re.compile(r'''(\d{3}-\d{5}|\d{4}-\d{5}|\d{9})\s*x*(\d*)''', re.IGNORECASE)

	# Record schematic pns from file names
	schematic_pn = pnRegex.findall(schempath)
	SCHEMATIC_PN.append(schematic_pn[0][0])
	# print(SCHEMATIC_PN)
	
	# Filter P/N from list of PDF text
	for line in stringList:
		logging.debug(line)
		groups = pnRegex.findall(line)
		logging.debug(groups)

		# if no standard pn in list, move to next line of text
		if not groups:
			continue

		# create copy of make pn -> XXXXXXXXX p/n
		pnGroupCopy = groups[0][0]
		pnGroup = pnGroupCopy.replace("-","")
		pnGroup = '0' * (9 - int(len(pnGroup))) + pnGroup
		logging.debug(pnGroup)

		# if p/n in dict - add quantity of found p/n
		if pnGroup in pndict:
			if groups[0][1] == '':
				pndict[pnGroup] += 1
			else:
				pndict[pnGroup] += int(groups[0][1])
		# else p/n not in dict, create new key and add quantity
		else:
			if groups[0][1] == '':
				pndict[pnGroup] = 1
			else:
				pndict[pnGroup] = int(groups[0][1])

		logging.debug(pnGroup + ': ' + str(pndict[pnGroup]))

	# print(pndict)
	
	# save  to a text file
	# with open(outputFileName, 'w') as file:
	# 	for pn, quantity in pndict.items():
	# 		file.write(pn + ': ' + str(quantity))
	# 		file.write('\n')

	return pndict



def pdf_extract(schempdf):
	'''
		Call pdf2txt and convert pdf to text file with parameters detect vertical on and output ascii file

		input:
			schempdf (string): path file to pdf

		return:
			schempn (dict): {pn: qty} 

		'''

	pdftxt = (os.path.splitext(schempdf)[0] + '_ascii.txt')
	if os.path.isfile(pdftxt):
		print('pdf_extract: already converted: ' + pdftxt)
	else:
		pdf2txt.extract_text(files=[schempdf], outfile=(pdftxt), detect_vertical=True)


	# load converted file
	schemtxt = load_file(pdftxt)
	# print(schemtxt)


	# if file contains ascii text:
	if is_ascii(schemtxt):
		# Call ascii_conversion()
		schemtxt = ascii_conversion(schemtxt)

		##  Debug: check for outcome of pdf2txt output
		# text_file = open("output.txt","w")
		# schempnstr = ' '.join(schemtxt)
		# text_file.write(schempnstr)
		# text_file.close()
		# print(schemtxt)
		# Call pn_extractor()
		schem_pns = pn_extractor(schemtxt, schempdf)

	# else normal text
	else:
		schem_pns = pn_extractor(schemtxt)

	# print(schem_pns)



	return schem_pns


def combine(elecdict, hyddict):
	'''
	Takes two dictionaries and combines them. Duplicate p/ns between the schematics are summed


	input:
		elecdict (dict): {str*(pn): float(qty)} dictionary of pn: qty from the electrical schematic, summed parts without duplicates
		hyddict (dict):  {str*(pn): float(qty)} dictionary of pn: qty from the hydraulic  schematic, summed parts without duplicates

	'''


	schem_pns = {}

	for pn in elecdict:
		if pn in schem_pns:
			schem_pns[pn] += schem_pns[pn] + elecdict[pn]
		else:
			schem_pns[pn] = elecdict[pn]

	for pn in hyddict:
		if pn in schem_pns:
			schem_pns[pn] += schem_pns[pn] + hyddict[pn]
		else:
			schem_pns[pn] = hyddict[pn]

	# print(schem_pns)
	special_cases(schem_pns)

	return schem_pns


def special_cases(schempn):
	'''
		Removes special cases from schempn dictionry:
			remove all items from do_not_count.txt
			remove extra count of schem p/ns

	input:
		schempn (dict): pns found in schem dictionaries {pn: qty}
	file
	'''

	# load excel "do not count file" input into list
	# os.chdir('/home/matthewlefort/Documents/Projects/Python/PDF_PartNumberCheck')
	# cwd = os.getcwd()
	# donotcountfile = os.path.join(cwd,'do_not_count.xlsx')
	# donotcountdf = pd.read_excel(donotcountfile)

	# donotcountpn = donotcountdf['PartNumber'].values.tolist()

	i = 0
	for badpn in DO_NOT_COUNT:
		badpn = '0' *  (9 - len(str(badpn))) + str(badpn)
		DO_NOT_COUNT[i] = badpn
		i += 1
			
	# if schem p/n in donotcount list, del
	for badpn in DO_NOT_COUNT:
		if badpn in schempn:
			del schempn[badpn]


	# If SCHEMATIC_PN = qty 1, make sure only 1 of actual schematic pulled from pdfs
	for pn in SCHEMATIC_PN:
		if pn in schempn:
			schempn[pn] = 1

	# print(schempn)

	# # Debug check if pns removed from do_not_count,xlsx
	# text_file = open("output.txt","w")
	# for key in schempn:
	# 	text_file.write(key)
	# 	text_file.write(':  ')
	# 	text_file.write(str(schempn[key]))
	# 	text_file.write('\n')
	# text_file.close()

	## Include one copy of schem partnumber






if __name__ == '__main__':

# python3.5 pdf2txt.py 990569773_K.pdf -o 990569773_K_ascii.txt -V

	os.chdir('/home/matthewlefort/Documents/Projects/Python/PDF_PartNumberCheck/Data')
	cwd = os.getcwd()
	elecfile = os.path.join(cwd,'990653411-A.pdf')
	hydfile = os.path.join(cwd, '990653414-A.pdf ')

	elec_pn = pdf_extract(elecfile)
	hyd_pn = pdf_extract(hydfile)
	schem_pns = combine(elec_pn, hyd_pn)
