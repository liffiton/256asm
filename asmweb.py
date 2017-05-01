#!/usr/bin/env python
"""
CS256 ISA Assembler: Web interface
Author: Mark Liffiton
"""

from __future__ import print_function

import json
import os
import sys
import zipfile

from assembler import Assembler, AssemblerException
import web


# A bit of dependency injection
#  Thanks: https://www.electricmonk.nl/log/2015/03/06/dependency-injection-in-web-py/
# This seems overcomplicated...
class Injector:
    def __init__(self, assembler):
        self.assembler = assembler

    def __call__(self, handler):
        web.ctx.assembler = self.assembler
        return handler()


urls = (
    '/assemble/', 'asm2bin',
    '/dl/.*', 'download',
    '/sample.asm', 'sample',
    '/', 'Main',
)


class Main:
    def GET(self):
        name = web.ctx.assembler.name
        return web.template.render('templates/').index(name)


class sample:
    def GET(self):
        samplefile = web.ctx.assembler.samplefile
        return open(samplefile).read()


class download:
    def GET(self):
        name = web.ctx.assembler.name
        with zipfile.ZipFile('%s2bin.zip' % name, 'w') as zip:
            zip.write('asm2bin.py')
            zip.write('assembler.py')
            zip.write(web.ctx.assembler.configfile)
            zip.write(web.ctx.assembler.samplefile)
        return open('%s2bin.zip' % name, 'rb').read()


class asm2bin:
    def POST(self):
        lines = web.data().split('\n')

        out = {}
        out['messages'] = []

        a = web.ctx.assembler
        a.register_info_callback(out['messages'].append)

        try:
            (instructions, instructions_bin) = a.assemble_lines(lines)
            out['code'] = a.prettyprint_assembly(instructions, instructions_bin, colorize=True)

            upperbytes = []
            lowerbytes = []
            for word in instructions_bin:
                upperbytes.append(word // 256)
                lowerbytes.append(word % 256)

            out['upper'] = " ".join("%02x" % byte for byte in upperbytes)
            out['lower'] = " ".join("%02x" % byte for byte in lowerbytes)

        except AssemblerException as e:
            out['error'] = (e.msg, e.data, e.inst)

        web.header('Content-Type', 'application/json')
        return json.dumps(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: asmweb.py CONFIGFILE [IP]", file=sys.stderr)
        sys.exit(1)
    configfile = sys.argv.pop(1)  # remove it because web.py uses argv
    if not os.path.exists(configfile):
        print("File not found: " + configfile, file=sys.stderr)
        print("Usage: asmweb.py CONFIGFILE [IP]", file=sys.stderr)
        sys.exit(1)
    assembler = Assembler(configfile)

    app = web.application(urls, globals())
    app.add_processor(Injector(assembler))
    app.run()
