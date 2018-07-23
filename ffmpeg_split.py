#!/usr/bin/env python
import os
import re
import subprocess as sp
from optparse import OptionParser


def parse_chapters(filename):
    chapters = []
    command = ["ffmpeg", '-i', filename]
    output = ""
    m = None
    title = None
    chapter_match = None
    try:
        # ffmpeg requires an output file and so it errors
        # when it does not get one so we need to capture stderr,
        # not stdout.
        output = sp.check_output(
            command,
            stderr=sp.STDOUT,
            universal_newlines=True
        )
    except sp.CalledProcessError as err:
        output = err.output

    num = 1

    for line in iter(output.splitlines()):
        x = re.match(r".*title.*: (.*)", line)

        if not x:
            m1 = re.match(
                r".*Chapter #(\d+:\d+): start (\d+\.\d+), end (\d+\.\d+).*",
                line
            )
            title = None
        else:
            title = x.group(1)

        if m1:
            chapter_match = m1

        if title and chapter_match:
            m = chapter_match
        else:
            m = None

        if m:
            chapters.append({
                "num": num,
                "title": title,
                "start": m.group(2),
                "end": m.group(3)
            })
            num += 1

    return chapters


def get_chapters(infile):
    _chapters = parse_chapters(infile)
    _, fext = os.path.splitext(infile)
    path = os.path.split(infile)
    newdir, fext = os.path.splitext(os.path.basename(infile))

    os.mkdir(path + "/" + newdir)

    leading_zeros_size = len(str(len(_chapters)))
    for chap in _chapters:
        chap['title'] = chap['title'].replace('/', ':')
        chap['title'] = chap['title'].replace("'", "\'")

        outfilename = "{} - {}".format(
            str(chap['num']).zfill(leading_zeros_size),
            chap['title']
        )
        chap['outfile'] = "{}/{}/{}.{}".format(
            path,
            newdir,
            re.sub("[^-a-zA-Z0-9_.():' ]+", '', outfilename),
            fext
        )
        chap['origfile'] = infile
    return _chapters


def convert_chapters(chapters):
    for chap in chapters:
        command = [
            "ffmpeg", '-i', chap['origfile'],
            '-vcodec', 'copy',
            '-acodec', 'copy',
            '-metadata',
            'title='+chap['title'],
            '-metadata',
            'track='+str(chap['num']),
            '-ss', chap['start'],
            '-to', chap['end'],
            chap['outfile']]
        try:
            # ffmpeg requires an output file and so it errors
            # when it does not get one
            sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
        except sp.CalledProcessError as err:
            raise RuntimeError(
                "Command '{}' return with error (code {}): {}".format(
                    err.cmd, err.returncode, err.output
                )
            )


if __name__ == '__main__':
    PARSER = OptionParser(
        usage="usage: %prog [options] filename",
        version="%prog 1.0"
    )
    PARSER.add_option(
        "-f", "--file", dest="infile", help="Input File", metavar="FILE"
    )
    OPTIONS, _ = PARSER.parse_args()
    if not OPTIONS.infile:
        PARSER.error('Filename required')

    CHAPTERS = get_chapters(OPTIONS.infile)
    convert_chapters(CHAPTERS)
