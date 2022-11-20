#!/usr/bin/env python
import os
import re
import pprint
import sys
import subprocess as sp
from os.path import basename
from subprocess import *
from optparse import OptionParser

def parseChapters(filename):
  chapters = []
  command = [ "ffmpeg", '-i', filename]
  output = ""
  m = None
  title = None
  chapter_match = None
  try:
    # ffmpeg requires an output file and so it errors
    # when it does not get one so we need to capture stderr,
    # not stdout.
    output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
  except CalledProcessError as e:
    output = e.output

  num = 1

  for line in iter(output.splitlines()):
    x = re.match(r".*title.*: (.*)", line)
    print("x:")
    pprint.pprint(x)

    print("title:")
    pprint.pprint(title)

    if x == None:
      m1 = re.match(r".*Chapter #(\d+:\d+): start (\d+\.\d+), end (\d+\.\d+).*", line)
      title = None
    else:
      title = x.group(1)

    if m1 != None:
      chapter_match = m1

    print("chapter_match:")
    pprint.pprint(chapter_match)

    if title != None and chapter_match != None:
      m = chapter_match
      pprint.pprint(title)
    else:
      m = None

    if m != None:
      chapters.append({ "name": str(num) + " - " + title, "start": m.group(2), "end": m.group(3)})
      num += 1

  return chapters

def getChapters():
  parser = OptionParser(usage="usage: %prog [options] filename", version="%prog 1.0")
  parser.add_option("-f", "--file",dest="infile", help="Input File", metavar="FILE")
  parser.add_option("-e", "--encode", help="Frame accurate splitting by reencoding", action="store_true", dest="encode")
  (options, args) = parser.parse_args()
  print(options)
  if not options.infile:
    parser.error('Filename required')
  chapters = parseChapters(options.infile)
  fbase, fext = os.path.splitext(options.infile)
  path, file = os.path.split(options.infile)
  newdir, fext = os.path.splitext( basename(options.infile) )

  os.mkdir(path + "/" + newdir)

  for chap in chapters:
    chap['name'] = chap['name'].replace('/',':')
    chap['name'] = chap['name'].replace("'","\'")
    print("start:" +  chap['start'])
    chap['outfile'] = path + "/" + newdir + "/" + re.sub("[^-a-zA-Z0-9_.():' ]+", '', chap['name']) + fext
    chap['origfile'] = options.infile
    print(chap['outfile'])
  return chapters, options.encode

def convertChapters(chapters, encode):
  for chap in chapters:
    print("start:" +  chap['start'])
    print(chap)
    if encode:
        command = [
            "ffmpeg", '-i', chap['origfile'],
            '-ss', chap['start'],
            '-to', chap['end'],
            '-c:v', 'libx264',
            chap['outfile']]
    else:
        command = [
        "ffmpeg", '-i', chap['origfile'],
        '-vcodec', 'copy',
        '-acodec', 'copy',
        '-ss', chap['start'],
        '-to', chap['end'],
        chap['outfile']]
    output = ""
    try:
      # ffmpeg requires an output file and so it errors
      # when it does not get one
      output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
    except CalledProcessError as e:
      output = e.output
      raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

if __name__ == '__main__':
  chapters, encode = getChapters()
  convertChapters(chapters, encode)
