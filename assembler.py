"""
CS256 ISA Assembler
Author: Mark Liffiton
"""
import collections
import configparser
import re
import sys


class AssemblerException(Exception):
    def __init__(self, msg, data=None, instruction=None):
        self.msg = msg
        self.data = data
        self.inst = instruction

    def __str__(self):
        ret = self.msg
        if self.data:
            ret += ": " + str(self.data)
        if self.inst:
            ret += "\n  In: " + self.inst
        return ret


class Assembler:
    """Assembles CS256 assembly code into machine code following definitions
    given in the specified config file."""

    def __init__(self, configfile, info_callback=None):
        self.configfile = configfile
        config = configparser.SafeConfigParser()
        config.read(configfile)

        self.name = config.get('general', 'name')
        self.inst_size = config.getint('general', 'inst_size')
        self.max_reg = config.getint('general', 'max_reg')
        self.reg_prefix = config.get('general', 'reg_prefix')
        self.samplefile = config.get('general', 'samplefile')

        self.special_regs = \
            {x: int(y) for x, y in config.items('special_regs')}

        self.field_sizes = \
            {x: int(y) for x, y in config.items('field_sizes')}

        self.instructions = collections.defaultdict(dict)
        for inst, opcode in config.items('instruction_opcodes'):
            self.instructions[inst]['opcode'] = int(opcode)
        for inst, parts in config.items('instruction_parts'):
            self.instructions[inst]['parts'] = parts

        if 'instruction_funccodes' in config.sections():
            for inst, funccode in config.items('instruction_funccodes'):
                self.instructions[inst]['funccode'] = int(funccode)

        self.report_commas = True

        self.palette = [
            '#6D993B',
            '#A37238',
            '#AC4548',
            '#6048A3',
            '#449599',
        ]

        # create sizes and arg counts for each instruction
        # modifies instruction dictionaries within self.instructions
        for inst_info in self.instructions.values():
            # figure out number of required arguments to instruction
            # (number of parts, not counting opcode(s) or function code(s) or 'x' space)
            parts = inst_info['parts']
            inst_info['args'] = len(parts) - parts.count('o') - parts.count('f') - parts.count('x')

            # figure out sizes (for shift amounts)
            sizes = []
            rem = self.inst_size  # remaining bits
            for c in inst_info['parts']:
                if c in self.field_sizes:
                    sizes.append(self.field_sizes[c])
                    rem -= self.field_sizes[c]
            if rem:
                sizes.append(rem)  # immediate (or extra) gets all remaining bits

            inst_info['sizes'] = sizes

        # Used internally
        self.inst_regex = r"({})\s".format("|".join(self.instructions))
        self.labels = {}
        self.cur_inst = ""     # used for error reporting

        self.info_callback = info_callback

    def register_info_callback(self, info_callback):
        self.info_callback = info_callback

    def assemble_instruction(self, inst, pc):
        """Produce the binary encoding of one instruction."""
        assert re.match(self.inst_regex, inst)

        self.cur_inst = inst

        if "," in inst:
            if self.report_commas:
                self.report_inf("Invalid comma found (stripping all commas)", inst)
                self.report_commas = False
            inst = inst.replace(',',' ')

        # split instruction into parts
        inst_parts = inst.split()
        op = inst_parts[0]
        args = inst_parts[1:]
        inst_info = self.instructions[op]

#        # Swap parts[1] and parts[2] for any instruction w/ at least 2 registers
#        # Instructions are written with dest first, but dest is second register field in instruction
#        if op != "biz" and op != "bnz":
#            (parts[1],parts[2]) = (parts[2],parts[1])
#
#        # !!! For sb:  given "sb r1 r2 imm", we want r1 in s1 (place 3)   and r2 in s0 (place 1)"
#        if op == 'sb':
#            data_r = parts[2]
#            addr_r = parts[1]
#            # !!! insert empty 'part' for the unused portion of the instruction
#            parts.insert(2, 0)
#            parts[1] = addr_r
#            parts[3] = data_r
#
#        # !!! For lb:  given "lb r1 r2 imm", we want r1 in dest (place 2) and r2 in s0 (place 1)"
#        if op == 'lb':
#            data_r = parts[2]
#            addr_r = parts[1]
#            # !!! insert empty 'part' for the unused portion of the instruction
#            parts.insert(3, 0)
#            parts[1] = addr_r
#            parts[2] = data_r

        # check for the correct number of arguments
        if inst_info['args'] != len(args):
            self.report_err("Incorrect number of arguments in instruction (expected %d, got %d)" % (inst_info['args'], len(args)), inst)
            sys.exit(2)

        # parse each part (get a numerical value for it)
        # and shift appropriate amount, summing each
        instruction = 0
        parts = inst_info['parts']
        sizes = inst_info['sizes']
        for i in range(len(parts)):
            c = parts[i]
            size = sizes[i]
            shamt = sum(sizes[i+1:])

            # r, l, j, and i have arguments, opcode and funccode do not
            if c in ['r', 'l', 'j', 'i']:
                arg = args.pop(0)
                val = self.parse_part(c, inst_info, pc, arg)
            else:
                val = self.parse_part(c, inst_info, pc)

            # check immediate or branch size
            if c in ['l', 'j', 'i']:
                if val >= 2**(size-1) or val < -2**(size-1):
                    self.report_err(
                        "Immediate/Label out of range",
                        "%d-bit space, but |%d| > 2^%d" % (size, val, size-1)
                    )
                    sys.exit(2)
                # fit negative values into given # of bits
                val = val % 2**size

            # print "Shifting: %d << %d" % (val, shamt)
            instruction += val << shamt

        return instruction

    def parse_part(self, type, inst_info, pc, arg=None):
        """Parse one argument of an instruction (opcode, register,
        immediate, or label).
        """
        if type == 'o':
            return inst_info['opcode']
        elif type == 'f':
            return inst_info['funccode']
        elif type == 'r' and arg in self.special_regs:
            return self.special_regs[arg]
        elif type == 'r' and re.match(r"^{}\d+$".format(re.escape(self.reg_prefix)), arg):
            regindex = int(arg[1:])
            if regindex > self.max_reg:
                self.report_err("Register out of range", regindex)
                sys.exit(2)
            return regindex
        elif type == 'i' and re.match(r"^-?\d+$|^-?0x[a-fA-F0-9]+$|^-?0b[01]+$", arg):
            return int(arg,0)
        elif type == 'j' and arg in self.labels:
            return self.labels[arg]
        elif type == 'l' and arg in self.labels:
            # offset from pc+1, so store instruction count - (pc+1)
            return self.labels[arg] - (pc+1)
        elif type == 'x':  # unused - fill w/ zero bits
            return 0
        else:
            self.report_err("Invalid instruction argument", arg)
            sys.exit(2)

    def assemble_instructions(self, instructions):
        """Assemble a list of instructions."""
        return [self.assemble_instruction(instructions[i], i) for i in range(len(instructions))]

    def first_pass(self, lines):
        """Take a first pass through the code, cleaning, stripping, and
           determining label addresses."""
        # clear the labels (in case this object is reused)
        self.labels = {}

        instructions = []

        for line in lines:
            # strip comments
            line = line.partition("#")[0]
            # clean up
            line = line.lower().strip()

            if not line:
                # it's a comment or blank!
                continue

            if re.match(self.inst_regex, line):
                # it's an instruction!
                instructions.append(line)
            elif re.match("^[a-z][a-z0-9]*:$", line):
                # store the label (strip the colon)
                self.labels[line[:-1]] = len(instructions)
            else:
                # Uh oh...
                self.report_inf("Invalid line (ignoring)", line)

        return instructions

    def assemble_lines(self, lines):
        """Fully assemble a list of lines of assembly code.
        Returns a list of binary-encoded instructions.
        """
        instructions = self.first_pass(lines)
        instructions_bin = self.assemble_instructions(instructions)
        return (instructions, instructions_bin)

    def prettyprint_assembly(self, instructions, instructions_bin, colorize=False):
        """Return a pretty-printed string of the instructions and their
        assembled machine code to stdout.
        """

        # setup linelabels to map line numbers to labels
        linelabels = {line: label for (label, line) in self.labels.items()}

        ret = ""
        ret += "  #: %s  %s  %s\n" % ("Instruction".ljust(20,' '), "Binary".ljust(20,' '), "Hex")
        ret += "-" * 55 + "\n"
        for i in range(len(instructions)):
            inststr = instructions[i]
            instparts = inststr.split(' ')
            op = instparts[0]

            if colorize:
                for j in range(len(instparts)):
                    instparts[j] = "<span style='color: %s'>%s</span>" \
                        % (self.palette[j], instparts[j])
            # Add spaces to pad to 20 chars.  (Can't use ljust because of added <span> chars.)
            inststr = " ".join(instparts) + (" " * (20 - len(inststr)))

            # rjust() adds leading 0s if needed.
            instbin = bin(instructions_bin[i])[2:].rjust(16, '0')
            instbinparts = []
            j = 0
            sizes = self.instructions[op]['sizes']
            for size in sizes:
                part = instbin[j:j+size]
                instbinparts.append(part)
                j += size
            if colorize:
                for j in range(len(sizes)):
                    instbinparts[j] = "<span style='color: %s'>%s</span>" \
                        % (self.palette[j], instbinparts[j])
            # Add spaces between and after all parts and padding to 20 chars,
            # accounting for bits of the instruction and spaces between parts.
            instbinstr = " ".join(instbinparts) + (" " * (20 - self.inst_size - (len(sizes)-1)))

            insthex = "%04x" % instructions_bin[i]

            if i in linelabels:
                ret += linelabels[i] + ":\n"

            ret += "%3d: %s  %s  %s\n" % (i, inststr, instbinstr, insthex)

        return ret

    def assemble_file(self, filename, fileout0="", fileout1=""):
        """Fully assemble a file containing CS256 ISA assembly code."""
        self.report_inf("Assembling", filename)
        with open(filename) as f:
            lines = f.readlines()

        (instructions, instructions_bin) = self.assemble_lines(lines)

        print(self.prettyprint_assembly(instructions, instructions_bin))

        binfile0 = bytearray(word % 256 for word in instructions_bin)
        binfile1 = bytearray(word // 256 for word in instructions_bin)
        with open(fileout0, 'wb') as f0:
            f0.write(binfile0)
        with open(fileout1, 'wb') as f1:
            f1.write(binfile1)
        self.report_inf("Generated bin files", "%s and %s" % (fileout0, fileout1))

    def report_err(self, msg, data=""):
        raise AssemblerException(msg, data, self.cur_inst)

    def report_inf(self, msg, data=""):
        self.info_callback( (msg, data) )
