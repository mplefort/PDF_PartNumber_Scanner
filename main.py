from appJar import gui
from pathlib import Path
import schempnextract
import indentbomextract
import pncheckprocess


'''
Goal:
Create a CSV of P/N Checked with hightlighting P/n and Quantity
Green: P/N and quantity match on schematics and indented bills
Yellow: more on BOM then schematic
Red: shortage - more on schematic than BOMs

Outline of code:

GUI:
	1. Window to drag and drop/add file location of:	
		a. Unit Bill.xlsx/csv
		b. FA bill.xlsx/csv
		c. Elec Schem.pdf
		d. Hyd Schem.pdf
	2. Output file location with save as box, defualt to desktop

schem_pn_extract.py
	1. extract P/N from PDF
		a. pdf2txt.py <input file> -o <outputfile> -V # -V detect Vertical text
	2. Create Dictionary and sum all P/N from PDF
	3. check notes for "x/d" for multiples and add to sum
	4. if "unit supplied" do not count
	5. if (pn) does not count

indentbomextract.py
	1. create pandas data frame from indented BOM


pn_check_process:
	1. From schem pn dictionary look up p/n and quantity
	2. Search through pandas indentedBOM for P/N
		a. Given P/N and Quantity start from top and find P/N
		b. If p/n found, check qty and BOM level
			- for BOM level > 0, find Kit P/N and *qty
			- repeat until end of pandas df
		c. sum pn to determine total qty
	3. open schem_xxxxxxxxx_PartCheck.csv
	4. for PN in BOM Dictionary, check if =, <, > Schem dictionary
	5. write to csv and hightlight green, yellow, or red.
	6. Save output

GUI: using http://pbpython.com/pdf-splitter-gui.html
create a GUI to load in SchemPN.csv, IndentedBOM.csv, outputFile.xlsx

'''

# GUI interface to place CSV file from draftmatic ouput and 
# an idented BOM

## Create schem Dictionary
# 1. extract P/N from csv
# 2. sum all P/N to same dictionary item
# 3. check notes for "x/d" for multiples
# 4. if "unit supplied" do not count



def process(elec_schem, hyd_schem, fa_bom, unit_bom, output_dir):
	'''
	process the schem pdfs and xlsx boms and creates a new part_check.xlsx file
	with highlighting of:
		Green: P/N and quantity match on schematics and indented bills
		Yellow: more on BOM then schematic
		Red: shortage - more on schematic than BOMs
	Args:
		elec_schem (string): path to PDF of electrical schematic
		hyd_schem (string) ; path to PDF of hydraulic schematic
		fa_bom (string)    : path to .xlsx of FA indented BOM (unformated)
		unit_bom (string)  : path to .xlsx of Unit indented BOM (unformated)

	return: None

	'''

	# elec schem pdf -> elec pn dict
	elecdict = schempnextract.pdf_extract(elec_schem)

	# hyd schem pdf -> hyd pn dict
	hyddict = schempnextract.pdf_extract(hyd_schem)

	# fa bom excel file -> fa df
	dftoplev = indentbomextract.load_bom(fa_bom)
	# unit bom excel file -> unit df
	dfunitlev = indentbomextract.load_bom(unit_bom)
	# combine pn dicts
	pndict = schempnextract.combine(elecdict, hyddict)
	# combine dfs
	dfbom = indentbomextract.combinedf(dftoplev, dfunitlev)

	print('done')
	# compare pn dicts to dfs and create outputfile
	pncheckprocess.check(dfbom, pndict, output_dir)

	return None


def validate_inputs(elec_schem, hyd_schem, fa_bom, unit_bom, output_dir):
	""" Verify that the input values provided by the user are valid

	Args:
		elec_schem (string): path to PDF of electrical schematic
		hyd_schem (string) ; path to PDF of hydraulic schematic
		fa_bom (string)    : path to .xlsx of FA indented BOM (unformated)
		unit_bom (string)  : path to .xlsx of Unit indented BOM (unformated)

	Returns:
		True if error and False otherwise
		List of error messages
	"""
	errors = False
	error_msgs = []

	# # Make sure a PDF is selected
	# if Path(input_file).suffix.upper() != ".PDF":
	# 	errors = True
	# 	error_msgs.append("Please select a PDF input file")

	# # Make sure a range is selected
	# if len(range) < 1:
	# 	errors = True
	# 	error_msgs.append("Please enter a valid page range")

	# # Check for a valid directory
	# if not(Path(output_dir)).exists():
	# 	errors = True
	# 	error_msgs.append("Please Select a valid output directory")

	# # Check for a file name
	# if len(file_name) < 1:
	# 	errors = True
	# 	error_msgs.append("Please enter a file name")

	return(errors, error_msgs)


def press(button):

	""" Process a button press

	Args:
	button: The name of the button. Either Process of Quit
	"""
	if button == "Process":
		elec_pdf_file = app.getEntry("electrical_pdf")
		hyd_pdf_file = app.getEntry("hydraulic_pdf")
		fa_bom_file = app.getEntry("fa_bom")
		unit_bom_file = app.getEntry("unit_bom")
		output_dir = app.getEntry("output_directory")
		errors, error_msg = validate_inputs(elec_pdf_file, hyd_pdf_file, fa_bom_file, unit_bom_file, output_dir)
		if errors:
			app.errorBox("Error", "\n".join(error_msg), parent=None)
		else:
			app.statusbar(text='Extracting PNs from PDFs')
			process(elec_pdf_file, hyd_pdf_file, fa_bom_file, unit_bom_file, output_dir)
			app.statusbar(text='Completed, check output at: %s' % output_dir)
	else:
		app.stop()

	if button == "Quit":
		app.stop()


if __name__ == '__main__':

	# Create the GUI Window
	app = gui("PDF Splitter", useTtk=True)
	app.setTtkTheme("default")
	app.setSize(500, 400)

	# Add the interactive components
	app.addLabel("Electrical Schem PDF")
	app.addFileEntry("electrical_pdf")

	app.addLabel("Hydraulic Schem PDF")
	app.addFileEntry("hydraulic_pdf")

	app.addLabel("FA Indented BOM")
	app.addFileEntry("fa_bom")

	app.addLabel("Unit Indented BOM")
	app.addFileEntry("unit_bom")

	app.addLabel("Select Output Directory")
	app.addDirectoryEntry("output_directory")

	# link the buttons to the function called press
	app.addButtons(["Process", "Quit"], press)

	app.statusbar(header='Status', fields=1, text='Input Fields and Click Process')

	# start the GUI
	app.go()

	# os.chdir('/home/matthewlefort/Documents/Projects/Python/PDF_PartNumberCheck/Data')
	# cwd = os.getcwd()
	# toplevelfile = os.path.join(cwd, 'topLevel.xlsx')
	# unitlevelfile = os.path.join(cwd, 'unitLevel.xlsx')
	# elecschem = os.path.join(cwd, '990653411-A.pdf')
	# hydschem = os.path.join(cwd, '990653414-A.pdf')
	# outdir = cwd

	# process(elecschem, hydschem, toplevelfile, unitlevelfile, outdir)
