# Roster Code Style Guide #
## Overview ##
These are code guidelines for contributing to Roster. Please read and follow these guidelines before committing code to the Roster SVN tree.

This is a modified version of the [Google Python Style Guide r2.15](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html) by Amit Patel, Antoine Picard, Eugene Jhong, Jeremy Hylton, Matt Smart, and Mike Shields.



## Python Style Rules ##

### Semicolons ###
Do not terminate your lines with semi-colons and do not use semi-colons to put two commands on the same line.

### Line length ###
Maximum line length is 80 characters.

> Exception: lines importing modules may end up longer than 80 characters only if using Python 2.4 or earlier.

> Make use of Python's implicit line joining inside parentheses, brackets and braces. If necessary, you can add an extra pair of parentheses around an expression.
```
Yes: foo_bar(self, width, height, color='black', design=None, x='foo',
             emphasis=None, highlight=0)

     if (width == 0 and height == 0 and
         color == 'red' and emphasis == 'strong'):
```
> When a literal string won't fit on a single line, use parentheses for implicit line joining.
```
x = ('This will build a very long long '
     'long long long long long long string')
```

### Parentheses ###
Use parentheses sparingly.

> Do not use them in return statements or in for statements unless using parentheses for implied line continuation. (See above.) It is however fine to use parentheses around tuples.
```
Yes: for x, y in dict.items():
       bar()
     while (x):
       x = bar()
     if (x):
       bar():
     if (not x):
       bar()
     if (x and y):
       bar()
     return foo
```
```
No:  for (x, y) in dict.items():
       bar()
     while x:
       x=bar()
     if foo:
       bar()
     if not x:
       bar()
     if x and y:
       bar()
     return (foo)
```

### Indentation ###
Indent your code blocks with 2 spaces and indent line continuations with 4 spaces.
> Never use tabs or mix tabs and spaces. In cases of implied line continuation, you should align wrapped elements either vertically, as per the examples in the line length section; or using a hanging indent of 4 spaces, in which case there should be no argument on the first line.
```
Yes:   # Aligned with opening delimiter
       foo = long_function_name(var_one, var_two,
                                var_three, var_four)

       # 4-space hanging indent; nothing on first line
       foo = long_function_name(
           var_one, var_two, var_three,
           var_four)
```
```
No:    # Stuff on first line forbidden
       foo = long_function_name(var_one, var_two,
           var_three, var_four)

       # 2-space hanging indent forbidden
       foo = long_function_name(
         var_one, var_two, var_three,
         var_four)
```

### Blank Lines ###
Two blank lines between top-level definitions, one blank line between method definitions.
> Two blank lines between top-level definitions, be they function or class definitions. One blank line between method definitions and between the class line and the first method. Use single blank lines as you judge appropriate within functions or methods.

### Whitespace ###
Follow standard typographic rules for the use of spaces around punctuation.
> No whitespace inside parentheses, brackets or braces.
```
Yes: spam(ham[1], {eggs: 2}, [])
```
```
No:  spam( ham[ 1 ], { eggs: 2 }, [ ] )
```
> No whitespace before a comma, semicolon, or colon. Do use whitespace after a comma, semicolon, or colon except at the end of the line.
```
Yes: if x == 4:
       print x, y
     x, y = y, x
```
```
No:  if x == 4 :
       print x , y
     x , y = y , x
```
> No whitespace before the open paren/bracket that starts an argument list, indexing or slicing.
```
Yes: spam(1)
```
```
No:  spam (1)
```
```
Yes: dict['key'] = list[index]
```
```
No:  dict ['key'] = list [index]
```
> Surround binary operators with a single space on either side for assignment (=), comparisons (==, <, >, !=, <>, <=, >=, in, not in, is, is not), and Booleans (and, or, not). Use your better judgment for the insertion of spaces around arithmetic operators but always be consistent about whitespace on either side of a binary operator.
```
Yes: x == 1
```
```
No:  x<1
```
> Don't use spaces around the '=' sign when used to indicate a keyword argument or a default parameter value.
```
Yes: def complex(real, imag=0.0): return magic(r=real, i=imag)
```
```
No:  def complex(real, imag = 0.0): return magic(r = real, i = imag)
```
> Don't use spaces to vertically align tokens on consecutive lines, since it becomes a maintenance burden (applies to :, #, =, etc.):
```
Yes:
     foo = 1000  # comment
     long_name = 2  # comment that should not be aligned

     dictionary = {
         "foo": 1,
         "long_name": 2,
         }
```
```
No:
     foo       = 1000  # comment
     long_name = 2     # comment that should not be aligned

      dictionary = {
          "foo"      : 1,
          "long_name": 2,
          }
```

### Python Interpreter ###
Modules should begin with #!/usr/bin/env python
> Modules should begin with a "shebang" line specifying the Python interpreter used to execute the program:
```
#!/usr/bin/env python
```

### Comments ###
Be sure to use the right style for module, function, method and in-line comments. Comments are always on the same indentation as the code it is commenting, use 2 '#' characters and a space.
```
Yes: ## comment
```
```
No:  #comment
```
#### Doc Strings ####
> Python has a unique commenting style using doc strings. A doc string is a string that is the first statement in a package, module, class or function. These strings can be extracted automatically through the `__`doc`__` member of the object and are used by pydoc. (Try running pydoc on your module to see how it looks.) Our convention for doc strings is to use the three double-quote format for strings. A doc string should be organized as a summary line (one physical line) terminated by a period, question mark, or exclamation point, followed by a blank line, followed by the rest of the doc string starting at the same cursor position as the first quote of the first line. There are more formatting guidelines for doc strings below.
#### Modules ####
> Every file should contain the following items, in order:
    * a copyright statement.
```
# Copyright (c) 2009, Purdue University
```
    * a license boilerplate. Choose the appropriate boilerplate for the license used by the project (for example, Apache 2.0, BSD, LGPL, GPL)
```
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# Neither the name of the Purdue University nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

#### Functions and Methods ####

> Any function or method which is not both obvious and very short needs a doc string. Additionally, any externally accessible function or method regardless of length or simplicity needs a doc string. The doc string should include what the function does and have detailed descriptions of the input and output. It should not, generally, describe how it does it unless it's some complicated algorithm. For tricky code block/inline comments within the code are more appropriate. The doc string should give enough information to write a call to the function without looking at a single line of the function's code. Inputs should be individually documented, an explanation following after a colon, and should use a uniform hanging indent of 2 or 4 spaces. The doc string should specify the expected types where specific types are required. A "Raises:" section should list all exceptions that can be raised by the function. The doc string for generator functions should use "Yields:" rather than "Outputs:".
```
def fetch_bigtable_rows(big_table, keys, other_silly_variable=None):
  """Fetches rows from a Bigtable.

  Retrieves rows pertaining to the given keys from the Table instance
  represented by big_table.  Silly things may happen if
  other_silly_variable is not None.

  Inputs:
    big_table: An open Bigtable Table instance.
    keys: A sequence of strings representing the key of each table row
        to fetch.
    other_silly_variable: Another optional variable, that has a much
        longer name than the other args, and which does nothing.

  Outputs:
    A dict mapping keys to the corresponding table row data
    fetched. Each row is represented as a tuple of strings. For
    example:

    {'Serak': ('Rigel VII', 'Preparer'),
     'Zim': ('Irk', 'Invader'),
     'Lrrr': ('Omicron Persei 8', 'Emperor')}

    If a key from the keys argument is missing from the dictionary,
    then that row was not found in the table.

  Raises:
    IOError: An error occurred accessing the bigtable.Table object.
  """
  pass
```
#### Classes ####

> Classes should have a doc string below the class definition describing the class. If your class has public attributes, they should be documented here in an Attributes section and follow the same formatting as a function's Args section.
```
class SampleClass(object):
  """Summary of class here.

  Longer class information....
  Longer class information....

  Attributes:
    likes_spam: A boolean indicating if we like SPAM or not.
    eggs: An integer count of the eggs we have laid.
  """

  def __init__(self, likes_spam=False):
    """Inits SampleClass with blah."""
    self.likes_spam = likes_spam
    self.eggs = 0

  def public_method(self):
    """Performs operation blah."""
```
#### Block and Inline Comments ####

> The final place to have comments is in tricky parts of the code. If you're going to have to explain it at the next code review, you should comment it now. Complicated operations get a few lines of comments before the operations commence.
```
## We use a weighted dictionary search to find out where i is in
## the array.  We extrapolate position based on the largest num
## in the array and the array size and then do binary search to
## get the exact number.

if i & (i-1) == 0:        # true iff i is a power of 2
```
> To improve legibility, these comments should be at least 2 spaces away from the code.

> On the other hand, never describe the code. Assume the person reading the code knows Python (though not what you're trying to do) better than you do.
```
## BAD COMMENT: Now go through the b array and make sure whenever i occurs
## the next element is i+1
```

### Classes ###
If a class inherits from no other base classes, explicitly inherit from object. This also applies to nested classes.
```
Yes: class SampleClass(object):
       pass


     class OuterClass(object):

       class InnerClass(object):
         pass


     class ChildClass(ParentClass):
       """Explicitly inherits from another class already."""
```
```
No: class SampleClass:
      pass


    class OuterClass:

      class InnerClass:
         pass
```
> Inheriting from object is needed to make properties work properly, and it will protect your code from one particular potential incompatibility with Python 3000. It also defines special methods that implement the default semantics of objects including `__`new`__`, `__`init`__`, `__`delattr`__`, `__`getattribute`__`, `__`setattr`__`, `__`hash`__`, `__`repr`__`, and `__`str`__`.

### Strings ###
Use the % operator for formatting strings, even when the parameters are all strings. Never use + to concatenate strings.
```
Yes: x = '%s%s' % (a, b)
     x = '%s, %s!' % (imperative, expletive)
     x = 'name: %s; score: %d' % (name, n)
```
```
No:  x = a + b
     x = imperative + ', ' + expletive + '!'
     x = 'name: ' + name + '; score: ' + str(n)
```
> Avoid using the + and += operators to accumulate a string within a loop. Since strings are immutable, this creates unnecessary temporary objects and results in quadratic rather than linear running time. Instead, add each substring to a list and ''.join the list after the loop terminates (or, write each substring to a cStringIO.StringIO buffer).
```
Yes: items = ['<table>']
     for last_name, first_name in employee_list:
       items.append('<tr><td>%s, %s</td></tr>' % (last_name, first_name))
     items.append('</table>')
     employee_table = ''.join(items)
```
```
No: employee_table = '<table>'
    for last_name, first_name in employee_list:
      employee_table += '<tr><td>%s, %s</td></tr>' % (last_name, first_name)
    employee_table += '</table>'
```
> Use """ for multi-line strings rather than '''. Note, however, that it is often cleaner to use implicit line joining since multi-line strings do not flow with the indentation of the rest of the program:
```
Yes:
  print ("This is much nicer.\n"
         "Do it this way.\n")
```
```
  No:
      print """This is pretty ugly.
Don't do this.
"""
```

### TODO Comments ###
TODOs should never be used. Instead, open up an issue if it needs to be attended to later.

### Imports formatting ###
Imports should be on separate lines.
> E.g.:
```
Yes: import os
     import sys
```
```
No:  import os, sys
```
> Imports are always put at the top of the file, just after any module comments and doc strings and before module globals and constants. Imports should be grouped with the order being most generic to least generic:
    * standard library imports
    * third-party imports
    * application-specific imports

> Within each grouping, imports should be sorted lexicographically, ignoring case, according to each module's full package path.
```
import foo
from foo import bar
from foo.bar import baz
from foo.bar import Quux
from Foob import ar
```

### Statements ###
Only one statement per line.
```
Yes: if foo:
       bar(foo)

     try:
       bar(foo)
     except ValueError:
       baz(foo)
```
```
No:  if foo: bar(foo)

  if foo: bar(foo)
  else:   baz(foo)

  try:               bar(foo)
  except ValueError: baz(foo)

  try:
    bar(foo)
  except ValueError: baz(foo)
```

### Access Control ###
If an accessor function would be trivial you should use public variables instead of accessor functions to avoid the extra cost of function calls in Python. When more functionality is added you can use property to keep the syntax consistent.
> On the other hand, if access is more complex, or the cost of accessing the variable is significant, you should use function calls (following the Naming guidelines) such as get\_foo()  and set\_foo(). If the past behavior allowed access through a property, do not bind the new accessor functions to the property. Any code still attempting to access the variable by the old method should break visibly so they are made aware of the change in complexity.

### Naming ###
module\_name, package\_name, ClassName, method\_name, ExceptionName, FunctionName, GLOBAL\_VAR\_NAME, instance\_var\_name, function\_parameter\_name, local\_var\_name.
#### Names to Avoid ####
  * single character names except for counters or iterators
  * dashes (-) in any package/module name
  * `_``_`double\_leading\_and\_trailing\_underscore`_``_` names (reserved by Python)
#### Naming Convention ####
  * "Internal" means internal to a module or protected or private within a class.
  * Prepending a single underscore (`_`) has some support for protecting module variables and functions (not included with import `*` from). Prepending a double underscore (`__`) to an instance variable or method effectively serves to make the variable or method private to its class (using name mangling).
  * Place related classes and top-level functions together in a module. Unlike Java, there is no need to limit yourself to one class per module.
  * Use CapWords for class names, but lower\_with\_under.py for module names. Although there are many existing modules named CapWords.py, this is now discouraged because it's confusing when the module happens to be named after a class. ("wait -- did I write import StringIO or from StringIO import StringIO?")
#### Naming Examples ####
| **Type** | **Public** | **Internal** |
|:---------|:-----------|:-------------|
| Packages | lower\_with\_under |  |
| Modules | lower\_with\_under | `_`lower\_with\_under |
| Classes | CapWords | `_`CapWords |
| Exceptions | CapWords |  |
| Functions | CapWords() | `_`CapWords() |
| Global/Class Constants | CAPS\_WITH\_UNDER | `_`CAPS\_WITH\_UNDER |
| Global/Class Variables | lower\_with\_under | `_`lower\_with\_under |
| Instance Variables | lower\_with\_under | `_`lower\_with\_under() (protected) or `__`lower\_with\_under() (private) |
| Method Names | lower\_with\_under() | `_`lower\_with\_under() (protected) or `__`lower\_with\_under() (private) |
| Function/Method Parameters | lower\_with under |  |
| Local Variables | lower\_with\_under |  |

### Main ###
Even a file meant to be used as a script should be importable and a mere import should not have the side effect of executing the script's main functionality. The main functionality should be in a main() function.
> In Python, pychecker, pydoc, and unit tests require modules to be importable. Your code should always check if `_``_`name`__` == '`_``_`main`_``_`' before executing your main program so that the main program is not executed when the module is imported.
```
def main():
  ...

if __name__ == '__main__':
  main()
```
> All code at the top level will be executed when the module is imported. Be careful not to call functions, create objects, or perform other operations that should not be executed when the file is being pychecked or pydoced.