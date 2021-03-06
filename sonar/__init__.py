#!/usr/bin/env python


"""
Core functions for the "ZAP" package,

Created by Zhenhai Zhang on 2011-04-05 as mytools.py
Edited and commented for publication by Chaim A Schramm on 2015-02-10.

Copyright (c) 2011-2016 Columbia University and Vaccine Research Center, National
                         Institutes of Health, USA. All rights reserved.
"""

from Bio import SeqIO
from Bio import Seq
from Bio import AlignIO
from Bio.SeqRecord import SeqRecord
from Bio.Align.Applications import ClustalwCommandline
from math import log

import glob
import re
import subprocess
import atexit


from numpy import mean, array, zeros, ones, nan, std, isnan

from commonVars import *


########## COMMAND LOGGING ############
global printLog
printLog = False #this tells us whether or not to print log info on exit (skip if program was called with -h)


#overload default error handling so we can log whether it was a successful exit or not
# code taken from: https://stackoverflow.com/a/9741784
class ExitHooks(object):
    def __init__(self):
        self.exit_code = None
        self.exception = None

    def hook(self):
        self._orig_exit = sys.exit
        sys.exit = self.exit
        self._orig_except = sys.excepthook
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        self.exit_code = str(code)
        self._orig_exit(code)

    def exc_handler(self, exc_type, exc, tb):
        self.exception = exc_type.__name__ + ": " + str(exc)
        self._orig_except(exc_type, exc, tb)

hooks = ExitHooks()
hooks.hook()


def logCmdLine( command ):
    
    global printLog

    if os.path.isdir( "%s/output/logs" % os.getcwd() ):

        for idx,arg in enumerate(command):
            if re.search("\s", arg):
                command[idx] = '"'+arg+'"'

        p = subprocess.Popen(['git', '-C', os.path.dirname(command[0]), 
                              'describe', '--always','--dirty','--tags'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        VERSION = p.communicate()[0].strip()
        
        with open("%s/output/logs/command_history.log"%os.getcwd(), "a") as handle:
            handle.write( "\n%s -- SONAR %s run with command:\n\t%s\n" % (time.strftime("%c"), VERSION, " ".join(command)) )
            
        printLog = True

    else:
        print "SONAR log directory not found; command line and output will not be saved"

    
def logExit():

    global printLog
    if printLog:
        with open("%s/output/logs/command_history.log" % os.getcwd(), "a") as handle:
            if hooks.exit_code is not None:
                formatted = re.sub( "\n", "\n\t", hooks.exit_code.strip(" \t\r\n") ) #remove white space and new lines on both ends; indent if multiple lines
                handle.write( "%s -- Program exited with error:\n\t%s\n" % (time.strftime("%c"),formatted) )
            elif hooks.exception is not None:
                formatted = re.sub( "\n", "\n\t", hooks.exception.strip(" \t\r\n") ) #remove white space and new lines on both ends; indent if multiple lines
                handle.write( "%s -- Exception:\n\t%s\n" % (time.strftime("%c"),formatted) )
            else:
                handle.write( "%s -- Program finished successfully\n" % time.strftime("%c") )
                
atexit.register(logExit)




#
# -- BEGIN -- class definition
#

class MyNode:
	def __init__(self, parent):
		self.parent 	= parent
		self.children 	= []
	def add_child(self, child):
		self.children.append(child)


class MySeq:
	def __init__(self, seq_id, seq):
		self.seq_id 	= seq_id					# sequence ID
		try:
			self.seq 	= str(seq)			# sequence in string format
		except:
			self.seq	= seq	
		self.seq_len 	= len(self.seq)				# sequence length
		
		
	
	def set_desc(self, desc):
		self.desc = desc
		
class MyQual:
	def __init__(self, qual_id, qual_list):
		self.qual_id 	= qual_id
		self.qual_list 	= qual_list
		self.qual_len	= len(qual_list)
		
class MyAlignment:
	def __init__(self, row):
		self.qid	= row[0].strip()		# query id
		self.sid	= row[1].strip()		# subject id
		self.identity 	= float(row[2])			# % identity
		self.alignment 	= int(row[3])			# alignment length
		self.mismatches = int(row[4]) 			# mismatches
		self.gaps	= int(row[5])			# gap openings
		self.qstart 	= int(row[6])			# query start
		self.qend	= int(row[7])			# query end
		self.sstart 	= int(row[8])			# subject start
		self.send	= int(row[9]) 			# subject end
		self.evalue 	= float(row[10])		# e-value
		self.score	= float(row[11])		# bit score
		self.strand	= str(row[12])			# strand
		
		self.qlen	= 0
		self.slen	= 0
		
		self.real_id	= 0.0				# recaluclated identity
		self.divergence	= 0.0				# recalculated diversity
		
	def set_strand(self, s):
		self.strand = s					# setting strand
		
	def set_real_identity(self, identity):
		self.real_id = identity
		
	def set_diversity(self, divergence):
		self.divergence = divergence
		
class MyAlignmentVerbose:
	def __init__(self, row):
		self.query_id		= row[0]
		self.sbjct_id		= row[1]
		self.strand		= row[2]
		self.evalue		= float(row[3])
		self.score		= float(row[4])
		self.identities		= int(row[5])
		self.gaps		= int(row[6])
		self.aln_len		= int(row[7])
		self.query_start	= int(row[8])
		self.query_end		= int(row[9])
		self.query_len		= int(row[10])
		self.sbjct_start	= int(row[11])
		self.sbjct_end		= int(row[12])
		self.sbjct_len		= int(row[13])
		self.aln_query		= row[14]
		self.aln_sbjct		= row[15]
	
		
class ProjectFolders:
	"""folder structure of a project """
	
	def __init__(self, proj_home):

		self.home       = proj_home
		self.work       = "%s/work"        %  proj_home
		self.out        = "%s/output"      %  proj_home

		#working folders
		self.annotate   = "%s/annotate"    %  self.work
		self.lineage    = "%s/lineage"     %  self.work
		self.phylo      = "%s/phylo"       %  self.work
		self.internal   = "%s/internal"    %  self.work

		#second-level
		self.vgene      = "%s/vgene"       %  self.annotate
		self.jgene      = "%s/jgene"       %  self.annotate
		self.last       = "%s/last_round"  %  self.lineage
		self.beast      = "%s/beast"       %  self.phylo

		#output
		self.seq        = "%s/sequences"   %  self.out
		self.tables     = "%s/tables"      %  self.out
		self.plots      = "%s/plots"       %  self.out
		self.logs       = "%s/logs"        %  self.out
		self.rates      = "%s/rates"       %  self.out
		
		#second-level
		self.aa         = "%s/amino_acid"  %  self.seq
		self.nt         = "%s/nucleotide"  %  self.seq


#
# -- END -- class defination
#



#
# -- BEGIN -- argument process functions
#

def processParas(para_list, **keywords):
	""" 
	process the parameter information, all parameter start with "-paraname"
	return a dictionary (paraName, paraValue)
	remove the first parameter which is the program name
	"""
	
	para_list 		= para_list[1 :]
	kwgs, values 	= para_list[ :: 2], para_list[1 :: 2]

	if len(kwgs) != len(values):
		print "number of keywords and values does not equal"
		sys.exit(0)
	
	kwgs 	= map(lambda x : keywords[x[1 :]], kwgs)
	values 	= map(evalValues, values)

	#check for multiple uses of the same keyword and convert those values into a list
	for k in set(kwgs):
		if kwgs.count(k) > 1:
			idx     = [ i for i,x in enumerate(kwgs) if x==k ]
			valList = [ values[i] for i in idx ]
			values[idx.pop(0)] = valList #pop removes first occurence from idx list so we can only eliminate later occurences in next 2 lines
			kwgs    = [ x for i,x in enumerate(kwgs)   if i not in idx ]
			values  = [ x for i,x in enumerate(values) if i not in idx ]
			

	return dict(zip(kwgs,values))
	


def evalValues(v):
	"""Evaluate strings and return a value corresponding to its real type (int, float, list, tuple) """
	
	try:	return eval(v)
	except:	return v



def getParas(my_dict, *args):
	"""return the value of the argument """	
	
	if len(args) == 1:	return my_dict[args[0]]
	else:	return (my_dict.get(arg) for arg in args)
		
		
def getParasWithDefaults(my_dict, default_dict, *args):
	"""return the value of the argument or the default value if it wasn't specified on the command line"""	
	
	if len(args) == 1:	return my_dict.get(args[0],default_dict.get(args[0]))
	else:	return (my_dict.get(arg,default_dict.get(arg)) for arg in args)
		
		
#		
# -- END -- argument process functions
#


#
# -- BEGIN --  folder and file methods
#

def fullpath2last_folder(s):
	"""get immediate parent folder"""
	
	return s[s.rindex("/") + 1 :]


def create_folders(folder, force=False):

	old_wd = os.getcwd()
	os.chdir(folder)

	if (os.path.isdir("work")):
		if not force:
			sys.exit("Working directory already exists. Please use the -f(orce) option to re-intiate an analysis from scratch.\n")
		else:
			try:
				shutil.rmtree("work")
			except:
				sys.exit("Cannot remove old working directory, please delete manually and restart.\n")
			
	if (os.path.isdir("output")):
		if not force:
			sys.exit("Output directory already exists. Please use the -f(orce) option to re-intiate an analysis from scratch.\n")
		else:
			try:
				shutil.rmtree("output")
			except:
				sys.exit("Cannot remove old output directory, please delete manually and restart.\n")
			

	os.mkdir("work")
	os.mkdir("output")

		
	# Create working folders
	for subfolder in ALL_FOLDERS:
		try:
			os.mkdir(subfolder)
			
		except:		# may need to delete old folders
			print "FOLDER EXISTS: %s"%subfolder
			
	
	os.chdir(old_wd)
	return ProjectFolders(folder)



def get_files_format(folder, format = ""):
	"""return all files in specified folder with particular format; if format is not specified, return all files"""

	files = os.listdir(folder)
	
	if len(format) > 0:
		files = [x for x in files if x.endswith(format)]
	
	return sorted(files)




def get_files_format_fullpath(folder, format = ""):
	"""return all files in specified folder with particular format; if format is not specified, return all files"""

	files = os.listdir(folder)
	
	if len(format) > 0:
		files = [x for x in files if x.endswith(format)]
	
	files = ["%s/%s" %(folder, x) for x in files]
	
	return sorted(files)


def parse_name(s):
	"""retrieve file name from full path """
	
	return s[s.rindex("/") + 1 : s.rindex(".")]

#
# -- END -- folder and file methods 
#


#
# -- BEGIN -- qual file methods
#

def generate_phred_scores(f):
	"""parse quality file and generate phred scores one read a time"""
	
	handle = open(f, "rU")
	old_id, old_quals = get_454_fasta_id(handle.next()), []

	for line in handle:
		if line.startswith(">"):					# start of a new entry
			new_id = get_454_fasta_id(line)

			yield MyQual(old_id, old_quals)
			old_id, old_quals = new_id, []
			
		else:		# quality score lines	
			line 		= line[ : -1].strip().split(" ")	# remove "\n", remove " " at both ends, split by " "
			line 		= [x for x in line if x != ""]
			old_quals 	+= map(int, line)
			
	yield MyQual(old_id, old_quals)
	

def generate_quals_folder(folder):
	qual_files = glob.glob("%s/*.qual" %folder)
	for qual_file in qual_files:
		for myqual in generate_phred_scores(qual_file):
			yield myqual
	


def load_quals(f):
	"""reutrn sequence ID and quality scores in dicitonary format"""

	result = dict()
	
	for seq_id, quals, seq_len in generate_phred_scores(f):
		result[seq_id] = quals
		
	return result
		

#
# -- END -- qual file methods
#


#
# -- BEGIN -- FASTA file and sequence methods
#

def has_pat(s, pat):
	has, start, end = False, -1, -1
	matches = re.finditer(pat, s)
	for match in matches:
		has, start, end = True, match.start(), match.end()
	return has, start, end
	

def write_seq2file(myseq1, myseq2, f):
	""" write two MySseq objects to given file"""
	try:
		handle = open(f, "w")
		handle.write(">%s\n" %myseq1.seq_id)
		handle.write("%s\n\n" %myseq1.seq)
	
		handle.write(">%s\n" %myseq2.seq_id)
		handle.write("%s\n\n" %myseq2.seq)
		handle.close()
	except:
		print type(myseq1)
		print type(myseq2)



def load_seqs_in_dict(f, ids):
	"""
	load all sequences in file f is their id is in ids (list or set or dictionary)
	"""
	result = dict()
	for entry in SeqIO.parse(open(f, "rU"), "fasta"):
		if entry.id in ids:
			result[entry.id] = entry
			
	return result
	

def load_fastas_in_list(f, l):
	
	print "loading reads from %s as in given list..." %f
	reader, result, good = SeqIO.parse(open(f, "rU"), "fasta"), dict(), 0

	for entry in reader:
		if entry.id in l:

			#changed to match load from set CAS 20121004
			result[entry.id] = entry
			good += 1
			if good == len(l): break

			#myseq = MySeq(entry.id, entry.seq)
			#myseq.desc = entry.description
			#result[entry.id] = myseq

	print "%d loaded...." %len(result)
	return result
	

def load_fastas_with_Vgene(f, v):
	print "loading reads from %s assigned to %s..." %(f,v)
	reader, dict_reads = SeqIO.parse(open(f, "rU"), "fasta"), dict()
	for entry in reader:
		if re.search(v, entry.description):
			dict_reads[entry.id] = entry

	print "%d loaded..." %len(dict_reads)
	return dict_reads

	
def load_fastas(f):
	"""return gene ID and sequences in a dictionary"""
	print "loading sequence info from %s..." %f

	reader, result = SeqIO.parse(open(f, "rU"), "fasta"), dict()

	for entry in reader:
		#myseq = MySeq(entry.id, entry.seq)
		#myseq.desc = entry.description
		result[entry.id] = entry
	
	return result


def generate_read_fasta(f):
	"""read fasta file and yield one reads per time """
	
	reader = SeqIO.parse(open(f, "rU"), "fasta")
	for entry in reader:
		yield entry


def generate_read_fasta_folder(fastas, type=1):

	for fasta_file in fastas:

		filetype = "fasta"
		if re.search("\.(fq|fastq)$", fasta_file) is not None:
			filetype = "fastq"

		for entry in SeqIO.parse(open(fasta_file, "rU"), filetype):

			yield MySeq(entry.id, entry.seq), None, fasta_file

			#if we reimplement qual handling uncomment next section
			#if filetype == "fastq":
			#	yield MySeq(entry.id, entry.seq, desc), MyQual(entry.id, entry.letter_annotations["phred_quality"]), fasta_file	
			
	
	
def check_fasta_qual_pair(fa_name, qu_name):
	return fa_name[ : fa_name.rindex(".")] == qu_name[ : qu_name.rindex(".")]


def translate_a_sequence(s):
	"""translate nucleotide to protein"""  # this method is redundant, but we wannt deal with "N"
	s = s.upper()
	if s.find("N") > 0:
		return None
	codons = ["".join(x) for x in zip(s[ :: 3], s[1 :: 3], s[2 :: 3])]

	return "".join([dict_codon2aa[x][0] for x in codons])
	
#
# -- END -- FASTA file and sequence methods 
#


