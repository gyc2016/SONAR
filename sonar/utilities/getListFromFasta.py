#!/usr/bin/env python

"""
getListFromFasta.py

This is a simple utility script for getting a list of the sequence identifiers
      from a large fasta file.

Usage: getListFromFasta.py -f seqs.fa [ -o output.list ]

    Invoke with -h or --help to print this documentation.

    f           Fasta file containing the sequences.
    o           Text file in which to save the list of sequences.
                   Prints to STDOUT if omitted.

Created by Chaim A Schramm on 2015-04-27.
Added printing to STDOUT on 2016-06-10.
Copyright (c) 2011-2016 Columbia University and Vaccine Research Center, National
                         Institutes of Health, USA. All rights reserved.

"""

import sys
try:
	from sonar import *
except ImportError:
	find_SONAR = sys.argv[0].split("sonar/utilities")
	sys.path.append(find_SONAR[0])
	from sonar import *


def main():

    global inFile, outFile
    if outFile != "":
	    sys.stdout = open(outFile, "w")
    for seq in generate_read_fasta(inFile):
	    print "%s"%seq.id


if __name__ == '__main__':

	#check if I should print documentation
	q = lambda x: x in sys.argv
	if any([q(x) for x in ["h", "-h", "--h", "help", "-help", "--help"]]):
		print __doc__
		sys.exit(0)

	#log command line
	logCmdLine(sys.argv)

	# get parameters from input
	dict_args = processParas(sys.argv, f="inFile", o="outFile")
        try:
            inFile, outFile = getParasWithDefaults(dict_args, dict(outFile=""), "inFile", "outFile")
        except KeyError:
            print __doc__
            sys.exit(1)


	main()

