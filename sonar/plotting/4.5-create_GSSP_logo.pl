#!/usr/bin/perl

=head 1 SUMMARY

 4.5-create_GSSP_logo.pl

 This script generates a logo plot of a mutability profile. Structure of the 
     EPS file is cribbed from WebLogo (weblogo.berkeley.edu/logo.cgi).

 Usage: 4.5-create_GSSP_logo.pl profile.txt [outHead]
 Invoke with -h or --help to print this documentation.

 Parameters:
     profile.txt - File with profiles
     outHead     - Where to save logo (in EPS format). Will append "_gene.eps"
                       (where gene is IGHV1-2 or the like). Default = profile

 Created by Chaim A. Schramm 2016-10-07.
 Edited and commented for publication by Chaim A Schramm on 2017-02-24.

 Copyright (c) 2011-2017 Columbia University and Vaccine Research Center, National
                          Institutes of Health, USA. All rights reserved.

=cut

use warnings;
use strict;
use diagnostics;
use Pod::Usage;
use FindBin;
use lib "$FindBin::Bin/../";
use PPvars qw(ppath);
use version qw/logCmdLine/;


if ($#ARGV<0 || $ARGV[0]=~/^-?-h/) { pod2usage(1); }
&logCmdLine($0,@ARGV);


my $inFile = $ARGV[0];
my $outHead = "profile";
if (-defined($ARGV[1])) { $outHead=$ARGV[1]; }

if (! -e $inFile) { die "Can't find input file $inFile!\n"; }


my %profiles;
my $maxY = 20;
open PROF, $inFile;
while (<PROF>) {
    next if /^Vgene/; #skip header
    chomp;
    my @arr = split;

    push @{$profiles{$arr[0]}}, [ map { 100 * $arr[4] * $_ } @arr[5..24] ];
	   
    while ( 100 * $arr[4] > $maxY ) { $maxY += 10; }
}
close PROF;


for my $gene (sort keys %profiles) {

    open EPS, ">$outHead\_$gene.eps";
    my $date = localtime;

    print EPS <<FIN;
%!PS-Adobe-3.0 EPSF-3.0
%%Title: Sequence Logo : Gene-specific substitution profile for $gene
%%Creator: Chaim A Schramm and Zizhang Sheng
%%CreationDate: $date
%%BoundingBox:   0  0  850  283
%%Pages: 0
%%DocumentFonts: 
%%EndComments: 

%850  283 
% ---- CONSTANTS ----
/cmfactor 72 2.54 div def % defines points -> cm conversion
/cm {cmfactor mul} bind def % defines centimeters


% ---- VARIABLES ----

/black [0 0 0] def
/red [0.8 0 0] def
/green [0 0.5 0] def
/blue [0 0 0.8] def
/yellow [0.9 0.9 0] def
/purple [0.8 0 0.8] def
/orange [1 0.7 0] def
/gray [0.8 0.8 0.8] def


/logoWidth 30 cm def
/logoHeight 10 cm def
/logoTitle (GSSP for $gene) def

/yaxis true def
/yaxisLabel (substitution frequency (%)) def
/yaxisBits  $maxY def % bits
/yaxisTicBits 10 def


/xaxis true def
/xaxisLabel (sequential position) def
/showEnds (-) def % d: DNA, p: PROTEIN, -: none

/showFineprint true def
/fineprint () def

/charsPerLine 100 def
/logoLines 1 def

/showingBox (n) def    \%n s f
/shrinking false def
/shrink  1 def
/outline false def

/IbeamFraction  1 def
/IbeamGray      0.50 def
/IbeamLineWidth 0.5 def

/fontsize       12 def
/titleFontsize  14 def
/smallFontsize   6 def

/defaultColor black def 

% Standard Amino Acid colors
/colorDict << 
  (G)  green  
  (S)  green  
  (T)  green  
  (Y)  green  
  (C)  green  
  (N)  purple 
  (Q)  purple 
  (K)  blue   
  (R)  blue   
  (H)  blue   
  (D)  red    
  (E)  red    
  (P)  black  
  (A)  black  
  (W)  black  
  (F)  black  
  (L)  black  
  (I)  black  
  (M)  black  
  (V)  black  
>> def



% ---- DERIVED PARAMETERS ----

/leftMargin
  fontsize 4 mul

def 

/bottomMargin
  fontsize 0.75 mul

  % Add extra room for axis
  xaxis {fontsize 2 mul add } if
  xaxisLabel () eq {} {fontsize 0.75 mul add} ifelse
def


/topMargin 
  logoTitle () eq { 10 }{titleFontsize 4 add} ifelse
def

/rightMargin 
  \%Add extra room if showing ends
  showEnds (-) eq { fontsize neg }{fontsize 1.5 mul} ifelse
def

/yaxisHeight 
  logoHeight 
  bottomMargin sub  
  topMargin sub
def

/ticWidth fontsize 2 div def

/pointsPerBit yaxisHeight yaxisBits div  def

/isBoxed 
  showingBox (s) eq
  showingBox (f) eq or { 
    true
  } {
    false
  } ifelse
def

/stackMargin 1 def

% Do not add space aroung characters if characters are boxed
/charRightMargin 
  isBoxed { 0.0 } {stackMargin} ifelse
def

/charTopMargin 
  isBoxed { 0.0 } {stackMargin} ifelse
def

/charWidth
  logoWidth
  leftMargin sub
  rightMargin sub
  charsPerLine div
  charRightMargin sub
def

/charWidth4 charWidth 4 div def
/charWidth2 charWidth 2 div def

/stackWidth 
  charWidth charRightMargin add
def
 
/numberFontsize 
  fontsize charWidth lt {fontsize}{charWidth} ifelse
def

% movements to place 5'/N and 3'/C symbols
/leftEndDeltaX  fontsize neg         def
/leftEndDeltaY  fontsize 1.5 mul neg def
/rightEndDeltaX fontsize 0.25 mul    def
/rightEndDeltaY leftEndDeltaY        def

% Outline width is proporional to charWidth, 
% but no less that 1 point
/outlinewidth 
  charWidth 32 div dup 1 gt  {}{pop 1} ifelse
def


% ---- PROCEDURES ----

/StartLogo { 
  % Save state
  save 
  gsave 

  % Print Logo Title, top center 
  gsave 
    SetTitleFont

    logoWidth 2 div
    logoTitle
    stringwidth pop 2 div sub
    logoHeight logoLines mul .95 mul
    titleFontsize sub
    moveto

    logoTitle
    show
  grestore

  % Print X-axis label, bottom center
  gsave
    SetStringFont

    logoWidth 2 div
    xaxisLabel stringwidth pop 2 div sub
    fontsize
    moveto

    xaxisLabel
    show
  grestore

  % Show Fine Print
  showFineprint {
    gsave
      SetSmallFont
      logoWidth
        fineprint stringwidth pop sub
        smallFontsize sub
          smallFontsize 3 div
      moveto
    
      fineprint show
    grestore
  } if

  % Move to lower left corner of last line, first stack
  leftMargin bottomMargin translate

  % Move above first line ready for StartLine 
  0 logoLines logoHeight mul translate

  SetLogoFont
} bind def

/EndLogo { 
  grestore 
  showpage 
  restore 
} bind def


/StartLine{ 
  % move down to the bottom of the line:
  0 logoHeight neg translate
  
  gsave 
    yaxis { MakeYaxis } if
    xaxis { ShowLeftEnd } if
} bind def

/EndLine{ 
    xaxis { ShowRightEnd } if
  grestore 
} bind def


/MakeYaxis {
  gsave    
    stackMargin neg 0 translate
    ShowYaxisBar
    ShowYaxisLabel
  grestore
} bind def


/ShowYaxisBar { 
  gsave  
    SetStringFont

    /str 10 string def % string to hold number  
    /smallgap stackMargin 2 div def

    % Draw first tic and bar
    gsave    
      ticWidth neg 0 moveto 
      ticWidth 0 rlineto 
      0 yaxisHeight rlineto
      stroke
    grestore

   
    % Draw the tics
    % initial increment limit proc for
    0 yaxisTicBits yaxisBits abs \%cvi
    {/loopnumber exch def

      % convert the number coming from the loop to a string
      % and find its width
      loopnumber 10 str cvrs
      /stringnumber exch def % string representing the number

      stringnumber stringwidth pop
      /numberwidth exch def % width of number to show

      /halfnumberheight
         stringnumber CharBoxHeight 2 div
      def

      numberwidth % move back width of number
      neg loopnumber pointsPerBit mul % shift on y axis
      halfnumberheight sub % down half the digit

      moveto % move back the width of the string

      ticWidth neg smallgap sub % Move back a bit more  
      0 rmoveto % move back the width of the tic  

      stringnumber show
      smallgap 0 rmoveto % Make a small gap  

      % now show the tic mark
      0 halfnumberheight rmoveto % shift up again
      ticWidth 0 rlineto
      stroke
    } for
  grestore
} bind def

/ShowYaxisLabel {
  gsave
    SetStringFont

    % How far we move left depends on the size of
    % the tic labels.
    /str 10 string def % string to hold number  
    yaxisBits yaxisTicBits div cvi yaxisTicBits mul 
    str cvs stringwidth pop
    ticWidth 2.5 mul  add neg  


    yaxisHeight
    yaxisLabel stringwidth pop
    sub 2 div

    translate
    90 rotate
    0 0 moveto
    yaxisLabel show
  grestore
} bind def


/StartStack {  % <stackNumber> startstack
  xaxis {MakeNumber}{pop} ifelse
  gsave
} bind def

/EndStack {
  grestore
  stackWidth 0 translate
} bind def


% Draw a character whose height is proportional to symbol bits
/MakeSymbol{ % charbits character MakeSymbol
  gsave
    /char exch def
    /bits exch def

    /bitsHeight 
       bits pointsPerBit mul 
    def

    /charHeight 
       bitsHeight charTopMargin sub
       dup 
       0.0 gt {}{pop 0.0} ifelse % if neg replace with zero 
    def 
 
    charHeight 0.0 gt {
      char SetColor
      charWidth charHeight char ShowChar

      showingBox (s) eq { % Unfilled box
        0 0 charWidth charHeight false ShowBox
      } if

      showingBox (f) eq { % Filled box
        0 0 charWidth charHeight true ShowBox
      } if

    } if

  grestore

  0 bitsHeight translate 
} bind def


/ShowChar { % <width> <height> <char> ShowChar
  gsave
    /tc exch def    % The character
    /ysize exch def % the y size of the character
    /xsize exch def % the x size of the character

    /xmulfactor 1 def 
    /ymulfactor 1 def

  
    % if ysize is negative, make everything upside down!
    ysize 0 lt {
      % put ysize normal in this orientation
      /ysize ysize abs def
      xsize ysize translate
      180 rotate
    } if

    shrinking {
      xsize 1 shrink sub 2 div mul
        ysize 1 shrink sub 2 div mul translate 

      shrink shrink scale
    } if

    % Calculate the font scaling factors
    % Loop twice to catch small correction due to first scaling
    2 {
      gsave
        xmulfactor ymulfactor scale
      
        ysize % desired size of character in points
        tc CharBoxHeight 
        dup 0.0 ne {
          div % factor by which to scale up the character
          /ymulfactor exch def
        } % end if
        {pop pop}
        ifelse

        xsize % desired size of character in points
        tc CharBoxWidth  
        dup 0.0 ne {
          div % factor by which to scale up the character
          /xmulfactor exch def
        } % end if
        {pop pop}
        ifelse
      grestore
    } repeat

    % Adjust horizontal position if the symbol is an I
    tc (I) eq {
      charWidth 2 div % half of requested character width
      tc CharBoxWidth 2 div % half of the actual character
      sub 0 translate
      % Avoid x scaling for I 
      /xmulfactor 1 def 
    } if


    % ---- Finally, draw the character
  
    newpath
    xmulfactor ymulfactor scale

    % Move lower left corner of character to start point
    tc CharBox pop pop % llx lly : Lower left corner
    exch neg exch neg
    moveto

    outline {  % outline characters:
      outlinewidth setlinewidth
      tc true charpath
      gsave 1 setgray fill grestore
      clip stroke
    } { % regular characters
      tc show
    } ifelse

  grestore
} bind def


/ShowBox { % x1 y1 x2 y2 filled ShowBox
  gsave
    /filled exch def 
    /y2 exch def
    /x2 exch def
    /y1 exch def
    /x1 exch def
    newpath
    x1 y1 moveto
    x2 y1 lineto
    x2 y2 lineto
    x1 y2 lineto
    closepath

    clip
    
    filled {
      fill
    }{ 
      0 setgray stroke   
    } ifelse

  grestore
} bind def


/MakeNumber { % number MakeNumber
  gsave
    SetNumberFont
    stackWidth 0 translate
    90 rotate % rotate so the number fits
    dup stringwidth pop % find the length of the number
    neg % prepare for move
    stackMargin sub % Move back a bit
    charWidth (0) CharBoxHeight % height of numbers
    sub 2 div %
    moveto % move back to provide space
    show
  grestore
} bind def


/Ibeam{ % heightInBits Ibeam
  gsave
    % Make an Ibeam of twice the given height in bits
    /height exch  pointsPerBit mul def 
    /heightDRAW height IbeamFraction mul def

    IbeamLineWidth setlinewidth
    IbeamGray setgray 

    charWidth2 height neg translate
    ShowIbar
    newpath
      0 0 moveto
      0 heightDRAW rlineto
    stroke
    newpath
      0 height moveto
      0 height rmoveto
      currentpoint translate
    ShowIbar
    newpath
    0 0 moveto
    0 heightDRAW neg rlineto
    currentpoint translate
    stroke
  grestore
} bind def


/ShowIbar { % make a horizontal bar
  gsave
    newpath
      charWidth4 neg 0 moveto
      charWidth4 0 lineto
    stroke
  grestore
} bind def


/ShowLeftEnd {
  gsave
    SetStringFont
    leftEndDeltaX leftEndDeltaY moveto
    showEnds (d) eq {(5) show ShowPrime} if
    showEnds (p) eq {(N) show} if
  grestore
} bind def


/ShowRightEnd { 
  gsave
    SetStringFont
    rightEndDeltaX rightEndDeltaY moveto
    showEnds (d) eq {(3) show ShowPrime} if
    showEnds (p) eq {(C) show} if
  grestore
} bind def


/ShowPrime {
  gsave
    SetPrimeFont
    (\242) show 
  grestore
} bind def

 
/SetColor{ % <char> SetColor
  dup colorDict exch known {
    colorDict exch get aload pop setrgbcolor
  } {
    pop
    defaultColor aload pop setrgbcolor
  } ifelse 
} bind def

% define fonts
/SetTitleFont {/Arial-Bold findfont titleFontsize scalefont setfont} bind def
/SetLogoFont  {/Arial-Bold findfont charWidth  scalefont setfont} bind def
/SetStringFont{/Arial-Bold findfont fontsize scalefont setfont} bind def
/SetPrimeFont {/Symbol findfont fontsize scalefont setfont} bind def
/SetSmallFont {/Arial findfont smallFontsize scalefont setfont} bind def

/SetNumberFont {
    /Helvetica-Bold findfont 
    numberFontsize
    scalefont
    setfont
} bind def

\%Take a single character and return the bounding box
/CharBox { % <char> CharBox <lx> <ly> <ux> <uy>
  gsave
    newpath
    0 0 moveto
    % take the character off the stack and use it here:
    true charpath 
    flattenpath 
    pathbbox % compute bounding box of 1 pt. char => lx ly ux uy
    % the path is here, but toss it away ...
  grestore
} bind def


% The height of a characters bounding box
/CharBoxHeight { % <char> CharBoxHeight <num>
  CharBox
  exch pop sub neg exch pop
} bind def


% The width of a characters bounding box
/CharBoxWidth { % <char> CharBoxHeight <num>
  CharBox
  pop exch pop sub neg 
} bind def


% Deprecated names
/startstack {StartStack} bind  def
/endstack {EndStack}     bind def
/makenumber {MakeNumber} bind def
/numchar { MakeSymbol }  bind def

%\%EndProlog

%\%Page: 1 1
StartLogo
StartLine % line number 1
FIN

    my @aas = ('A','C','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y');
    my $stackNum = 0;
    for my $stack (@{$profiles{$gene}}) {
	$stackNum++;
	print EPS "($stackNum) startstack\n";
	my @sorted = sort { $stack->[$a] <=> $stack->[$b] } (0..19);
	for my $num (@sorted) {
	    next if $stack->[$num] == 0;
	    print EPS " ($stackNum) $stack->[$num] ($aas[$num]) numchar\n";
	}
	print EPS "endstack\n";
    }

    print EPS "EndLine\nEndLogo\n\n%%EOF\n\n";

    close EPS;

} #next gene








