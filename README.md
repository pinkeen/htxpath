
===== HTXPath README =====

* What is it for?

HTXPath is a python module which simplifies the task of extracting pieces of data from [x]html (or like) documents.

You specify a PATH string (somewhat similar in syntax and principles to XPath) that defines an unambiguous set of elements within a document.

* Why HTXPath?

First of all, I haven't found any python libraries which were intended for the sole purpose of web page data harvesting.

Python XPath implementations are very slow, memory hogs which do not perform at all with not well-formed XML. That last thing is rather good cosidering their job. (Not even mentioning the char encoding hell.)
Unfortunately most of HTML and even XHTML out there doesn't stand a chance against their parsers.

That's when I tried BeautifulSoup - the only viable solution I found on the net. It didn't produce well-formed XML either so I had to tune every little problem with regexp filtering tricks. What's more, some poorly coded sites were stripped down by BS so that only few tags were left (sic!). 

So what about the one-night hand-crafted solution that is HTXPath you ask?

Cutting to the chase:

It's fast and doesn't require much memory because it doesn't preparse the data into a friedly structure but rather processes it as a stream using regexps. It doesn't care about standards' compliance - it goes where you need it to ingoring all that isn't needed to get there.

It's written in Python. ;)

* Features

> Fast, saves memory
> Familiar syntax (similar to XPath)
> Escapes CDATA
> Fixes orphaned tags:
	Closes tags which doesn't have '/' or a corresponding closing tag. Removes closing tags which doesn't have opening ones.
> Copes with badly nested tags in SOME situations.
	SO DON'T COUNT ON IT!
> Should work well with UNICODE input.
		
==== BASIC USAGE INSTRUCTIONS ====

Before you start:
> HTXPath strips documents of HTML comments and scripts before even parsing begins. That probably will be fixed sometime.
> DOCTYPE is also stripped and it won't be fixed because there are plenty of ways to get it without using such sophisticated (yeah, right ;)) tools.
> CDATA is liquidated but its content is left intact with crucial html entities escaped.

Probably the only function you will be needing is

	def find(xml, pth):

Where xml is your data (not necesarilly XML) and pth is the "command path string" (referred to as THE PATH [to the geek garden of pleasure ;)]). Function will return a list (always) of strings containig matched tags with everything inside them, so you can extract their attributes.

Path consist of "commands" which are separated by slashes (/) or double-slashes (//). For example "//body/div[class=main]" gives us
two commands: "body" and "div[class=main]".

Each command consists of tag name and a condition contained in square brackets ([]).

Single slash tells the parser to match the command only to tags nested directly below (inside) the previous tag or document root, whereas the double slash means that all nesting levels below the previous tag matched will be checked. You can have unlimited number of double slash separators in your path and they can be anywhere - unlike in the XPath.

A command can have multiple conditions (ex, div[class=test][id=main]). The command matched the tag when all conditions are met.

Contidtion types reference:
> [number] - ex. div[4] means that the fourth div within current scope is matched

> [attribute=value] - self-explanatory

> [attribute^value] - attribute starts with value

> [attribute~value] - attribute contains value

> [#attribute] - matches if attribute is present in the tag regardless of its value

Each of the qualifiers (#,^,~,=) can be negated with "!" sign (!#,!^,!~,!=).

Attribute and tag names can be "*" characters - then they are treated as wildcards and match any string - ex. "//*[*=hello]" will match any tag anywhere in the document as long as it contains any attribute with the value "hello".

Very handy function:

def getAttributes(xml)

It returns a dictionary of attributes with their corresponding values of the outer wrapping tag (in other words first encountered) in the xml string. Just feed it with an element from the "find" function result.

* Additional functions you're free to use:

> def stripComments(xml)
> def escapeCDATA(xml)
> def removeScriptTags(xml)
> def getText(xml) - strips xml of any tags
> def getTextLikeBrowser(xml) - strips tags, substitutes line break tags with newline characters and collapses whitespace
> def collapseWhitespace(xml)

2009 (C) Filip Sobalski <pinkeen@gmail.com>
