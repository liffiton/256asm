"""
CS256 ISA Assembler
Author: Mark Liffiton
"""
import collections
import configparser
import re
from dataclasses import dataclass
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


@dataclass
class Instruction:
    text: str
    lineno: int
    text_parts: list[tuple[str, str]] | None = None
    bin_parts: list[tuple] | None = None
    binary: int | None = None


class Assembler:
    """Assembles CS256 assembly code into machine code following definitions
    given in the specified config file."""

    def __init__(self, configfile, info_callback=None):
        # manipulate configfile and samplefile as PurePath objects
        self.configfile = PurePath(configfile)

        config = configparser.ConfigParser()
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
        if 'instruction_tweaks' in config:
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
                # any extra gets all remaining bits
                inst_info['parts'].append('x')
                sizes.append(rem)

            inst_info['sizes'] = sizes

        # Used internally
        self.inst_regex = r"({})\s".format("|".join(self.instructions))
        self.labels = {}
        self.cur_inst = None    # used for error reporting

        self.info_callback = info_callback

    def register_info_callback(self, info_callback):
        self.info_callback = info_callback

    def assemble_instruction(self, inst, pc):
        """Produce the binary encoding of one instruction."""
        assert re.match(self.inst_regex, inst.text)

        self.cur_inst = inst

        if "," in inst.text:
            if self.report_commas:
                self.report_inf("Invalid comma found (stripping all commas)", inst.text)
                self.report_commas = False
            inst.text = inst.text.replace(',',' ')

        # split instruction into parts
        args = inst.text.split()
        inst.text_parts = list(zip(args, self.palette))  # zip() stops at end of shortest

        inst_info = self.instructions[args[0]]

        # check for the correct number of arguments
        if inst_info['args'] != len(args)-1:
            self.report_err(
                "Incorrect number of arguments in instruction (expected {}, got {})".format(inst_info['args'], len(args)-1),
                inst.text
            )

        bin_parts = []
        text_part_iter = iter(inst.text_parts)
        for kind, size in zip(inst_info['parts'], inst_info['sizes']):
            if kind in ['o', 'r', 'l', 'j', 'i']:
                # these have arguments
                arg, color = next(text_part_iter)
                val = self.parse_part(kind, inst_info, pc, arg)

                # check immediate or branch size
                if kind in ['l', 'j', 'i']:
                    if val >= 2**(size-1) or val < -2**(size-1):
                        self.report_err(
                            "Immediate/Label out of range",
                            "{}-bit space, but |{}| > 2^{}".format(size, val, size-1)
                        )
                    # fit negative values into given # of bits
                    val = val % 2**size
            else:
                # other kinds ('x', funccode) do not
                val = self.parse_part(kind, inst_info, pc)
                color = '#999999'

            # Convert to binary; rjust() adds leading 0s if needed.
            bin_val = bin(val)[2:].rjust(size, '0')
            bin_parts.append((kind, size, bin_val, val, color))

        if inst_info.get('tweak') == "flip_args":
            # Swap first and second operand
            # e.g., for a Store instruction w/ dest address written first but it needs to be 2nd reg.
            # e.g., for a Branch instruction where we want the immediate to be first in the encoding but we write the label second in the assembly instruction
            bin_parts[1], bin_parts[2] = bin_parts[2], bin_parts[1]

        elif inst_info.get('tweak') == "dupe1to3":
            # Copy first operand to third (end) position
            # e.g., for a Store instruction w/ src data as first arg, but ISA typically has src reg as second and third args
            bin_parts.append(bin_parts[1])

        inst.bin_parts = bin_parts

        # build final binary by shifting and summing each part
        instruction_bin = 0
        for kind, size, bin_val, val, color in bin_parts:
            instruction_bin <<= size
            instruction_bin += val

        inst.binary = instruction_bin

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

    def assemble_instructions(self, instructions):
        """Assemble a list of instructions."""
        return [self.assemble_instruction(inst, pc) for pc, inst in enumerate(instructions)]

    def first_pass(self, lines) -> list[Instruction]:
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
                inst = Instruction(text=line, lineno=lineno)
                instructions.append(inst)
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
        self.assemble_instructions(instructions)
        return instructions

    def prettyprint_assembly(self, instructions, colorize=False):
        """Return a pretty-printed string of the instructions and their
        assembled machine code to stdout.
        """

        # set up linelabels to map line numbers to labels
        linelabels = {line: label for (label, line) in self.labels.items()}

        if instructions:
            max_inst_width = max(len(inst.text) for inst in instructions)
            max_inst_width = max(max_inst_width, 12)   # always at *least* 12 chars
        else:
            max_inst_width = 15

        header = "  #: {0:<{1}}  {2:<20}  {3}\n".format("Instruction", max_inst_width, "Binary", "Hex")
        header += "-" * len(header) + "\n"

        ret = header
        for inst in instructions:
            inst_str = " ".join(part[0] for part in inst.text_parts)
            # Pad to 20 chars with spaces.
            # (Pre-compute because don't want to count added <span> chars when colorized.)
            padding = " " * (max_inst_width - len(inst_str))

            if colorize:
                inst_str = " ".join(f"<span style='color: {part[1]}'>{part[0]}</span>" for part in inst.text_parts)

            inst_str += padding

            # Pad to 20 chars with spaces.
            padding_len = 20 - self.inst_size - (len(inst.bin_parts) - 1)
            if colorize:
                instbinstr = " ".join(
                    f"<span style='color: {color}'>{bin_val}</span>"
                    for kind, size, bin_val, val, color in inst.bin_parts
                ) + (" " * padding_len)
            else:
                instbinstr = " ".join(
                    bin_val for kind, size, bin_val, val, color in inst.bin_parts
                ) + (" " * padding_len)

            insthex = "{:04x}".format(inst.binary)

            if inst.lineno in linelabels:
                ret += linelabels[inst.lineno] + ":\n"

            # (Can't use format string justification because of added <span> chars.)
            ret += "{:3}: {}  {}  {}\n".format(inst.lineno, inst_str, instbinstr, insthex)

        return ret

    def output_bin(self, filename, bytes):
        """Create a binary image file for the given bytes."""
        with open(filename, 'wb') as f:
            f.write(bytes)

    def output_logisim_img(self, filename, words):
        """Create a Logisim memory image file for the given bytes."""
        file_header = "v2.0 raw\n"  # header required by Logisim to read memory image files
        with open(filename, 'w') as f:
            f.write(file_header)
            f.write(" ".join("{:04x}".format(word) for word in words))

    def output_sim_bin(self, filename, words):
        """Create a 256sim memory image file for the given bytes."""
        with open(filename, 'w') as f:
            f.write(" ".join("{:04x}".format(word) for word in words))
            f.write("\n")

    def assemble_file(self, filename, format, outfiles):
        """Fully assemble a memory image file containing CS256 ISA assembly code."""
        self.report_inf("Assembling", filename)
        with open(filename) as f:
            lines = f.readlines()

        instructions = self.assemble_lines(lines)

        print(self.prettyprint_assembly(instructions))

        binary = [inst.binary for inst in instructions]
        bytes_low = bytes(word % 256 for word in binary)
        bytes_high = bytes(word // 256 for word in binary)

        if format == "bin":
            self.output_bin(outfiles[0], bytes_low)
            self.output_bin(outfiles[1], bytes_high)
        elif format == "256sim":
            self.output_sim_bin(outfiles[0], binary)
        elif format == "logisim":
            self.output_logisim_img(outfiles[0], binary)

        self.report_inf("Generated", ", ".join(outfiles))

    def report_err(self, msg, data=""):
        raise AssemblerException(msg, data, self.cur_inst.lineno, self.cur_inst.text)

    def report_inf(self, msg, data=""):
        self.info_callback( (msg, data) )
