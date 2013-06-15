# HTXPath README

## What is it for?

HTXPath is a python module which simplifies the task of extracting pieces of data from [x]html (or like) documents. You would usually use it
for web data scraping.

## How does it work?

You provide a *path* string (somewhat similar in syntax and principles to XPath) that defines an unambiguous set of elements within a document and you get
a list with elements that match your *path*.

## Why HTXPath?

*This section is preserved for historical purposes. There may be some better approaches now. (Or they were always there but I could not find them then.) Skip to cut to the chase.*

First of all, I haven't found any python libraries which were intended for the sole purpose of web page data harvesting.

Python XPath implementations are very slow, memory hogs which do not perform at all with not well-formed XML. That last thing is rather good cosidering their job. (Not even mentioning the char encoding hell.)
Unfortunately most of HTML and even XHTML out there doesn't stand a chance against their parsers.

That's when I tried BeautifulSoup - the only viable solution I found on the net. It didn't produce well-formed XML either so I had to tune every little problem with regexp filtering tricks. What's more, some poorly coded sites were stripped down by BS so that only few tags were left (sic!). 

So what about the one-night hand-crafted solution that is HTXPath you ask?

It's fast and doesn't require much memory because it doesn't preparse the data into a friedly structure but rather processes it as a stream using regexps. It doesn't care about standards' compliance - it goes where you need it to ingoring all that isn't needed to get there.

## HTML and regexps? Huh? Are you insane?

It uses regexps only find small chunks of data in small chunks of data. The general approach is stack based as it is the simplest sane solution for parsing nested blocks of data.

## Features

* Fast.
* Low memory footprint.
* Familiar syntax (similar to XPath).
* Fixes orphaned tags: Closes tags which doesn't have '/' or a corresponding closing tag. Removes closing tags which doesn't have opening ones.
* Copes with badly nested tags in SOME situations.
* Works with unicode input.

## Error resistance

Because HTXPath processes the input like a stream it skips the portions that doesn't interest it. For example - it means that you can get
around badly-formed html by constructing a *path* that does not encompass the areas with errors.

## Basic usage

**Read this before you start!**
* HTXPath strips documents of HTML comments and scripts before even parsing begins. That probably will be fixed sometime.
* DOCTYPE is also stripped and it won't be fixed because there are plenty of ways to get it without using such sophisticated (yeah, right ;)) tools.
* CDATA is liquidated but its content is left intact with crucial html entities escaped.

### The path string

The path consist of *commands* which are separated by slashes (`/`) or double-slashes (`//`). 
For example `//body/div[class=main]` is parsed into two commands: `body` and `div[class=main]`.

Each command consists of a tag name and a condition contained in square brackets (`[]`).

Single slash tells the parser thath the command should only match tags nested directly below (inside) the previous tag or document root.
The double slash means that all nesting levels below the previous tag matched will be checked. 
The number of double slash separators in your path is unlimited and they can be present at any level - unlike in the XPath.

A command can encompass multiple conditions (ex. `div[class=test][id=main]`). 
The command matches the tag when all conditions are met.

#### Conditions

* `[number]` - ex. `div[4]` means that the fourth div within current scope is matched
* `[attribute=value]` - attribute matches the value exactly
* `[attribute^value]` - attribute starts with value
* `[attribute~value]` - attribute contains value
* `[#attribute]` - matches if attribute is present in the tag regardless of its value

Each of the qualifiers (`#`, `^`, `~`, `=`) can be negated with `!` sign (`!#`, `!^`, `!~`, `!=`).

#### Wildcards

Attribute and tag names can be substituted with wildcard (`*`) character. 
For example `//*[*=hello]` will match any tag anywhere in the document as long as it contains any attribute with the value "hello".

### Functions

_All functions assume **unicode** strings._

#### `htxpath.find(xml, pth)`

Parses the string `xml` and (always) returns an list of strings that match the path `pth`.

The strings contain matched tags with everything inside them, so you can extract their attributes.

#### `htxpath.getAttributes(xml)`

Parses the outer wrapping tag (in other words - the first encountered) in the `xml` string and returns its attributes as a dictionary.
Just feed it with an element from the `htxpath.find` function's result.

#### `htxpath.getTextLikeBrowser(xml)`

Strips `xml` string of tags, substitutes line break tags with newline characters and collapses whitespace.

#### `htxpath.getText(xml)`

Strips `xml` string of any tags leaving only the text.

#### `htxpath.stripComments(xml)`

Strips HTML comments from `xml` string.

#### `htxpath.collapseWhitespace(xml)`

Collapses withespace in `xml` string.

# Example usage

*No error checking, just pure fun.*

Demonstrates API not the paths.

## Get the title

```python
result = htxpath.find(html, '//title')[0]
title = htxpath.getTextLikeBrowser(result)
```

## Get all links in a div

```python
links = []
result = htxpath.find(html, '//a[#href]')

for anchor in result:
    attrs = htxpath.getAttributes(anchor)
    text = htxpath.getTextLikeBrowser(anchor)
    href = attrs['href']
    links.append((href, text))
```

# Is it production ready?

Well, it depends on what you mean by *production*. Usually data scrapers encounter a lot of errors and have to deal with them somehow
(skip the erroneus items perhaps?), so moderate error rate is acceptable.

It all depends on your use case. If you have a lot of different sites (based on a lot of templates) the you must find out if the overall error
rate is acceptable. If you scrape a lot of pages rendered from a few templates then you may achieve 0% error rate even without any fine-tuning.

Personally, I used it in production with great results. Scraped data from some seriously broken HTML. Occasionaly I encountered some show-stopping
errors but there is a lot of data out there, you can just try to find another, less-broken source.

# Legal mumbo-jumbo

2009 &copy; Filip Sobalski <pinkeen@gmail.com>

This file is part of HTXPath.

HTXPath is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/pinkeen/htxpath/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

