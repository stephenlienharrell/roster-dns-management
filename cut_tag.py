#!/usr/bin/python

# Copyright (c) 2009, Purdue University
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

"""List reserved word tool for roster"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = "1.0"


import os
import time
import sys
import getpass
import subprocess
import shutil

from optparse import OptionParser

def main(args):
  """Collects command line arguments.

  Inputs:
    args: list of arguments from the command line
  """
  DEBUG = False

  parser = OptionParser()

  parser.add_option('-v', '--major_version', action='store', dest='major_version',
                    help='Major Version', metavar='<version>',
                    default=None)
  parser.add_option('-m', '--minor_version', action='store', dest='minor_version',
                    help='Minor Version', metavar='<version>',
                    default=None)
  parser.add_option('-b', '--beta-version', action='store', dest='beta_version',
                    help='Minor Version', metavar='<version>',
                    default=None)
  parser.add_option('-d', '--debug', action='store_false', dest='debug_flag',
                    help='Print all output from Sphinx and svn propset',
                    metavar='<version>')

  (globals()["options"], args) = parser.parse_args(args)

  if( options.minor_version is None or options.major_version is None ):
    print "Must specify minor and major versions."
    sys.exit(1)

  current_version = '%s.%s' % (options.major_version, options.minor_version)

  if( options.beta_version is not None ):
    current_version = '%sb%s' % (current_version, options.beta_version)

  if( options.debug_flag is not None ):
    DEBUG = True

  while( True ):
    yes_no = raw_input('Is version %s correct? [Y/n] ' % current_version)
    if( not yes_no ):
      yes_no = 'y'
    if( yes_no.lower() not in ['y', 'n'] ):
      continue
    if( yes_no.lower() == 'n' ):
      print 'Exiting...'
      sys.exit(0)
    else:
      break

  if( os.path.exists('trunk') and os.path.exists('tags') ):
    # this is hackish
    os.system('svn copy trunk tags/release-%s' % current_version)
    os.system('perl -pi -e s/#TRUNK#/%s/ tags/release-%s/*/*' %
        (current_version, current_version))
    os.system('perl -pi -e s/#TRUNK#/%s/ tags/release-%s/*/*/*' %
        (current_version, current_version))
    os.system(
        'perl -pi -e "s/Current Release/%s release-%s/g" '
        'tags/release-%s/*/ChangeLog' % (time.strftime('%Y-%m-%d'),
                                         current_version, current_version))
    os.system(
        'perl -pi -e "s/Current Release/Current Release\n\n%s release-%s/g" '
        'trunk/*/ChangeLog' %  (time.strftime('%Y-%m-%d'),
                                current_version))

    if( CheckDepencies(DEBUG) ):
      GenerateAllDocumentation(current_version, DEBUG)

  else:
    print 'No tags or trunk directory found, run this in the base directory'
    sys.exit(1)

def SystemProcess(arg_list, DEBUG):
  """A connivence function for subprocess.Popen. 

  Inputs: 
  arg_list: List of arguments to supply Popen with.
    DEBUG: Boolean to print out subprocess output or not.

  Outputs:
    The return code of running the supplied command
  """

  system_command = subprocess.Popen(arg_list, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.STDOUT)
  output = system_command.communicate()[0].strip('\n')

  if( DEBUG ):
    print output

  return system_command.returncode

def CheckDepencies(DEBUG):  
  """Checks to make sure required programs for documentation generation
  are installed.

  Outputs: 
    True if all programs are present, False otherwise.
  """

  print 'Checking dependencies'

  programs = ['sphinx-apidoc', 'svn', 'sqlt-graph', 'convert']
  for program in programs:
    command = ['which', program]

    if( SystemProcess(command, DEBUG) != 0 ):
      print '%s is not installed' % progam
      print 'Unable to generate documentation, now exiting/'
      return False

  print 'Passed dependency check'
  return True

def SetMimeTypes(DEBUG):
  """Recursively sets the svn:mime-type of all files to the correct type for 
  all files in a given directory, and all files in any subdirectories

  Note: This function is more or less tailored to be called by AddFilesToSVN,
  so unless you're setting up the pwd the same way AddFilesToSVN is, don't 
  call this function on 'your own.'

  Inputs: 
    DEBUG: Boolean to print out subprocess output or not.
  """
  directory = os.getcwd()

  #Found these on the internet, I'm sure there are some more that I could 
  #remove, but they're not hurting anyone for now    
  svn_type_dict = { 'bmp' : 'svn:mime-type image/bmp',
                  'css' : 'svn:mime-type text/css',                
                  'gif' : 'svn:mime-type image/gif',                
                  'html' : 'svn:mime-type text/html',
                  'jpg' : 'svn:mime-type image/jpeg',
                  'js' : 
                  'svn:mime-type application/x-javascript',               
                  'pbm' : 'svn:mime-type image/x-portable-bitmap',
                  'pdf' : 'svn:mime-type application/pdf',
                  'pgm' : 'svn:mime-type image/x-portable-graymap',
                  'png' : 'svn:mime-type image/png',
                  'pnm' : 
                  'svn:mime-type image/x-portable-anymap',               
                  'ppm' : 
                  'svn:mime-type image/x-portable-pixmap',               
                  'ps' : 
                  'svn:mime-type application/postscript',                
                  'rtf' : 'svn:mime-type application/rtf',
                  'sh' : 'svn:mime-type application/x-sh',
                  'svg' : 'svn:mime-type image/svg+xml',
                  'tar' : 'svn:mime-type application/x-tar',
                  'tex' : 'svn:mime-type application/x-tex',
                  'tgz' : 'svn:mime-type application/x-compressed',
                  'tif' : 'svn:mime-type image/tiff',
                  'txt' : 'svn:mime-type text/plain',                
                  'xhtml' : 'svn:mime-type application/xhtml+xml',          
                  'xml' : 'svn:mime-type text/xml',
                  'xsl' : 'svn:mime-type text/xml',
                  'zip' : 'svn:mime-type application/zip'}

  if( 'svn' not in directory ):
    for file_or_folder in os.listdir(os.getcwd()):
          if( os.path.isfile(file_or_folder) ):
            if( 'svn' not in file_or_folder ):
              try:
                extension = file_or_folder.split('.').pop()

                try:
                  arg3 = svn_type_dict[extension].split(' ')[0]
                  arg4 = svn_type_dict[extension].split(' ')[1]
                  SystemProcess(['svn', 'propset', arg3, arg4, file_or_folder], 
                                DEBUG)

                #If we don't have the extension in the dictionary,
                #that's probably fine, like if there was a main.c 
                #in there somehow, having that as plaintext is fine
                except KeyError:
                  arg3 = svn_type_dict['txt'].split(' ')[0]
                  arg4 = svn_type_dict['txt'].split(' ')[1]
                  SystemProcess(['svn', 'propset', arg3, arg4, file_or_folder], 
                                DEBUG)  

              #File is extensionless, plaintext will be fine
              except IndexError:
                  arg3 = svn_type_dict['txt'].split(' ')[0]
                  arg4 = svn_type_dict['txt'].split(' ')[1]
                  SystemProcess(['svn', 'propset', arg3, arg4, file_or_folder], 
                                DEBUG)   
          else:
            os.chdir(os.path.join(os.getcwd(), file_or_folder))
            SetMimeTypes(DEBUG)

            #If the recursive call moved my path, I'll revert back to the
            #original directory that I was in before the recursive call
            os.chdir(directory)
  
  os.chdir(directory)

def GenerateSchemaImage(release_number, DEBUG):
  """Generates a .png image file of the Database Schema defined in
  roster-core/roster_core/embedded_files.py

  NOTE: This must be run from the code path's root directory.

  Inputs: 
    release_number: The current release number, ex 1.3
    DEBUG: Boolean to print out subprocess output or not.
  """

  print 'Generating MySQL Database Schema Image'

  SystemProcess(['cp', 
                 'tags/release-%s/roster-core/'
                 'roster_core/embedded_files.py' % str(release_number),
                 'embedded_files.py'], DEBUG)

  input_file = open('embedded_files.py', 'r')
  try:
    contents = input_file.read()
    os.remove('embedded_files.py')

    #Parsing the MySQL Database schema
    contents = contents[contents.index('SCHEMA_FILE'):]
    contents = contents.strip('SCHEMA_FILE = """').strip('\n').strip('"""')
  except ValueError:
    print 'embedded_files.py doesn\'t contain SCHEMA_FILE?'
    raise
  finally:
    input_file.close()

  output_file = open('db_schema.sql', 'w')
  try:
    output_file.write(contents)
  finally:
    output_file.close()

  #Generating schema pictures
  SystemProcess(['sqlt-graph', '-f', 'MySQL', '-o', 'db_schema.png', '-c', 
                 '--show-constraints', '--show-datatypes', '-t', 
                 'png', 'db_schema.sql'], DEBUG)
  SystemProcess(['convert', '-size', '800x800', 'db_schema.png', 
                 '-resize', '800x800', 'thumbnail.png'], DEBUG)

  os.rename('db_schema.sql', 'wiki/DatabaseSchema/db_schema_%s.sql' % str(release_number))
  os.rename('db_schema.png', 'wiki/DatabaseSchema/db_schema_%s.png' % str(release_number))
  os.rename('thumbnail.png', 'wiki/DatabaseSchema/thumbnail_%s.png' % str(release_number))  

def UpdateWikiPage(release_number):
  """Updates the Documentation Wiki Index page to show the correct latest
  documentation, and correctly append what used to be the latest doc, to the 
  end of the list of old documentations.

  NOTE: This must be run from the code path's root directory.

  Inputs: 
  release_number: The current release number, ex 1.3
  """

  print 'Updating Wiki'
  os.chdir(os.path.join(os.getcwd(), 'wiki'))

  doc_lines = []
  doc_page_handle = open('DeveloperDocumentation.wiki', 'r')
  try:
    doc_lines = doc_page_handle.readlines()
  finally:
    doc_page_handle.close()

  new_lines = [ '----',
               '==Version %s==' % str(release_number), 
               '===Database Schema===',

               '[http://roster-dns-management.googlecode.com/svn/wiki/'
               'DatabaseSchema/thumbnail_%s.png]' % str(release_number),

               ' * [http://roster-dns-management.googlecode.com/svn/wiki/'
               'DatabaseSchema/db_schema_%s.png '
               'Full Size Schema Image]' % str(release_number),

               ' * [http://roster-dns-management.googlecode.com/svn/wiki/'
               'DatabaseSchema/db_schema_%s.sql '
               'Schema SQL File]' % str(release_number),

               '\n===Roster API Documentation===',

               ' * [http://roster-dns-management.googlecode.com/svn/tags/'
               'release-%s/roster-core/docs/html/index.html '
               'Roster Core]' % str(release_number),

               ' * [http://roster-dns-management.googlecode.com/svn/tags/'
               'release-%s/roster-config-manager/docs/html/index.html '
               'Roster Config Manger]' % str(release_number),
               ' * [http://roster-dns-management.googlecode.com/svn/tags/'
               'release-%s/roster-server/docs/html/index.html '
               'Roster Server]' % str(release_number),
               ' * [http://roster-dns-management.googlecode.com/svn/tags/'
               'release-%s/roster-user-tools/docs/html/index.html '
               'Roster User Tools]\n' % str(release_number)]

  old_lines_start = doc_lines.index('=Latest Documentation=\n') + 1
  old_lines_end = doc_lines.index('<br />\n')

  old_lines = doc_lines[old_lines_start:old_lines_end]

  for i in range(old_lines_end - old_lines_start):
    doc_lines.pop(old_lines_start)

  for line in reversed(old_lines):
    doc_lines.insert(7, '%s\n' % line.rstrip('\n'))

  for line in reversed(new_lines):
    doc_lines.insert(2, '%s\n' % line.rstrip('\n'))

  doc_page_handle = open('DeveloperDocumentation.wiki', 'w')
  try:
    doc_page_handle.writelines(doc_lines)
  finally:
    doc_page_handle.close()

def GenerateSphinx(release_number, DEBUG):
  """Generates Sphinx HTML Documentation.

  NOTE: This must be run from the code path's root directory.

  Inputs:
  release_number: The current release number, ex 1.3
  DEBUG: Boolean to print out subprocess output or not.
  """

  #Changing into the tags folder
  os.chdir(os.path.join(os.getcwd(), 'tags', 'release-%s' % str(release_number)))

  for directory in os.listdir(os.getcwd()):
    if( 'roster' in directory ):
      print 'Generating HTML Documenation for %s ' % directory

      #moving into roster-core for example
      os.chdir(os.path.join(os.getcwd(), directory))

      #this block turns roster-core into Roster Core
      dir_words = directory.split('-')
      for i, word in enumerate(dir_words):
        dir_words[i] = '%s%s' % (word[0].capitalize(), word[1:])

      arg1 = ' '.join(dir_words) #arg1 = "Roster Core"
      arg2 = 'v%s' % str(release_number) #arg2 = "v0.91"
      arg3 = directory.replace('-', '_') #arg3 = "roster_core"

      sphinx_commands =  [['sphinx-apidoc', '--full', '--force', '-o', 'docs', 
      '--doc-project=%s' % arg1, '--doc-author=Purdue University',  
      '--doc-version=%s' % arg2, '%s' % arg3], ['make', 'html']]

      #generating the sphinx make file
      SystemProcess(sphinx_commands[0], DEBUG)

      #changing to the docs folder and running make
      os.chdir(os.path.join(os.getcwd(), 'docs'))
      SystemProcess(sphinx_commands[1], DEBUG)

      os.rename('_build/html', 'html')
      shutil.rmtree('_build')
      shutil.rmtree('_static')
      shutil.rmtree('_templates')

      #emulating rm *.*
      for file_or_folder in os.listdir(os.getcwd()):
        if( 'html' not in file_or_folder ):
          if( os.path.isfile(file_or_folder) ):
            os.remove(file_or_folder)
          else:
            shutil.rmtree(file_or_folder)

      if( len(os.listdir(os.getcwd())) > 1 ):
        print '%s' % (
          'Error, more files than there should be here.\n'
          'Probably not a huge problem, '
          'just some Sphinx build stuff laying around.')

      os.chdir(os.path.join(os.getcwd(), '..', '..'))

def AddFilesToSVN(root_directory, release_number, DEBUG):
  """Adds files to version control and changes their svn:mime-type so that they
  correctly show up on the internet instead of downloading.

  Inputs:
  release_number: The release number. ex 1.3
  DEBUG: Boolean to print out subprocess output or not.
  """

  print 'Changing MIME Types'
  os.chdir(os.path.join(root_directory, 'tags', 'release-%s' % str(release_number)))

  for directory in os.listdir(os.getcwd()):
    if( 'roster' in directory ):
      current_dir = os.getcwd()

      os.chdir(os.path.join(os.getcwd(), directory))
      SystemProcess(['svn', 'add', 'docs'], DEBUG)
      SetMimeTypes(DEBUG)

      os.chdir(current_dir)

  os.chdir(os.path.join(root_directory, 'wiki', 'DatabaseSchema'))

  for file_name in os.listdir(os.getcwd()):
    if( 'svn' not in file_name ):
      SystemProcess(['svn', 'add', file_name], DEBUG)
  SetMimeTypes(DEBUG)

def GenerateAllDocumentation(release_number, DEBUG):
  """Auto-generates HTML documentation for the latest release of Roster using 
  Sphinx, generates a MySQL Database Schema image, and updates the Wiki
  documentation page.

  Inputs:
    DEBUG: Boolean to print out subprocess output or not.
  """

  release_number = str(release_number)
  root_directory = os.getcwd()

  GenerateSphinx(release_number, DEBUG)
  os.chdir(root_directory)

  UpdateWikiPage(release_number)
  os.chdir(root_directory)

  GenerateSchemaImage(release_number, DEBUG)
  os.chdir(root_directory)

  AddFilesToSVN(root_directory, release_number, DEBUG)
  os.chdir(root_directory)

  print 'Finished'

if __name__ == "__main__":
    main(sys.argv[1:])
