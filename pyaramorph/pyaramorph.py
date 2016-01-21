#!/usr/bin/python
# -*- coding: utf-8 -*-
# =====================================================================
# PyAraMorph, an Arabic morphological analyzer
# Copyright © 2005 Alexander Lee
# An arabic morphological analyzer.
# Ported to Python from Tim Buckwalter's AraMorph.pl.
# =====================================================================
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# =====================================================================

import sys
import readline
import re
import buck

# Data file paths
TABLE_AB = "tableAB"
TABLE_BC = "tableBC"
TABLE_AC = "tableAC"

class Analyzer:

    def __init__(self, out=sys.stdout, err=sys.stderr):
        self.out = out
        self.err = err
        self.seen = {}

        self.tableAB = self.LoadTable(TABLE_AB)
        self.tableBC = self.LoadTable(TABLE_BC)
        self.tableAC = self.LoadTable(TABLE_AC)

        self.prefixes = self.LoadDict("dictPrefixes")
        self.stems = self.LoadDict("dictStems")
        self.suffixes = self.LoadDict("dictSuffixes")

    def Process(self, str):
        """ Extract Arabic words from the given text and analyze them
        """
        if str == '\n': return
        tokens = self.Tokenize(str)
        for token in tokens:
            word = self.GetLookup(token)
            self.out.write("analysis for: %s %s\n" % (token, word))
            self.Analyze(word)

    def Analyze(self, word):
        """ Find possible solutions for the given word """
        results = []
        count = 0
        segments = self.Segment(word)

        for (prefix, stem, suffix) in segments:
            if self.prefixes.has_key(prefix) \
                    and self.stems.has_key(stem) \
                    and self.suffixes.has_key(suffix):
                solutions = self.CheckSegment(prefix, stem, suffix)
                if len(solutions) > 0:
                    results += solutions

        if len(results) > 0:
            for sol in results:
                self.out.write(sol)
                self.out.write('\n')

    def CheckSegment(self, prefix, stem, suffix):
        """ See if the prefix, stem, and suffix are compatible """
        solutions = []

        # Loop through the possible prefix entries
        for pre_entry in self.prefixes[prefix]:
            (voc_a, cat_a, gloss_a, pos_a) = pre_entry[1:5]

            # Loop through the possible stem entries
            for stem_entry in self.stems[stem]:
                (voc_b, cat_b, gloss_b, pos_b, lemmaID) = stem_entry[1:]

                # Check the prefix + stem pair
                pairAB = "%s %s" % (cat_a, cat_b)
                if not self.tableAB.has_key(pairAB): continue

                # Loop through the possible suffix entries
                for suf_entry in self.suffixes[suffix]:
                    (voc_c, cat_c, gloss_c, pos_c) = suf_entry[1:5]

                    # Check the prefix + suffix pair
                    pairAC = "%s %s" % (cat_a, cat_c)
                    if not self.tableAC.has_key(pairAC): continue

                    # Check the stem + suffix pair
                    pairBC = "%s %s" % (cat_b, cat_c)
                    if not self.tableBC.has_key(pairBC): continue

                    # Ok, it passed!
                    buckvoc = "%s%s%s" % (voc_a, voc_b, voc_c)
                    univoc = buck.buck2uni(buckvoc)
                    if gloss_a == '': gloss_a = '___'
                    if gloss_c == '': gloss_c = '___'
                    solutions.append(
                            "  solution: (%s %s) [%s]\n       pos: %s%s%s\n     gloss: %s + %s + %s\n" % \
                            (univoc, buckvoc, lemmaID, \
                            pos_a, pos_b, pos_c, \
                            gloss_a, gloss_b, gloss_c))

        return solutions

    def Tokenize(self, str):
        """ Extract all Arabic words from input and ignore everything
        else """
        tokens = re.split(u'[^\u0621-\u0652\u0670-\u0671]+', str)
            # include all strictly Arabic consonants and diacritics --
            # perhaps include other letters at a later time.
        return tokens

    def GetLookup(self, token):
        """ Remove diacritics and convert to transliteration """
        token = re.sub(u'ـ', '', token) # remove any تَطوِيل
        token = re.sub(u'[\u064b-\u0652\u0670]', '', token)
            # remove any vowels/diacritics
            # FIXME do something about \u0671, ALIF WASLA ?
        return buck.uni2buck(token)

    def Segment(self, word):
        """ Create possible segmentations of the given word """
        segments = []
        prelen = 0
        suflen = 0
        strlen = len(word)

        while prelen <= 4:
            # This loop increases the prefix length until > 4
            prefix = word[0:prelen]
            stemlen = strlen - prelen
            suflen = 0

            while stemlen >= 1 and suflen <= 6:
                # This loop increases suffix length until > 6,
                # or until stem length < 1
                stem = word[ prelen : (prelen+stemlen) ]
                suffix = word[ (prelen+stemlen) : ]
                segments.append( (prefix, stem, suffix) )
                
                stemlen -= 1
                suflen += 1

            prelen += 1

        return segments

    def LoadDict(self, file):
        """ Load the given dictionary file """
        dict = {}
        lemmas = 0
        entries = 0
        lemmaID = ""

        p_AZ = re.compile('^[A-Z]')
        p_iy = re.compile('iy~$')

        infile = open(file, 'r')
        self.out.write("loading %s ... " % (file))

        for line in infile:
            if line.startswith(';; '): # a new lemma
                m = re.search('^;; (.*)$', line)
                lemmaID = m.group(1)
                if self.seen.has_key(lemmaID):
                    self.err.write(
                        "lemmaID %s in %s isn't unique!\n" % (lemmaID, file))
                    sys.exit(1)
                else:
                    self.seen[lemmaID] = 1;
                    lemmas += 1;

            elif line.startswith(';'): # a comment
                continue

            else: # an entry
                line = line.strip(' \n')
                (entry, voc, cat, glossPOS) = re.split('\t', line)

                m = re.search('<pos>(.+?)</pos>', glossPOS)
                if m:
                    POS = m.group(1)
                    gloss = glossPOS
                else:
                    gloss = glossPOS
                    #voc = "%s (%s)" % (buck.buck2uni(voc), voc)
                    if cat.startswith('Pref-0') or cat.startswith('Suff-0'):
                        POS = "" # null prefix or suffix
                    elif cat.startswith('F'):
                        POS = "%s/FUNC_WORD" % voc
                    elif cat.startswith('IV'):
                        POS = "%s/VERB_IMPERFECT" % voc
                    elif cat.startswith('PV'):
                        POS = "%s/VERB_PERFECT" % voc
                    elif cat.startswith('CV'):
                        POS = "%s/VERB_IMPERATIVE" % voc
                    elif cat.startswith('N') and p_AZ.search(gloss):
                        POS = "%s/NOUN_PROP" % voc # educated guess
                                # (99% correct)
                    elif cat.startswith('N') and p_iy.search(voc):
                        POS = "%s/NOUN" % voc # (was NOUN_ADJ:
                                # some of these are really ADJ's
                                # and need to be tagged manually)
                    elif cat.startswith('N'):
                        POS = "%s/NOUN" % voc
                    else:
                        self.err.write("no POS can be deduced in %s!\n" % file)
                        self.err.write(line+'\n')
                        sys.exit(1)

                gloss = re.sub('<pos>.+?</pos>', '', gloss)
                gloss = gloss.strip()

                dict.setdefault(entry, []).append(
                    (entry, voc, cat, gloss, POS, lemmaID))
                entries += 1

        infile.close()
        if not lemmaID == "":
            self.out.write(
                "loaded %d lemmas and %d entries\n" % (lemmas, entries))
        else:
            self.out.write("loaded %d entries\n" % (entries))
        return dict

    def LoadTable(self, file):
        """ Load the given table file """
        p = re.compile('\s+')
        table = {}
        infile = open(file, 'r')

        for line in infile:
            if line.startswith(';'): continue # comment line
            line = line.strip()
            p.sub(' ', line)
            table[line] = 1

        infile.close()
        return table


if __name__ == "__main__":
    """ Read user input, analyze, output results. """
    morph = Analyzer()

    if len(sys.argv) > 1 and sys.argv[1] == "bw":
        print "Buckwalter Arabic Morphological Analyzer (press ctrl-d to exit)"
        while True:
            try:
                s = raw_input("$ ")
                #morph.Process(unicode(s))
                morph.Analyze(s)
            except EOFError:
                print "Goodbye!"
                break
            except UnicodeDecodeError:
                print "Decode error. Skipping."
                

    else:

        print "Unicode Arabic Morphological Analyzer (press ctrl-d to exit)"
        while True:
            try:
                s = raw_input("$ ")
                morph.Process(unicode(s))
            except EOFError:
                print "Goodbye!"
                break
            except UnicodeDecodeError:
                print "Decode error. Skipping."

