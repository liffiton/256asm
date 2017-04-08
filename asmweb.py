#!/usr/bin/env python

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
        data = web.data()
        lines = data.split('\n')

        web.header('Content-Type', 'application/json')

        out = {}
        out['messages'] = []

        def getmsg(msgtuple):
            out['messages'].append(msgtuple)

        a = web.ctx.assembler
        a.register_info_callback(getmsg)

        try:
            (instructions, instructions_bin) = a.assemble_lines(lines)
            out['code'] = a.prettyprint_assembly(instructions, instructions_bin, colorize=True)

            upper = ""
            lower = ""
            for word in instructions_bin:
                insthex = "%04x" % word
                upper += " %s" % insthex[0:2]
                lower += " %s" % insthex[2:4]

            out['upper'] = upper
            out['lower'] = lower

        except AssemblerException as e:
            out['error'] = (e.msg, e.data, e.inst)

        return json.dumps(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: asmweb.py CONFIGFILE [IP]"
        sys.exit(1)
    configfile = sys.argv.pop(1)  # remove it because web.py uses argv
    if not os.path.exists(configfile):
        print >> sys.stderr, "File not found: " + configfile
        print >> sys.stderr, "Usage: asmweb.py CONFIGFILE [IP]"
        sys.exit(1)
    assembler = Assembler(configfile)

    app = web.application(urls, globals())
    app.add_processor(Injector(assembler))
    app.run()
