#!/usr/bin/python
"""
Unit tests for the Assembler class
"""
import unittest
from assembler import Assembler


class AssemblerTestCase(unittest.TestCase):
    def setUp(self):
        self.Assembler = Assembler()

    def tearDown(self):
        self.Assembler = None

    def run_inst(self, inst, result):
        self.assertEqual(self.Assembler.assemble_instruction(inst, 0), result,
                         "incorrect encoding of: %s" % inst)

    def test_zero(self):
        self.run_inst("add $1 $2 $3", 0b0000010100110000)

    def test_one_instruction_add(self):
        self.run_inst("addi $1 $7 23", 0b0010011110010111)

    def test_one_instruction_addi_negative(self):
        self.run_inst("addi $1 $7 -1", 0b0010011111111111)

    def test_one_instruction_sb(self):
        self.run_inst("sb $1 $2 33", 0b1010010100100001)

    def test_lines_beq_1(self):
        lines = "label:\nadd $1 $2 $3\nbeq $0 $7 label\n"
        self.assertEqual(self.Assembler.assemble_lines(lines.split("\n")),
                         [0b0000010100110000, 0b0110001111111110],
                         "incorrect add/beq/label, two instructions")

    def test_lines_beq_2(self):
        lines = "label:\nadd $1 $2 $3\nbeq $1 $1 label\nlabel2:\nbeq $2 $2 label2\n"
        self.assertEqual(self.Assembler.assemble_lines(lines.split("\n")),
                         [0b0000010100110000, 0b0110010011111110,
                          0b0110100101111111],
                         "incorrect add/beq/label, three instructions")

if __name__ == '__main__':
    unittest.main()
