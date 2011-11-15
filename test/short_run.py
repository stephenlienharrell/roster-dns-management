#!/usr/bin/env python

import glob
import os
import sys
import subprocess
import curses
import datetime
import copy

class ShortRun(object):
  def __init__(self):
    self.error_tests = {}
    self.stdscr = curses.initscr()
    curses.echo()
    self.current_string = ('Roster Unittest Environment\n'
                       '---------------------------\n\n')
    self.stat_string = ''
    self.init_time = datetime.datetime.now()

  def RunCommand(self, command):
    handle = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    handle.wait()
    contents = str(handle.stderr.read())
    return_code = handle.returncode

    return (return_code, contents)

  def RunTests(self, window):
    unittests = glob.glob('*test.py')
    try:
      skiplist = open('skip', 'r').read().split()
    except:
      skiplist = []

    for i, unittest in enumerate(unittests):
      if( unittest in sys.argv or unittest in skiplist ):
        continue # Blacklist
      timediff = datetime.datetime.now() - self.init_time
      self.stat_string = ('---------------------------\n'
                         'Current Test: %s (%s/%s)\n'
                         'Time elapsed: %s\n'
                         'Failed tests: %s\n\n'
                         'Detailed errors will show after exiting.' % (
          unittest, i + 1, len(unittests) - len(sys.argv) - len(skiplist),
          str(timediff),
          ', '.join(self.error_tests.keys())))
      window.clear()
      window.addstr('%s\n\n%s' % (self.current_string,
                                self.stat_string))
      window.refresh()
      return_code, contents = self.RunCommand('python %s' % unittest)
      
      if( return_code == 0 ):
        self.current_string = '%s.' % self.current_string
      else:
        self.current_string = '%sF' % self.current_string
        self.error_tests[unittest] = contents
      timediff = datetime.datetime.now() - self.init_time
      self.stat_string = ('---------------------------\n'
                         'Current Test: %s (%s/%s)\n'
                         'Time elapsed: %s\n'
                         'Failed tests: %s\n\n'
                         'Detailed errors will show after exiting.' % (
          unittest, i + 1, len(unittests) - len(sys.argv) - len(skiplist),
          str(timediff),
          ', '.join(self.error_tests.keys())))
      window.clear()
      window.addstr('%s\n\n%s' % (self.current_string,
                                  self.stat_string))
      window.refresh()
    self.stat_string = '%s%s' % (self.stat_string,
                                 '\n\nPress any key to exit...')
    window.clear()
    window.addstr('%s\n\n%s' % (self.current_string,
                                self.stat_string))
    window.refresh()

    window.getch()

if( __name__ == '__main__' ):
  name = sys.argv.pop(0)
  if( len(sys.argv) > 0 ):
    if( sys.argv[0] == '--help' ):
      sys.argv.pop(0)
      print("To skip tests add the names of the tests to a file called 'skip' "
            "in this directory. Also they can be appended as arguments to the "
            "end of %s." % name)
      exit(0)
  shortrun_instance = ShortRun()
  try:
    curses.wrapper(shortrun_instance.RunTests)
    for error in shortrun_instance.error_tests:
      print '---------------------------'
      print error
      print shortrun_instance.error_tests[error]
      print '---------------------------'
    print "Failed %s tests: %s" % (
        len(shortrun_instance.error_tests),
        ', '.join(shortrun_instance.error_tests.keys()))

  except KeyboardInterrupt:
    for error in shortrun_instance.error_tests:
      print '---------------------------'
      print error
      print shortrun_instance.error_tests[error]
      print '---------------------------'
    print "Failed %s tests: %s" % (
        len(shortrun_instance.error_tests),
        ', '.join(shortrun_instance.error_tests.keys()))
    print "Tests canceled."
