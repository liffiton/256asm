"""
CS256 ISA Assembler
Author: Mark Liffiton
"""
import collections
import configparser
import re
import sys
from pathlib import PurePath


class AssemblerException(Exception):
    def __init__(self, msg, data=None, lineno=None, instruction=None):
        self.msg = msg
        self.data = data
        self.lineno = lineno
        self.inst = instruction

    def __str__(self):
        ret = self.msg
        if self.data:
            ret += ": {}".format(self.data)
        if self.inst:
            ret += "\n  In line {}: {}".format(self.lineno, self.inst)
        return ret


class Assembler:
    """Assembles CS256 assembly code into machine code following definitions
    given in the specified config file."""

    def __init__(self, configfile, info_callback=None):
        # manipulate configfile and samplefile as PurePath objects
        self.configfile = PurePath(configfile)

        config = configparser.SafeConfigParser()
        config.read(self.configfile)

        self.name = config.get('general', 'name')
        self.inst_size = config.getint('general', 'inst_size')
        self.max_reg = config.getint('general', 'max_reg')
        self.reg_prefix = config.get('general', 'reg_prefix')
        # Samplefile should be in same directory as config file
        self.samplefile = self.configfile.parent / config.get('general', 'samplefile')

        self.special_regs = \
            {x: int(y) for x, y in config.items('special_regs')}

        self.field_sizes = \
            {x: int(y) for x, y in config.items('field_sizes')}

        self.instructions = collections.defaultdict(dict)
        for inst, opcode in config.items('instruction_opcodes'):
            self.instructions[inst]['opcode'] = int(opcode)
        for inst, parts in config.items('instruction_parts'):
            self.instructions[inst]['parts'] = list(parts)
        for inst, tweak in config.items('instruction_tweaks'):
            self.instructions[inst]['tweak'] = tweak

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
        self.cur_inst = None    # used for error reporting
        self.cur_lineno = None  # used for error reporting

        self.info_callback = info_callback

    def register_info_callback(self, info_callback):
        self.info_callback = info_callback

    def assemble_instruction(self, inst, lineno, pc):
        """Produce the binary encoding of one instruction."""
        assert re.match(self.inst_regex, inst)

        self.cur_inst = inst
        self.cur_lineno = lineno

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
        parts = inst_info['parts']
        sizes = inst_info['sizes']

        # check for the correct number of arguments
        if inst_info['args'] != len(args):
            self.report_err(
                "Incorrect number of arguments in instruction (expected {}, got {})".format(inst_info['args'], len(args)),
                inst
            )
            sys.exit(2)

        if inst_info['tweak'] == "flip_args":
            # Swap args[0] and args[1]
            # e.g., for a Store instruction w/ dest address written first but it needs to be 2nd reg.
            # e.g., for a Branch instruction where we want the immediate to be first in the encoding but we write the label second in the assembly instruction
            args[0], args[1] = args[1], args[0]
            parts[0], parts[1] = parts[1], parts[0]
            sizes[0], sizes[1] = sizes[1], sizes[0]

        elif inst_info['tweak'] == "dupe1to3":
            # Copy args[0] to args[2]
            # e.g., for a Store instruction w/ src data as first arg, but ISA typically has src reg as second and third args
            args.append(args[0])
            parts.append(parts[0])
            sizes.append(sizes[0])

        # parse each part (get a numerical value for it)
        # and shift appropriate amount, summing each
        instruction = 0
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
                        "{}-bit space, but |{}| > 2^{}".format(size, val, size-1)
                    )
                    sys.exit(2)
                # fit negative values into given # of bits
                val = val % 2**size

            # print "Shifting: {} << {}".format(val, shamt)
            instruction += val << shamt

        return instruction

    def parse_part(self, type, inst_info, pc, arg=None):
        """Parse one argument of an instruction (opcode, register,
        immediate, or label).
        """
        #print(f"Type {type}  arg {arg}")

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
            try:
                return int(arg,0)
            except ValueError as e:
                self.report_err(str(e))
        elif type == 'j' and arg in self.labels:
            return self.labels[arg]
        elif type == 'l' and arg in self.labels:
            # offset from pc, so store instruction count - pc
            return self.labels[arg] - pc
        elif type == 'x':  # unused - fill w/ zero bits
            return 0
        else:
            self.report_err("Invalid instruction argument", f"{arg} - type {type}")
            sys.exit(2)

    def assemble_instructions(self, instructions):
        """Assemble a list of instructions."""
        return [self.assemble_instruction(inst[0], inst[1], i) for i, inst in enumerate(instructions)]

    def first_pass(self, lines):
        """Take a first pass through the code, cleaning, stripping, and
           determining label addresses."""
        # clear the labels (in case this object is reused)
        self.labels = {}

        instructions = []

        for lineno, line in enumerate(lines):
            # one-based counting for lines
            lineno += 1

            # strip comments
            line = line.partition("#")[0]
            # clean up
            line = line.lower().strip()

            if not line:
                # it's a comment or blank!
                continue

            if re.match(self.inst_regex, line):
                # it's an instruction!
                instructions.append((line, lineno))
            elif re.match("^[a-z][a-z0-9]*:$", line):
                # store the label (strip the colon)
                self.labels[line[:-1]] = len(instructions)
            else:
                # Uh oh...
                self.report_inf("Invalid line (ignoring)", "{}: {}".format(lineno, line))

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

        if instructions:
            max_inst_width = max(len(inst[0]) for inst in instructions)
            max_inst_width = max(max_inst_width, 12)   # always at *least* 12 chars
        else:
            max_inst_width = 15

        header = "  #: {0:<{1}}  {2:<20}  {3}\n".format("Instruction", max_inst_width, "Binary", "Hex")
        header += "-" * len(header) + "\n"

        ret = header
        for i in range(len(instructions)):
            inststr = instructions[i][0]
            instparts = inststr.split()
            op = instparts[0]

            if colorize:
                for j in range(len(instparts)):
                    instparts[j] = "<span style='color: {}'>{}</span>".format(self.palette[j], instparts[j])
            # Add spaces to pad to 20 chars.
            # (Can't use ljust because of added <span> chars.)
            inststr = " ".join(instparts) + (" " * (max_inst_width - len(inststr)))

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
                    instbinparts[j] = "<span style='color: {}'>{}</span>".format(self.palette[j], instbinparts[j])
            # Add spaces between and after all parts and padding to 20 chars,
            # accounting for bits of the instruction and spaces between parts.
            # (Can't use ljust because of added <span> chars.)
            instbinstr = " ".join(instbinparts) + (" " * (20 - self.inst_size - (len(sizes)-1)))

            insthex = "{:04x}".format(instructions_bin[i])

            if i in linelabels:
                ret += linelabels[i] + ":\n"

            # (Can't use format string justification because of added <span> chars.)
            ret += "{:3}: {}  {}  {}\n".format(i, inststr, instbinstr, insthex)

        return ret

    def output_bin(self, filename, bytes):
        """Create a binary image file for the given bytes."""
        with open(filename, 'wb') as f:
            f.write(bytes)

    def output_logisim_img(self, filename, bytes):
        """Create a Logisim memory image file for the given bytes."""
        file_header = "v2.0 raw\n"  # header required by Logisim to read memory image files
        with open(filename, 'w') as f:
            f.write(file_header)
            f.write(" ".join("{:02x}".format(byte) for byte in bytes))

    def output_sim_bin(self, filename, words):
        """Create a 256sim memory image file for the given bytes."""
        with open(filename, 'w') as f:
            f.write(" ".join("{:04x}".format(word) for word in words))
            f.write("\n")

    def assemble_file(self, filename, format, outfiles):
        """Fully assemble a Logisim memory image file containing CS256 ISA assembly code."""
        self.report_inf("Assembling", filename)
        with open(filename) as f:
            lines = f.readlines()

        (instructions, instructions_bin) = self.assemble_lines(lines)

        print(self.prettyprint_assembly(instructions, instructions_bin))

        bytes_low = bytes(word % 256 for word in instructions_bin)
        bytes_high = bytes(word // 256 for word in instructions_bin)

        if format == "bin":
            self.output_bin(outfiles[0], bytes_low)
            self.output_bin(outfiles[1], bytes_high)
        elif format == "256sim":
            self.output_sim_bin(outfiles[0], instructions_bin)
        elif format == "logisim":
            self.output_logisim_img(outfiles[0], bytes_low)
            self.output_logisim_img(outfiles[1], bytes_high)

        self.report_inf("Generated", ", ".join(outfiles))

    def report_err(self, msg, data=""):
        raise AssemblerException(msg, data, self.cur_lineno, self.cur_inst)

    def report_inf(self, msg, data=""):
        self.info_callback( (msg, data) )
