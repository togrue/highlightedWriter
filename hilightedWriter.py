#          Copyright Tobias Gruen 2016
# Distributed under the Boost Software License, Version 1.0.
#    (See accompanying file LICENSE_1_0.txt or copy at
#          http://www.boost.org/LICENSE_1_0.txt)

# Note:
# The windows terminal has introduced support ASCII escape-sequences in windows 10.
# Colors can't be displayed before Window 10.

import re, os, platform
import sys
 
_highlictColorDict = {
    "black":         (30, None),
    "bright-black":  (30, 1),
    "red":           (31, None),
    "bright-red":    (31, 1),
    "green":         (32, None),
    "bright-green":  (32, 1),
    "yellow":        (33, None),
    "bright-yellow": (33, 1),
    "blue":          (34, None),
    "bright-blue":   (34, 1),
    "magenta":       (35, None),
    "bright-magenta":(35, 1),
    "cyan":          (36, None),
    "bright-cyan":   (36, 1),
    "white":         (37, None),
    "bright-white":  (37, 1),
} 

def _isHighlighterRegex(txt, wordMatchRegex):
  return re.match(wordMatchRegex, txt) is None
  
def safe_cast(val, to_type, default=None):
  try:
    return to_type(val)
  except ValueError:
    return default

def streamSupportsColor(stream):
  """
  Returns True if the stream goes to a terminal that supports color
  """
  isAtty = hasattr(stream, "isatty") and stream.isatty()
  system =  platform.system()
  revision = safe_cast("a"+platform.release(), int, 0)

  if isAtty:
    if not (system == "Windows" and revision < 10):
      return True
  return False

  
class HighlightedWriter:
  """
  Adds terminal color-escape-sequences to the output text, according to a highlighting dictionary.
  
  The Highlighting dictionary distinguishs between 
   - non-regex strings, they are only highlighted if they match a whole word
   - regex strings
  Color mapping keys are considered as a Regex, if the wordMatchRegex doesn't match the key string.
  """
  # A dictionary that contains all the non regex matches.
  wordsColorMap = {}
  # A dictionary with the regex names and their color.
  regexColorMap = {}
  
  # The print output stream, to this stream will be written.
  flushAfterWrite = True
  outputStream = sys.stdout
  highlight = False

  def __init__(self, outputStream, colorMapping, flushAfterWrite = True, colorMode = "auto", wordMatchRegex=r"[a-zA-Z_][\w_]*"):
    """
    outputStream =  the stream where the colorized Text goes
    colorMapping = a dictionary consisting of keyword/captureRegex (key) to color (value) items eg. {"for":"bright-blue", "while":"red", "//.*":"green"}
                   Available colors are: "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white" and the same colors in "bright-{colorname}" variants.
                   implemention detail: all the regex expressions are combined into one single regex (so if modifiers are applied to a key they have to be undone at the end of the regex):
                   e.g. "(?i)...(?-i)" or simply "(?i:...)"
    flushAfterWrite = if True, flush() is called at the stream after writing.
    colorMode = one of ("auto", "on", "off"). If color mode is auto it enables colors, if the output stream is a console that supports colors.
    wordMatchRegex = the regex to match the non-regex matches
    """
    self.outputStream = outputStream  
    
    if colorMode == "auto":
      self.highlight = streamSupportsColor(self.outputStream)
    elif colorMode == "on":
      self.highlight = True
    elif colorMode == "off":
      self.highlight = False
    else:
      raise Exception("Unsupported color mode")
      
    self.wordsColorMap = dict(filter(lambda x: not _isHighlighterRegex(x[0], wordMatchRegex), colorMapping.items()))
    regexMappings = list(filter(lambda x: _isHighlighterRegex(x[0], wordMatchRegex), colorMapping.items()))
    
    regexes = []
    for n, r in enumerate(regexMappings):
      # Try to compile the single regexes (syntax only check)
      re.compile(r[0]) 
      groupName = "g_"+str(n)
      # associate the color, with a generated regex group name
      self.regexColorMap[groupName] = r[1] 
      regexes.append("(?P<%s>%s)"%(groupName, r[0]))
      
    regexes.append("(?P<g_word>%s)"%(wordMatchRegex))
    
    combinedRegex = "|".join(regexes)
    self.regex = re.compile(combinedRegex)

  def _highlight(self, txt, color):
    colorEntry = _highlictColorDict.get(color, None)
    if colorEntry:
      if colorEntry[1] is None:
        return "\x1B[%dm%s\x1B[0m"%(colorEntry[0], txt)
      else:
        return "\x1B[%d;%dm%s\x1B[0m"%(colorEntry[0], colorEntry[1], txt)
    else:    
      return txt
  
  def _createHighlightedText(self, txt):
    if self.regex is None:
      return txt
      
    highlight = self._highlight
    outtxt = ""
    lastend = 0
    for m in re.finditer(self.regex, txt):
      outtxt += txt[lastend:m.start()]
      lastend = m.end()
      
      foundGroup=""
      if m.lastgroup and m.lastgroup.startswith("g_"):
        foundGroup=m.lastgroup;
        
      color = ""
      if foundGroup == "g_word":
        color = self.wordsColorMap.get(m.group(0),"")
        outtxt += highlight(m.group(0), color)
      else:
        color = self.regexColorMap.get(foundGroup, "")
        outtxt += highlight(m.group(0), color)
      
    outtxt += txt[lastend:]  
    return outtxt
  
  def write(self, txt):  
    if(self.highlight):
      txt = self._createHighlightedText(txt)
    self.outputStream.write(txt)
    if self.flushAfterWrite:
      self.outputStream.flush()
  
  def writeln(self, txt):
    self.write(txt+'\n')
  
  def flush():
    if self.outputStream:
      self.outputStream.flush()


def _highlightedWriterTest():
  kwds = """ and       del       from      not       while     as        elif      global    or        with   
             assert    else      if        pass      yield     break     except    import    print            
             class     exec      in        raise     continue  finally   is        return           
             def       for       lambda    try """             
  wordColorDict = {
        "#.*"                                                   : "green"              # comments...
       ,"'''([^']|'{1,2})*?'''|r'[^']*'|'([^\\']|\\\\.)*'"      : "bright-green"       # 'strings'
       ,'"""([^"]|"{1,2})*?"""|r"[^"]*"|"(\\\\.|[^\\\\"])*"'    : "bright-green"       # "strings"
       ,r"(\d+(\.\d+(e[+-]?\d+)?)?)|(\.\d+(e[+-]?\d+)?)"        : "red"                # numbers, fp-literals
       }
       
  # Add the keywords to the dictionary (e.g. "and" : "bright-blue")
  for kw in re.finditer("\w+", kwds):
    wordColorDict[kw.group(0)] = "bright-blue"

  # Initialize the HighlightedWriter 
  w = HighlightedWriter(sys.stdout, wordColorDict, colorMode="auto") 
  
  #Print itself
  f = open(__file__, "r")
  w.write(f.read())

  
