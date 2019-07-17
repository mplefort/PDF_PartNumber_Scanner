from cx_Freeze import setup, Executable
import sys

build_exe_options = {"packages": ["appJar", "pathlib", "schempnextract", "indentbomextract", "pncheckprocess",
								 "xlsxwriter", "pdf2txt", "pandas", "numpy"]}

base = None
if sys.platform == "win32":
	base = "Win32GUI"


setup(	name='PDF_PN_Extractor',
		version='0.1',
		description='Pull pn from PDF and Check',
		options= {"build_exe": build_exe_options},
		executables=[Executable("main.py", base=base)])

