#!/usr/bin/env python

"""

checkForFrameshift.py

This script uses pairwise clustal alignments to the assigned germline to detect
      and discard possible frameshift errors (primarily expected in data from 454
      or other pyrosequencing techniques). Uses clustal despite it being slower 
      and less efficient because I was unable to optimize parameters for muscle.

Usage: checkForFrameshift.py in.fa out.fa [ db.fa ]

    Invoke with -h or --help to print this documentation.

    in.fa 	Fasta file containing sequences to be checked. V gene assignment
                     must be present in def line in standard format.
    out.fa 	Fasta file in which to save good sequences.
    db.fa 	Optional fasta file containing germline V gene sequences to align
                     to. Default is <SONAR>/germDB/IgHKLV_cysTruncated.fa.
                     Truncation of 3' end of V gene is recommended to avoid the
                     introduction of spurious gaps into the alignment due to SHM
                     in CDR3.

Created by Chaim Schramm on 2015-12-29.

Copyright (c) 2015-2016 Columbia University and Vaccine Research Center, National
                               Institutes of Health, USA. All rights reserved.

"""

import glob, os, re, sys
from Bio import SeqIO
from Bio.Align.Applications import ClustalwCommandline
from Bio import AlignIO
import numpy

try:
	from sonar.annotate import *
except ImportError:
	find_SONAR = sys.argv[0].split("sonar/utilities")
	sys.path.append(find_SONAR[0])
	from sonar.annotate import *


if len(sys.argv) < 3 :
	print __doc__
	sys.exit(0)

q = lambda x: x in sys.argv
if any([q(x) for x in ["h", "-h", "--h", "help", "-help", "--help"]]):
	print __doc__
	sys.exit(0)

#log command line
logCmdLine(sys.argv)


db = "%s/germDB/IgHKLV_cysTruncated.fa"%SCRIPT_FOLDER
if len(sys.argv) == 4: db = sys.argv[3]


all_letters = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
fa_head     = "".join(numpy.random.choice(all_letters,size=8))
germs       = dict()
for entry in SeqIO.parse(open(db, "rU"), "fasta"):
    germs[entry.id] = entry.seq


#load sequences and preprocess to align:
sequences   = []
total, good = 0, 0
reader      = SeqIO.parse(open(sys.argv[1], "rU"), "fasta")
for entry in reader:

    total += 1
    gene = re.search("V_gene=(IG[HKL]V[^,\s]+)",entry.description)

    if gene:

        germline = gene.groups()[0]

        if not germline in germs:
            print "%s might be misassigned; %s is not in my germline library. Skipping..." % (entry.id, germline)
            continue

        with open("%s.fa"%fa_head, "w") as handle:
            handle.write(">%s\n%s\n>%s\n%s\n" % ( germline, germs[germline], entry.id, entry.seq ))

        clustal_cline = ClustalwCommandline(infile="%s.fa"%fa_head)
        try:
            stdout, stderr = clustal_cline()
        except:
            print "Error in alignment of %s (will skip): %s" % (entry.id, stderr)
            for f in glob.glob("%s.*"%fa_head): os.remove(f)
            continue

        alignment = AlignIO.read("%s.aln"%fa_head, "clustal")

        shift = False

        for record in alignment:
            codons = re.sub( "---", "", str(record.seq.strip("-")) ) #don't care about leading/trailing and full-codon indels are fine
            if "-" in codons:
                shift = True #likely frameshift --discard!

        if not shift: #made it; save the sequence
            good += 1
            sequences.append(entry)

        for f in glob.glob("%s.*"%fa_head): os.remove(f)

SeqIO.write(sequences, sys.argv[2], "fasta")
print "Total: %d, Good: %d" % (total, good)
