#!/usr/bin/env python
#
# Copyright (C) 2011 Dave Eddy <dave@daveeddy.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# XMLDict.py
# XMLDict class used to convert a dictionary into an XML string
#
# Author
#  Dave Eddy <dave@daveeddy.com>
#  http://www.daveeddy.com
#

from xml.dom.minidom import parse, parseString

# Convenience Functions
def convert_dict_to_xml(dict):
    """Convenience Function: This creates an XMLDict object, and returns the XML string"""
    a   = XMLDict(dict)
    xml = a.get_xml()
    return xml

def prettify(xml):
    """Convenience Function: This returns a pretty version of the XML"""
    return parseString(xml).toprettyxml()

class XMLDict:
    """Class used to convert a python dictionary to XML"""
    def __init__(self, dict):
        """Create the XML and store it"""
        self.dict = dict
        self.xml  = self._convert_dict_to_xml(self.dict)

    def get_xml(self):
        """Returns the XML"""
        return self.xml

    def get_pretty_xml(self):
        """Returns the pretty XML"""
        return parseString(self.xml).toprettyxml()

    def _convert_dict_to_xml(self, dict):
        """Converts a dictionary to XML"""
        xml = ''
        for k,v in dict.iteritems(): # iterate through the dictionary
            if self._is_dict(v): # the value is a dictionary
                xml += "<%s>" % (k)
                xml += self._convert_dict_to_xml(v) # recursively call itself
                xml += "</%s>" % (k)
            else: #value is not a dictionary
                if not self._is_list(v):
                    v = [v]
                for value in v:
                    if self._is_dict(value):
                        xml += "<%s>" % (k)
                        xml += self._convert_dict_to_xml(value) # recursively call itself
                        xml += "</%s>" % (k)
                    else:
                        xml += "<%s>%s</%s>" % (str(k),str(value),str(k))

        return xml

    def _is_dict(self, a):
        """Returns True if the item is a dictionary"""
        return type(a) == type({})

    def _is_list(self, a):
        """Returns True if the item is a list"""
        return type(a) == type([])
