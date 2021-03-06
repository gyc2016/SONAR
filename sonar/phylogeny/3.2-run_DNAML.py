#!/usr/bin/env python

"""
3.2-runDNAML.py

This script calls DNAML to generate a maximum likelihood tree for a set
      of sequences, outgroup-rooted on the germline V gene sequence. For
      optimal results, sequences should be aligned manually (use the DNAML/
      PHYLIP format) and specified with the -i parameter. However, the
      script can also use MUSCLE to create an automated alignment to be
      passed directly to DNAML. For automatic alignments, please use the
      -v parameter to specify the assigned V gene, which will be added to
      the alignment and used for rooting the tree.


Usage: 3.2-runDNAML.py ( -i custom/input.phy | -v germline_V )
                       [ -locus <H|K|L> -lib path/to/library.fa -n native.fa ]
		       [ -f -h ]

    Invoke with -h or --help to print this documentation.

    Required parameters:
    i		Manual alignment (in PHYLIP format) of the sequences to be 
                   analayzed, with known antibody seqeunces and germline 
		   (or other outgroup) sequence included. This is the 
		   preferred option for running this program and should be
		   used especially for inferring ancestral sequences.
                   If -n and -v (see below) are supplied instead, sequences
                   will be taken from output/sequences/ROOT-collected.fa and
                   aligned automagically with MUSCLE.

        * OR *

    v		Assigned germline V gene of known antibodes, for use in 
                   rooting the trees.


    Optional parameters (compatible with both -v and -i):

    outtree     Where to save the output tree. Default: output/<project>.tree
    outfile     Where to save DNAML output (text tree and inferred ancestors)
                   Default: output/logs/<project>.dnaml.out


    Optional parameters (only relevant when using the -v option):

    seqs        A fasta file containing the sequences from which the tree is
                   to be built. Default:
		   output/sequences/nucleotide/<project>-collected.fa
    locus	H (default): use V heavy / K: use V kappa / L: use V lambda
                   Ignored if the -lib option is used to supply a custom
                   library
    lib		Optional custom germline library (eg Rhesus or Mouse).
    n		Fasta file containing the known sequences.


    Optional flags:

    f		Force a restart of the analysis, even if there are files from
                   a previous run in the working directory.

Created by Chaim A Schramm 2015-07-09.
Added options for flexibility and more informative error messages by CAS 2016-08-19.

Copyright (c) 2011-2016 Columbia University Vaccine Research Center, National
                         Institutes of Health, USA. All rights reserved.

"""

import sys
from Bio import AlignIO
from Bio.Align.Applications import MuscleCommandline

try:
	from sonar.phylogeny import *
except ImportError:
	find_SONAR = sys.argv[0].split("sonar/phylogeny")
	sys.path.append(find_SONAR[0])
	from sonar.phylogeny import *



def revertName(match):
    return lookup[ int(match.group(0)) - 1 ] #ids are 1-indexed, list is 0-indexed

def main():

    global inFile, lookup, workDir, outTreeFile, outFile, seqFile

    oldFiles = glob.glob("%s/infile"%workDir) + glob.glob("%s/outtree"%workDir) + glob.glob("%s/outfile"%workDir)
    if len(oldFiles) > 0:
        if force:
            for f in oldFiles:
                os.remove(f)
        else:
            sys.exit("Old files exist! Please use the -f flag to force overwrite.")
        

    if doAlign:

        #first create a working file to align and add the germline and natives
        shutil.copyfile(seqFile, "%s/%s_to_align.fa"%(workDir, prj_name))
        handle = open( "%s/%s_to_align.fa"%(workDir, prj_name), "a" )
        handle.write( ">%s\n%s\n" % (germ_seq.id, germ_seq.seq) )
        for n in natives.values():
            handle.write( ">%s\n%s\n" % (n.id, n.seq) )
        handle.close()

        #now run muscle
        run_muscle            = MuscleCommandline( input="%s/%s_to_align.fa" % (workDir, prj_name), out="%s/%s_aligned.afa" % (prj_tree.phylo, prj_name) )
        run_muscle.maxiters   = 2
        run_muscle.diags      = True
        run_muscle.gapopen    = -5000.0 #code requires a float
        print run_muscle
        run_muscle()

        inFile = "%s/%s_aligned.afa" % (workDir, prj_name)


    #open the alignment to rename everything and find germline sequence
    #rename is to avoid possible errors with DNAML from sequence ids that are too long
    germ_pos = 1
    with open(inFile, "rU") as handle:
        if doAlign:
            aln = AlignIO.read(handle, "fasta")
        else: 
            try:
                aln = AlignIO.read(handle, "phylip-relaxed")
            except:
                sys.exit("Please make sure custom input is aligned and in PHYLIP format...")

    lookup = []
    for seq in aln:
        lookup.append( seq.id )
        if re.search("(IG|VH|VK|VL|HV|KV|LV)", seq.id) is not None:
            germ_pos = len( lookup )
        seq.id = "%010d" % len( lookup )


    with open("%s/infile" % workDir, "w") as output:
        AlignIO.write(aln, output, "phylip")


    #now generate script for DNAML
    # J is "jumble" followed by random seed and number of times to repeat
    # O is outgroup root, followed by position of the germline in the alignment
    # 5 tells DNAML to do the ancestor inference
    # Y starts the run
    with open("%s/dnaml.in"%workDir, "w") as handle:
        seed = random.randint(0,1e10) * 2 + 1 #seed must be odd
        handle.write("J\n%d\n5\nG\nO\n%d\n5\nY\n" % (seed, germ_pos))


    # change to work directory so DNAML finds "infile" and puts the output where we expect
    origWD = os.getcwd()
    os.chdir(workDir)
    with open("dnaml.in", "rU") as pipe:
        subprocess.call([dnaml], stdin=pipe)
    os.chdir(origWD)

    #revert names in tree
    with open("%s/outtree"%workDir, "rU") as intree:
        mytree = intree.read()
    fixedtree = re.sub("\d{10}", revertName, mytree)
    with open(outTreeFile, "w") as outtree:
        outtree.write(fixedtree)

    #revert names in out file
    with open("%s/outfile"%workDir, "rU") as instuff:
        mystuff = instuff.read()
    fixedstuff = re.sub("\d{10}", revertName, mystuff)
    with open(outFile, "w") as outstuff:
        outstuff.write(fixedstuff)
        
	
    print "\nOutput in %s and %s\n" % (outTreeFile, outFile)


if __name__ == '__main__':

	#check if I should print documentation
	q = lambda x: x in sys.argv
	if any([q(x) for x in ["h", "-h", "--h", "help", "-help", "--help"]]):
		print __doc__
		sys.exit(0)

	#log command line
	logCmdLine(sys.argv)


	#check forcing parameter
	force = False
	flag = [x for x in ["f", "-f", "--f", "force", "-force", "--force"] if q(x)]
	if len(flag)>0:
		sys.argv.remove(flag[0])
		force = True


	prj_tree 	= ProjectFolders(os.getcwd())
	prj_name 	= fullpath2last_folder(prj_tree.home)


	#get the parameters from the command line
	dict_args = processParas(sys.argv, n="natFile", v="germlineV", locus="locus", lib="library", i="inFile", seqs="seqFile", outtree="outTreeFile", outfile="outFile")
	defaults = dict(locus="H", library="", inFile=None, seqFile=None, outTreeFile=None, outFile=None)
	natFile, germlineV, locus, library, inFile, seqFile, outTreeFile, outFile = getParasWithDefaults(dict_args, defaults, "natFile", "germlineV", "locus", "library", "inFile", "seqFile", "outTreeFile", "outFile")

        doAlign = True
	if germlineV is None:
            if inFile is None:
                print __doc__
		sys.exit("You must specify either -i or -v")
            else:
                doAlign = False
        else:
            if inFile is not None:
                print __doc__
                sys.exit("Options -i and -v are mutually exclusive")
            else:
                #load native sequences
		natives = dict()
		if natFile is not None:
			natives = load_fastas(natFile)
		else: 
			print "No native sequences specified; tree will only include NGS sequences."

                #load germline sequence
                if not os.path.isfile(library):
                    if locus in dict_vgerm_db.keys():
			library = dict_vgerm_db[locus]
                    else:
			sys.exit("Can't find custom V gene library file!")

                germ_dict = load_fastas(library)
                try:
                    germ_seq = germ_dict[germlineV]
                except:
                    sys.exit( "Specified germline gene (%s) is not present in the %s library!\n" % (germlineV, library) )
		
	workDir = prj_tree.phylo
	if not os.path.isdir(workDir):
		print "No work directory found, temporary files will be placed in current directory."
		workDir = "."

	if outTreeFile is None:
		if os.path.isdir(prj_tree.out):
			outTreeFile = "%s/%s.tree" % (prj_tree.out, prj_name)
		else:
			outTreeFile = "%s.tree" % prj_name

	if outFile is None:
		if os.path.isdir(prj_tree.logs):
			outFile = "%s/%s.dnaml.out"%(prj_tree.logs,prj_name)
		else:
			outFile = "%s.dnaml.out" % prj_name

	if doAlign and seqFile is None:
		seqFile = "%s/%s-collected.fa" %( prj_tree.nt, prj_name)
		if not os.path.isfile(seqFile):
			sys.exit( "Can't find sequence file %s to build tree from." % seqFile )

	main()

