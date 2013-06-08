#!/usr/bin/env python

"""

    HTXPath python module
    [X]HTML data extraction suite
    2009 (c) Filip Sobalski <pinkeen@gmail.com>


    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import sys
import re

import urllib
import urllib2
import cookielib
import socket
import httplib

cookiejar = cookielib.CookieJar()

command_re = re.compile(r'(/{1,2}.*?)(?=(?:/|$))', re.UNICODE)
pattern_re = re.compile(r'\[(.*?)\]', re.UNICODE)
element_re = re.compile(r'(/{1,2})(.*?)(?:\[|$)', re.UNICODE)
condition_re = re.compile(r'([^" ]+?)\s*(\=|!\=|\^|!\^|~|!~)\s*"?(.*?)"?\s*$', re.UNICODE)
condition_order_re = re.compile(r'\A\d+$', re.UNICODE)
condition_exists_re = re.compile(r'(!?#)(.*)$', re.UNICODE)
tag_re = re.compile(r'\s*<(/)?(.*?)(?:\s+([^<>]*?))?(/)?>', re.DOTALL | re.UNICODE | re.IGNORECASE)
attr_re = re.compile(r'([\da-z]+?)\s*=\s*("|\')(.*?)(\2)', re.DOTALL | re.UNICODE | re.IGNORECASE)
script_tag_re = re.compile(r'<script(.*?)>(.*?)</script>', re.DOTALL | re.UNICODE | re.IGNORECASE)
fix_whitespace_re = re.compile(r'[\s\n\r]+', re.UNICODE)
strip_tags_re = re.compile(r'<.*?>', re.UNICODE | re.DOTALL)
line_break_re = re.compile(r'<br(?:\s.*?)?/?>', re.UNICODE | re.IGNORECASE)
cdata_re = re.compile('<!\[CDATA\[(.*?)\]\]>', re.UNICODE | re.DOTALL | re.IGNORECASE)
amp_re = re.compile(r'&(?![^\s]+;)', re.UNICODE | re.IGNORECASE)
comments_re = re.compile(r'<!--.*?-->', re.UNICODE | re.DOTALL)
doctype_re = re.compile(r'<!DOCTYPE.*?>', re.UNICODE | re.DOTALL)

"""
Is there a proper way to do it?
I mean, so the `if debug: ...` statements could be
skipped by the bytecode compiler in a 'production
environment' somehow ?
"""
debug = False

class PathParseError(Exception):
    """
    Raised when errors concerning parsing path encountered.
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class DataParseError(Exception):
    """
    Raised when errors concerning parsing html data encountered.
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

def httpQuery(address, form_data = {}, encoding = 'utf-8', timeout_secs = 5, max_retries = 4):
    """
    Convenience function. Queries specified address. Query can include post data (ex. for logging in).
    Handles timeouts/errors and retries if needed. Keeps track of cookies via global cookiejar.
    Returns fetched data if successful and None on failure.
    """

    socket.setdefaulttimeout(timeout_secs)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    form_data_ = {}

    for n, v in form_data.iteritems():
        form_data_[n] = v.encode(encoding)

    login_data = urllib.urlencode(form_data_)

    request = urllib2.Request(address, login_data)

    request.add_header('connection', 'keep-alive')
    request.add_header('user-agent', 'HTXPath')

    retry_count = 0

    while True:
        if retry_count == max_retries:
            # couldn't fetch any data
            return None

        retry_count += 1

        try:
            resp = opener.open(request, timeout = timeout_secs)
        except (urllib2.URLError, httplib.BadStatusLine), e:
            # connection error, retrying...
            continue
        try:
            r = resp.read()
        except socket.timeout:
            # socket timeout, retrying...
            continue

        return r

def stripComments(xml):
    """
    Strips html comments.
    """
    return comments_re.sub('', xml)

def stripDOCTYPE(xml):
    """
    Strips html DOCTYPE tag.
    """
    return doctype_re.sub('', xml)

def escapeCDATA(xml):
    """
    Escapes strings contained in CDATA tags and strips xml of these tags.
    Part of internal mechanism.
    """
    cdatas = cdata_re.findall(xml)

    if len(cdatas) == 0:
        return xml

    tmp = xml
    xml = ''

    for cd in cdatas:
        # FIX: following code is pretty fucked up, isn't it ?
        cd = cd.replace('<', '&lt;').replace('>', '&gt;')
        cd = amp_re.sub('&amp;', '<![CDATA[' + cd + ']]>')
        tmp = cdata_re.sub(cd, tmp, 1)
        f = cdata_re.search(tmp)
        xml += tmp[:f.end()]
        tmp = tmp[f.end():]

    xml += tmp

    return cdata_re.sub('\\1', xml)

def removeScriptTags(xml):
    """
    Removes inline scripts. They rather should be escaped?
    """

    return script_tag_re.sub('', xml)

def getText(xml):
    """
    Strips tags and scripts from html.
    """
    xml = script_tag_re.sub('', xml)
    xml = strip_tags_re.sub('', xml)
    return xml

def getTextLikeBrowser(xml):
    """
    Converts html to the form it is seen in a plain text browser.
    """
    xml = line_break_re.sub('\n', xml)
    xml = script_tag_re.sub('', xml)
    xml = strip_tags_re.sub('', xml)
    return fix_whitespace_re.sub(' ', xml).strip()

def collapseWhitespace(xml):
    return fix_whitespace_re.sub(' ', xml).strip()

def getAttributes(xml):
    """
    Returns dictionary of attributes of the first encountered tag in xml.
    """
    s = tag_re.search(xml)

    if s == None: return None

    attrs = s.groups()[2]

    if attrs == None: return None

    res = {}
    for name, devnull, value, devnull in attr_re.findall(attrs):
        res[name.lower()] = value

    return res


def parseCondition(pattern):
    """
    Parses element's select condition (string contained between [] in path).
    Part of internal mechanism.
    """
    condition = condition_order_re.findall(pattern)

    if len(condition) > 0:
        return int(condition[0])

    negate = False

    condition = condition_exists_re.findall(pattern)

    if len(condition) > 0:
        qualifier, attribute = condition[0]

        if len(qualifier) == 2:
            negate = True

        return (negate, re.compile('(?:\s|\A)' + re.escape(attribute) + '(?!\s*")(?:\s*\=\s*".*?")?', re.UNICODE))


    condition = condition_re.findall(pattern)

    if len(condition) == 0:
        raise PathParseError("cannot parse command condition '%s'" % (pattern))

    if debug: print "\t\t\tCondition: " + str(condition)

    attribute, qualifier, value = condition[0]
    if len(qualifier) == 2:
        negate = True
        qualifier = qualifier[1]

    attribute = re.escape(attribute)
    value = re.escape(value)

    if attribute == r'\*':
        attribute = '.*?'

    dre = ''

    if qualifier == '=':
        dre = r'(?:\s|\A)%s\s*\=\s*(\'|")%s\1'

    if qualifier == '~':
        dre = r'(?:\s|\A)%s\s*\=\s*(\'|").*?%s.*?\1'

    if qualifier == '^':
        dre = r'(?:\s|\A)%s\s*\=\s*(\'|")%s.*?\1'

    return (negate, re.compile(dre % (attribute, value), re.UNICODE))

def parseCommand(command):
    """
    Returns parsed command (part of the path delimited by slashes) string.
    """
    gscope = False
    scope, element = element_re.findall(command)[0]

    if len(element) == 0:
        raise PathParseError("cannot parse command: tag name not found in '%s'" % (command))

    if len(scope) == 2: gscope = True

    if debug:   print "\t\tElement: " + element + " (global scope: " + str(gscope) + ")"

    patterns = pattern_re.findall(command)

    conditions = []

    for pattern in patterns:
        pp = parseCondition(pattern)
        conditions.append(pp)
        if debug:   print "\t\tPattern: " + str(pp)

    return (gscope, element, conditions)


def find(xml, pth):
    """
    Parses path string and returns elements conforming to the path in the xml string.
    """
    if debug: print "Path: " + pth

    command_strings = command_re.findall(pth)
    commands = []

    for c in command_strings:
        if debug: print "\tCommand: " + c
        commands.append(parseCommand(c))

    if len(commands) == 0:
        raise PathParseError("found no usable commands in path")

    xml = removeScriptTags(xml)
    xml = escapeCDATA(xml)
    xml = stripComments(xml)
    xml = stripDOCTYPE(xml)
    xml = removeOrphanedTags(xml)

    return findIn(xml, commands)


def findIn(xml, commands):
    """
    Returns searches for tags conforming to parsed command path. Recurses if has to go into
    a nested tag.
    """
    if debug: print "\tStarting parsing loop..."

    found = []

    content = xml

    ci = 0
    count = 0

    while True:
        gs, ctg, ccn = commands[0]

        ctg = ctg.lower()

        f = tag_re.search(content)

        if f == None: return found

        end, tag, attr, cls = f.groups()

        tag = tag.lower()

        if debug:
            print "\t\tNext iter..."
            print "\t\tTag: ", f.groups()
            print "\t\tCount: ", count

        if end == None:
            if (tag == ctg or ctg == '*'): count += 1

            if (tag == ctg or ctg == '*') and checkConditions(ccn, attr, count):
                if debug: print "\t\tCommand MATCHED."

                if cls == None:
                    endpos = getEndTagPos(content[f.end():], tag) + f.end()
                    tmp = content[f.end():endpos]

                    if len(commands) > 1:
                        if debug: print "\tGoing IN."
                        found.extend(findIn(tmp, commands[1:]))
                        if debug: print "\tComing OUT."
                    else:
                        found.append(content[f.start():endpos])

                    if gs: content = content[f.end():]
                    else: content = content[endpos:]

                else:
                    if len(commands) == 1:
                        found.append(content[f.start():f.end()])
                    content = content[f.end():]

            else:
                if not gs and cls == None:
                    if debug: print "\t\tNot global scope, not found. Skipping tag..."
                    endpos = getEndTagPos(content[f.end():], tag) + f.end()
                    content = content[endpos:]
                else:
                    if debug: print "\t\tGlobal scope, not found. Advancing to next tag..."
                    content = content[f.end():]
        else:
            if debug: print "\t\tEnding tag found. Advancing to next tag..."
            content = content[f.end():]



def checkConditions(conditions, attributes, count):
    """
    Checks if the attributes fullfill parsed conditions (among them tag order count if applicable).
    """
    if attributes == None:  attributes = ''
    if len(conditions) == 0: return True

    for c in conditions:
        if type(c) == int:
            if count != c:
                return False
        else:
            neg, exp = c
            res = exp.search(attributes)

            if res and neg:
                return False
            if not res and not neg:
                return False

    return True

def getEndTagPos(xml, tag):
    """
    Returns position of the ending of the appropriate closing tag in the xml string.
    """
    tstack = []

    pos = 0

    while True:
        ef = tag_re.search(xml, pos)
        eend, etag, eattr, ecls = ef.groups()

        etag = etag.lower()
        pos = ef.end()

        if ecls == None and etag.strip() != 'br':
            if eend == None:
                tstack.append(etag)
            else:
                if len(tstack) == 0 and etag == tag:
                    break

                # tag nesting fix

                # will not work with all badly nested tags - will fail in certain situations depending on the path ;(

                # PROB: what if tag whose ending we're searching for contains badly nested (not closed within it) tags ?
                #   DataParseError below is thrown on its ending encountered, ouch...

                ttstack = []
                while True:
                    if len(tstack) == 0:
                        # fix for PROB:
                        if tag == etag:
                            # so, is this the ending we hoped for ?
                            return pos
                        else:
                            raise DataParseError("could not find corresponding end tag for '%s': found end tag '%s' withouth starting tag (tag stack empty)" % (tag, etag))

                    ft = tstack.pop()

                    if ft == etag:
                        tstack.extend(ttstack)
                        break
                    else:
                        ttstack.insert(0, ft)

    return pos

def removeOrphanedTags(xml):
    """
    Closes/removes open tags.
    """

    ostack = []
    cstack = []

    pos = 0

    while True:
        ef = tag_re.search(xml, pos)

        if ef == None:
            break

        eend, etag, eattr, ecls = ef.groups()
        etag = etag.lower()

        if ecls == None and etag.strip() != 'br':
            if eend == None:
                ostack.append((etag, ef.start()))
            else:
                ostack_tmp = []

                while True:
                    if len(ostack) == 0:
                        cstack.append((etag, ef.start()))
                        ostack.extend(ostack_tmp)
                        break

                    ft, start = ostack.pop()

                    if ft == etag:
                        ostack.extend(ostack_tmp)
                        break
                    else:
                        ostack_tmp.insert(0, (ft, start))

        pos = ef.end()

    if debug: print "\t\t\t\tRemoving orpahned tags..."

    ostack.extend(cstack)

    shift = 0

    for t in ostack:
        tag, start = t

        if debug: print "\t\t\t\tTag '%s' starts at %d " % (tag, start + shift)

        ef = tag_re.search(xml, start + shift)

        tag = ef.group()
        eend = ef.groups()[0]

        if eend:
            xml = xml[:ef.start()] + xml[ef.end():]
            shift -= len(tag)
        else:
            xml = xml[:ef.start()] + tag[:len(tag) - 1] + '/>' + xml[ef.end():]
            shift += 1

        if debug: print "\t\t\t\tFound tag : " + ef.group().strip()

    return xml
            

if __name__ == "__main__":

    print "HTXPath python module (testing app)"
    print "[X]HTML data extraction suite"
    print "2009 (c) Filip Sobalski <pinkeen@gmail.com>"
    print "\nInstructions:\nSupply PATH string as first argument.\nFeed XHTML into the STDIN or supply URL as the second argument.\n"

    if len(sys.argv) == 3:
        d = httpQuery(sys.argv[2])
    else:
        d = sys.stdin.read()

    f = find(d, sys.argv[1])

    if len(f) == 0:
        print "-> No element matching path '%s' found." % (sys.argv[1])

    for i in range(0, len(f)):
        print "-> Result %d of %d : " % (i + 1, len(f))
        print "-> Found tag attributes: " + str(getAttributes(f[i]))
        print f[i]
    



