#!/usr/bin/env python

'''
    Sample HTXPath unit testing module.
    Fell free to use it as a template.
    Put your input data into testData dir.
'''

import unittest
import htxpath

def collapseResultsWhitespace(result):
    tmp = []
    for item in result:
        tmp.append(htxpath.collapseWhitespace(item))

    return tmp


class BasicTests(unittest.TestCase):

    def setUp(self):
        f = open("test_data/test.htm", "rb")
        self.testData = f.read()
        f.close()

    def testBasicPath(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "//body/div[id=d1]"))
        wanted = ['<div id="d1"> <a href="test test test">OK1</a><br/> <a id="5" class="jaunty" href="5aaa">OK2</a><br/> <a id="5" href="5bbb">OK3&4</a> <div class="bed4"> <div class="bad"></div> <div class="red1"> <input type="help" value="OK4"/> </div> </div> <div aclass="bed4"></div> </div>']

        self.assertEqual(result, wanted)

    def testWildcardArgumentContainigPath(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "//body/div[1]/*[class~ed]"))
        wanted = ['<div class="bed4"> <div class="bad"></div> <div class="red1"> <input type="help" value="OK4"/> </div> </div>']
        self.assertEqual(result, wanted)

    def testWildcardArgumentStartingPath(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "//*[class^e]"))
        wanted = ['<div class="elo"> </div>', '<div-open class="eee"/>']
        self.assertEqual(result, wanted)

    def testWildcardAttribute(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "//h1[*=super]"))
        wanted = ['<h1 class="super">OK</h1>', '<h1 id="super">OK</h1>', '<h1 lang="super">OK</h1>']
        self.assertEqual(result, wanted)

    def testAbsoluteSimplePathGetAttrs(self):
        result = htxpath.find(self.testData, "/html/body/span/input")
        result = htxpath.getAttributes(result[0])
        wanted = {'color': 'humorous', 'type': 'help3', 'value': 'OK5'}
        self.assertEqual(result, wanted)

    def testAttributeExists(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "//*[#value]"))
        wanted = ['<input type="help" value="OK4"/>', '<input type="help" value="OK4"/>', '<input type="help3" value="OK5" color="humorous"/>']
        self.assertEqual(result, wanted)

    def testCDATAEscape(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "/html/test"))
        wanted = ['<test id="test3"> hello &amp; my name is carol =5 &lt;test&gt; </test>']
        self.assertEqual(result, wanted)

    def testTagNestingFix(self):
        result = collapseResultsWhitespace(htxpath.find(self.testData, "/html/span/b[!#class]"))
        wanted = ['<b>something <badly-nested-tag> <b class="fff"> </b> inside th ebadly nested tag </b>']
        self.assertEqual(result, wanted)

    def testTagClosing(self):
        result = htxpath.find(self.testData, "/html/this-tag-is-open")
        result = htxpath.getAttributes(result[0])
        wanted = {'ourvalue': 'hooray!'}
        self.assertEqual(result, wanted)

if __name__ == '__main__':
    unittest.main()

    


    