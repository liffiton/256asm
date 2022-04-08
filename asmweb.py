#!/usr/bin/env python3
"""
CS256 ISA Assembler: Web interface
Author: Mark Liffiton
"""

import os
import sys
import zipfile

from assembler import Assembler, AssemblerException
from bottle import post, request, route, run, static_file, template


# Parse/check commandline arguments
if len(sys.argv) < 2:
    print("Usage: asmweb.py CONFIGFILE [PORT]", file=sys.stderr)
    sys.exit(1)

configfile = sys.argv[1]
if not os.path.exists(configfile):
    print("File not found: {}".format(configfile), file=sys.stderr)
    print("Usage: asmweb.py CONFIGFILE [PORT]", file=sys.stderr)
    sys.exit(1)
assembler = Assembler(configfile)

if len(sys.argv) > 2:
    port = int(sys.argv[2])
else:
    port = 8080


@route('/')
def index():
    return template(
        'index',
        name=assembler.name,
        instructions=assembler.instructions,
        reg_prefix=assembler.reg_prefix
    )


@route('/static/<filename>')
def static(filename):
    return static_file(filename, root='static/')


@route('/sample.asm')
def sample():
    return static_file(str(assembler.samplefile), root='.')


@route('/dl/<filename>')
def download(filename):
    zipfilename = '{}2bin.zip'.format(assembler.name)
    assert(filename == zipfilename)
    with zipfile.ZipFile(zipfilename, 'w') as zip:
        zip.write('asm2bin.py')
        zip.write('assembler.py')
        zip.write(assembler.configfile)
        zip.write(assembler.samplefile)
        zip.write('README.md')
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
        out['bin'] = " ".join("{:04x}".format(word) for word in instructions_bin)

        upperbytes = []
        lowerbytes = []
        for word in instructions_bin:
            upperbytes.append(word // 256)
            lowerbytes.append(word % 256)

        out['upper'] = " ".join("{:02x}".format(byte) for byte in upperbytes)
        out['lower'] = " ".join("{:02x}".format(byte) for byte in lowerbytes)

    except AssemblerException as e:
        out['error'] = {key: getattr(e, key) for key in ['msg', 'data', 'lineno', 'inst']}

    return out


# Launch the server for external access
run(host='0.0.0.0', port=port)
