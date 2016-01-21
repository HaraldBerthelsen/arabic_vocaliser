# -*- coding: UTF-8 -*-
# =====================================================================
# buck.py
# Copyright © 2005 Alexander Lee
# Provides functions for translation between the Buckwalter
# transliteration and Unicode Arabic.
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

import re

_buck2uni = {
    "'" : u"ء",
    "|" : u"آ",
    ">" : u"أ",
    "O" : u"أ",
    "&" : u"ؤ",
    "W" : u"ؤ",
    "<" : u"إ",
    "I" : u"إ",
    "}" : u"ئ",
    "A" : u"ا",
    "b" : u"ب",
    "p" : u"ة",
    "t" : u"ت",
    "v" : u"ث",
    "j" : u"ج",
    "H" : u"ح",
    "x" : u"خ",
    "d" : u"د",
    "*" : u"ذ",
    "r" : u"ر",
    "z" : u"ز",
    "s" : u"س",
    "$" : u"ش",
    "S" : u"ص",
    "D" : u"ض",
    "T" : u"ط",
    "Z" : u"ظ",
    "E" : u"ع",
    "g" : u"غ",
    "_" : u"ـ",
    "f" : u"ف",
    "q" : u"ق",
    "k" : u"ك",
    "l" : u"ل",
    "m" : u"م",
    "n" : u"ن",
    "h" : u"ه",
    "w" : u"و",
    "Y" : u"ى",
    "y" : u"ي",
    "F" : u"ً",
    "N" : u"ٌ",
    "K" : u"ٍ",
    "a" : u"َ",
    "u" : u"ُ",
    "i" : u"ِ",
    "~" : u"ّ",
    "o" : u"ْ",
    "`" : u"ٰ",
}
""" Maps ascii characters to the unicode characters """

# Now we create a reverse mapping.
# Note that the extra characters:
#   I (hamza-under-alif) -> duplicates <
#   O (hamza-over-alif) -> duplicates >
#   W (hamza-on-waw) -> duplicates &
# must be removed, since these are duplicates that Buckwalter has
# proposed for XML compatibility. I'll just remove them from now.

_tmp = _buck2uni.copy()
del _tmp['I']
del _tmp['O']
del _tmp['W']

_uni2buck = dict([[v,k] for k,v in _tmp.items()])
""" Maps unicode characters to ascii characters """

# =====================================================================

_buck2uni_patstr = '[%s]' % ''.join(map(re.escape, _buck2uni.keys()))
_buck2uni_pat = re.compile(_buck2uni_patstr)

def buck2uni(str):
    """ Convert string from Buckwalter transliteration to Unicode """
    def repl(match):
        value = match.group()
        return _buck2uni[value]

    result = _buck2uni_pat.sub(repl, str)
    return unicode(result)

_uni2buck_patstr = '[%s]' % ''.join(map(re.escape, _uni2buck.keys()))
_uni2buck_pat = re.compile(_uni2buck_patstr)

def uni2buck(str):
    """ Convert string from Buckwalter transliteration to Unicode """
    def repl(match):
        value = match.group()
        return _uni2buck[value]

    result = _uni2buck_pat.sub(repl, str)
    return result
