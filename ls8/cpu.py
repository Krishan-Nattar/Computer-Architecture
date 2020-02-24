"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.register = [0] * 8
        self.ram = [0] * 255
        self.pc = 0
        self.LDI = 0b10000010 # Set a specific register to a specific value
        self.PRN = 0b01000111 # Print a number
        self.HLT = 0b00000001 # Halt the program
        self.MUL = 0b10100010 # Multiply two registers together and store result in register A
        pass

    def load(self):
        """Load a program into memory."""
        # print(sys.argv)
        path = sys.argv[1]
        # print(path)

        address = 0

        with open(path) as file:
            for line in file:
                if line[0] != "#" and line !='\n':
                    # print(line)
                    # print(line[0:8])
                    self.ram[address] = int(line[:8], 2)
                    address += 1



        # For now, we've just hardcoded a program:

        # program = [
        #     # From print8.ls8
        #     0b10000010, # LDI R0,8
        #     0b00000000,
        #     0b00001000,
        #     0b01000111, # PRN R0
        #     0b00000000,
        #     0b00000001, # HLT
        # ]

        # for instruction in program:
        #     self.ram[address] = instruction
        #     address += 1

        


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.register[reg_a] += self.register[reg_b]
        elif op == "MUL":
            self.register[reg_a] *= self.register[reg_b]
            #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        IR = self.pc
        # print(self.ram)
        
        while True:
            command = self.ram[IR]
            operand_a = self.ram_read(IR + 1)
            operand_b = self.ram_read(IR + 2)

            if command == self.LDI:
                reg = operand_a
                num = operand_b
                self.register[reg] = num
                IR += 3
            elif command == self.PRN:
                reg = operand_a
                num = self.register[reg]
                print(num)
                IR += 2
            elif command == self.HLT:
                sys.exit(1)
            elif command == self.MUL:
                self.alu("MUL", operand_a, operand_b)
                IR += 3
            else:
                print("INVALID COMMAND")
                sys.exit(1)
        pass
    def ram_read(self, MAR):
        return self.ram[MAR]
    def ram_write(self, MDR, MAR):
        self.ram[MAR] = MDR

