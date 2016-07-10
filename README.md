# highlightedWriter

Allows to write text to the console, that will be automatically highlighted.

The colors are applied via ASCII escape sequences, so all terminals that recognize ASCII escape sequences are supported.

##Example

This code sets up the highlighting, of all python keywords, comments, numeric-literals and most strings-literal types
```python
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

  w = HighlightedWriter(sys.stdout, wordColorDict, colorMode="auto")

  #Print itself
  f = open(__file__, "r")
  w.write(f.read())
```
###Output
![Alt text](img/example.png?raw=true "Example")

