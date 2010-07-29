#!/usr/bin/env python

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


import copy

def Parse(char_list):
  """Parses exploded isc named.conf portions.

  Inputs:
    char_list: List of isc file parts

  Outputs:
    dict: fragment or full isc file dict
    Recursive dictionary of isc file, dict values can be of 3 types,
    dict, string and bool. Boolean values are always true. Booleans are false
    if key is absent. Booleans represent situations in isc files such as:
      acl "registered" { 10.1.0/32; 10.1.1:/32;}}

    Example:

    {'stanza1 "new"': 'test_info', 'stanza1 "embedded"': {'acl "registered"':
        {'10.1.0/32': True, '10.1.1/32': True}}}
  """
  index = 0
  dictionary_fragment = {}
  new_char_list = copy.deepcopy(char_list)
  if( type(new_char_list) == str ):
    return new_char_list
  if( type(new_char_list) == dict ):
    return new_char_list
  while( index < len(new_char_list) ):
    if( len(new_char_list) > index + 1 and new_char_list[index + 1] == '{' ):
      key = new_char_list.pop(index)
      skip, dict_value = Clip(new_char_list[index:])
      dictionary_fragment[key] = copy.deepcopy(Parse(dict_value))
      index += skip
    else:
      if( len(new_char_list[index].split()) == 1 and '{' not in new_char_list ):
        for item in new_char_list:
          if( item in [';'] ):
            continue
          dictionary_fragment[item] = True
      elif( len(new_char_list[index].split()) == 2 ):
        dictionary_fragment[new_char_list[index].split()[0]] = new_char_list[
            index].split()[1]
        index += 1
      index += 1
  return dictionary_fragment

def Clip(char_list):
  """Clips char_list to individual stanza.

  Inputs:
    char_list: partial of char_list from Parse

  Outputs:
    tuple: (int: skip to char list index, list: shortened char_list)
  """
  assert(char_list[0] == '{')
  char_list.pop(0)
  skip = 0
  for index, item in enumerate(char_list):
    if( item == '{' ):
      skip += 1
    elif( item == '}' and skip == 0 ):
      return (index, char_list[:index])
    elif( item == '}' ):
      skip -= 1
  raise Exception("Invalid brackets.")

def Explode(isc_string):
  """Explodes isc file into relevant tokens.

  Inputs:
    isc_string: String of isc file

  Outputs:
    list: list of isc file tokens delimited by brackets and semicolons
      ['stanza1 "new"', '{', 'test_info', ';', '}']
  """
  str_array = []
  temp_string = []
  prev_char = ''
  for char in isc_string:
    if( prev_char == '}' and char != ';' ):
      str_array.append(';')
      prev_char = ';'
    if( char in ['\n'] ):
      continue
    if( char in ['{', '}', ';'] ):
      if( ''.join(temp_string).strip() == '' ):
        str_array.append(char)
      else:
        str_array.append(''.join(temp_string).strip())
        str_array.append(char)
        temp_string = []
    else:
      temp_string.append(char)
    prev_char = char
  return str_array

def ScrubComments(isc_string):
  """Clears comments from an isc file

  Inputs:
    isc_string: string of isc file
  Outputs:
    string: string of scrubbed isc file
  """
  isc_list = []
  for line in isc_string.split('\n'):
    if( line.strip().startswith(('#', '//')) ):
      continue
    else:
      isc_list.append(line.split('#')[0].split('//')[0].strip())

  return '\n'.join(isc_list)

def MakeNamedDict(named_string):
  """Makes a more organized named specific dict from parsed_dict

  Inputs:
    named_string: string of named file

  Outputs:
    dict: organized dict with keys views options and acls
    {'acls': {'acl1': ['10.1.0/32', '10.1.1/32']},
     'views': {'view1': {'zones': {'test_zone': {'file': '/path/to/zonefile',
                                                 'type': 'master',
                                                'options': 'zone_options'}},
                         'options': 'view_options'}}}
  """
  named_string = ScrubComments(named_string)
  parsed_dict = copy.deepcopy(Parse(Explode(named_string)))
  named_data = {'acls': {}, 'views': {}, 'options': {}}
  for key in parsed_dict:
    if( key.startswith('acl') ):
      named_data['acls'][key.split()[1]] = []
      for cidr in parsed_dict[key]:
        named_data['acls'][key.split()[1]].append(cidr)
    elif( key.startswith('view') ):
      view_name = key.split()[1].strip('"').strip()
      named_data['views'][view_name] = {'zones': {}, 'options': {}}
      for view_key in parsed_dict[key]:
        if( view_key.startswith('zone') ):
          zone_name = view_key.split()[1].strip('"').strip()
          named_data['views'][view_name]['zones'][zone_name] = (
              {'options': {}, 'file': ''})
          for zone_key in parsed_dict[key][view_key]:
            if( zone_key.startswith('file') ):
              named_data['views'][view_name]['zones'][zone_name]['file'] = (
                  parsed_dict[key][view_key][zone_key].strip('"').strip())
            elif( zone_key.startswith('type') ):
              named_data['views'][view_name]['zones'][zone_name]['type'] = (
                  parsed_dict[key][view_key][zone_key].strip('"').strip())
            else:
              named_data['views'][view_name]['zones'][zone_name]['options'][
                  zone_key] = parsed_dict[key][view_key][zone_key]
        else:
          named_data['views'][view_name]['options'][view_key] = (
              parsed_dict[key][view_key])
    else:
      named_data['options'][key] = parsed_dict[key]

  return named_data


def MakeISC(isc_dict):
  """Outputs an isc formatted file string from a dict

  Inputs:
    isc_dict: a recursive dictionary to be turned into an isc file
              (from Parse)

  Outputs:
    str: string of isc file without indentation
  """
  if( type(isc_dict) == str ):
    return isc_dict
  isc_list = []
  for option in isc_dict:
    if( type(isc_dict[option]) == bool ):
      isc_list.append('%s;' % option)
    elif( type(isc_dict[option]) == str):
      isc_list.append('%s %s;' % (option, isc_dict[option]))
    elif( type(isc_dict[option]) == dict ):
      isc_list.append('%s { %s };' % (option, MakeISC(isc_dict[option])))
  return '\n'.join(isc_list)

def MakeZoneViewOptions(named_data):
  """Makes zone and view data into strings to load into database.

  Inputs:
    named_data: named dict from MakeNamedDict

  Outputs:
    dict: dict with keys {'views': {}, 'zones': {}}
  """
  options_dict = {'views':{}, 'zones': {}}
  for view in named_data['views']:
    options_dict['views'][view] = MakeISC(named_data['views'][view]['options'])
    for zone in named_data['views'][view]['zones']:
      options_dict['zones'][zone] = MakeISC(named_data['views'][view]['zones'][
          zone]['options'])
  return options_dict

def DumpNamedHeader(named_data):
  """This function dumps the named header from a named_data dict

  Inputs:
    named_data: named dict from MakeNamedDict

  Outputs:
    str: stirng of named header
  """
  return MakeISC(named_data['options'])
