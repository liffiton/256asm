# 256asm

256asm is an assembler for the student-designed ISAs from CS 256 (Computer
Organization and Architecture) at Illinois Wesleyan University.  Each year,
students design a new ISA from scratch (though heavily influenced by MIPS,
which they learn earlier in the semester), design a datapath for it, and
implement their CPU both in [Logisim](http://www.cburch.com/logisim/) and on
physical breadboards.

256asm was created to help students produce machine code to run on their CPU.
It is flexible and configurable, allowing the one codebase to work for each
successive ISA with minimal if any changes (again, this works given that each
ISA has a similar "lineage" given the MIPS influence).  It can handle ISAs with
varying instruction widths, operand counts, field sizes, etc., and branch and
jump instructions can be created with either offset or absolute jump address
immediate values.

The assembler can be run via the command-line as ``asm2bin.py`` or via a simple
web interface that assembles code and reports errors as the code is typed.
Both interfaces produce binary data that can be copied into Logisim or written
into EEPROMs to run the code on the students' CPU.

![asmweb screenshot](docs/asmweb_screenshot.png?raw=true)

## Usage

Every run requires a config file specifying the details of an ISA.  See the
included ``*.conf`` files for examples.

To serve the web interface:

    ./asmweb.py CONFIGFILE

The interface should then be accessible via port 8080.

Optionally, you can specify a different port:

    ./asmweb.py CONFIGFILE PORTNUMBER

To run the command-line assembler:

    ./asm2bin.py CONFIGFILE FILE.asm

That will produce ``FILE.0.bin`` and ``FILE.1.bin`` with the low and high bytes
of the instructions, respectively.  Alternatively, specify output filenames
directly with:

    ./asm2bin.py CONFIGFILE FILE.asm FILEOUT0 FILEOUT1

## Dependencies

The code is compatible with Python 3.6+.

The web interface ``asmweb.py`` depends on [Bottle](https://bottlepy.org/), a
version of which is included in this repository.

The assembler itself and the command-line interface ``asm2bin.py`` have no
dependencies beyond the Python standard library.

## Caveats

Some aspects of the assembler are not as polished nor configurable as they
could be.  While much can be controlled via the config file, some ISAs may
require modifications to the Assembler class to properly handle all of their
features.

