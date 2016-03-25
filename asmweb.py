#!/usr/bin/env python

from assembler import Assembler, AssemblerException
import web
import json
import zipfile

_NAME = "DYEL"

urls = (
    '/assemble/', 'asm2bin',
    '/dl/.*', 'download',
    '/', 'Main',
)


class Main:
    def GET(self):
        raise web.redirect("/static/index.html")


class download:
    def GET(self):
        with zipfile.ZipFile('%s2bin.zip' % _NAME, 'w') as zip:
            zip.write('asm2bin.py')
            zip.write('assembler.py')
        return open('%s2bin.zip' % _NAME, 'rb').read()


class asm2bin:
    def POST(self):
        data = web.data()
        lines = data.split('\n')

        web.header('Content-Type', 'application/json')

        out = {}
        out['messages'] = []

        def getmsg(msgtuple):
            out['messages'].append(msgtuple)

        a = Assembler(info_callback=getmsg)

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
    app = web.application(urls, globals())
    app.run()
