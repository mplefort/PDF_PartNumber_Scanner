import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


# indentbomextract.py
# 	1. create pandas data frame from indented BOM
#   2. CLean BOM for only relevent info for pncheckprocess


def load_bom(file):
	'''
		load_bom: use .xlsx input file and extract columns: Level, Item, Description, Type, Description, Type, Op Seq
		remove all white spaces are non numeric characters from "Item"

		Input:
			file (str): File path to bom to load
		Output:
			dfbom (pandasdf): 
		return

	'''


	dfbom = pd.read_excel(file,index_col=None, na_values=['NA'])

	# Clean BOM 
	# gets colums, Level, Item, Description, Type, Description, Type, Op Seq
	dfbom = dfbom.iloc[:, [0, 1, 2, 4, 8, 14]]

	# iterator over rows to remove reference p/ns with part types: ATO model, ATO Option Class, Reference item
	row = 0
	irrevtype = ['ATO model', 'ATO Option Class'] #, 'Reference item']
	dfcopy = dfbom.copy()
	
	for item in dfcopy['Item']:
		# string "    - 990100100  " -> "990100100"
		item = item.replace('-', '')
		item = item.strip()
		dfbom.at[row,'Item'] = item

		#  remove irrelevant pns of type:
		#  'Configured Item, ATO model, ATO Option Class, Reference Item'
		if dfcopy.at[row, 'Type'] in irrevtype:
			# print(dfbom.at[row,'Type'])
			# print(dfbom.tail())
			dfbom = dfbom.drop(dfcopy.index[row])
			

		row += 1

	# Reset index column as changed from removing rows (drop())
	dfbom.reset_index(inplace=True)

	# writer = pd.ExcelWriter('BomReduced.xlsx')
	# dfbom.to_excel(writer,'Sheet1')
	# writer.save()

	return dfbom


def combinedf(dftoplev, dfunitlev):
	'''
		Appends data frames of same number of columns with dfunitlev on bottom.
		
	
		input:
			dftoplev (pandas df) : toplevel  bom with index and columns ('Level', 'Item', 'Description', 'Type', 'Op Seq', 'Quantity')
			dfunitlev (pandas df): unitlevel bom with index and columns ('Level', 'Item', 'Description', 'Type', 'Op Seq', 'Quantity')

	'''

	frames = [dftoplev, dfunitlev]
	result = pd.concat(frames)

	result.reset_index(inplace=True)
	writer = pd.ExcelWriter('BomCombined.xlsx')
	result.to_excel(writer,'Sheet1')
	writer.save()

	return result


if __name__ == '__main__':

	os.chdir('/home/matthewlefort/Documents/Projects/Python/PDF_PartNumberCheck/Data')
	cwd = os.getcwd()
	unitfile = os.path.join(cwd,'unitLevel.xlsx')
	topfile = os.path.join(cwd, 'topLevel.xlsx')

	unitbom = load_bom(unitfile)
	topbom = load_bom(topfile)

	combinebom = combinedf(topbom, unitbom)

