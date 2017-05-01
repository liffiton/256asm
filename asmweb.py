#!/usr/bin/env python
"""
CS256 ISA Assembler: Web interface
Author: Mark Liffiton
"""

from __future__ import print_function

import os
import sys
import zipfile

from assembler import Assembler, AssemblerException
from bottle import post, request, route, run, static_file, template


# Parse/check commandline arguments
if len(sys.argv) < 2:
    print("Usage: asmweb.py CONFIGFILE [IP]", file=sys.stderr)
    sys.exit(1)
configfile = sys.argv.pop(1)  # remove it because web.py uses argv
if not os.path.exists(configfile):
    print("File not found: %s" % configfile, file=sys.stderr)
    print("Usage: asmweb.py CONFIGFILE [IP]", file=sys.stderr)
    sys.exit(1)
assembler = Assembler(configfile)


@route('/')
def index():
    return template('index', name=assembler.name)


@route('/static/<filename>')
def static(filename):
    return static_file(filename, root='static/')


@route('/sample.asm')
def sample():
    return static_file(assembler.samplefile, root='.')


@route('/dl/<filename>')
def download(filename):
    zipfilename = '%s2bin.zip' % assembler.name
    assert(filename == zipfilename)
    with zipfile.ZipFile(zipfilename, 'w') as zip:
        zip.write('asm2bin.py')
        zip.write('assembler.py')
        zip.write(assembler.configfile)
        zip.write(assembler.samplefile)
    return static_file(zipfilename, root='.', download=True)


@post('/assemble/')
def assemble():
    asm = request.body.read().decode()
    lines = asm.split('\n')

    out = {}
    out['messages'] = []

    assembler.register_info_callback(out['messages'].append)

    try:
        (instructions, instructions_bin) = assembler.assemble_lines(lines)
        out['code'] = assembler.prettyprint_assembly(instructions, instructions_bin, colorize=True)

        upperbytes = []
        lowerbytes = []
        for word in instructions_bin:
            upperbytes.append(word // 256)
            lowerbytes.append(word % 256)

        out['upper'] = " ".join("%02x" % byte for byte in upperbytes)
        out['lower'] = " ".join("%02x" % byte for byte in lowerbytes)

    except AssemblerException as e:
        out['error'] = (e.msg, e.data, e.inst)

    return out


# Launch the server for external access
run(host='0.0.0.0')
