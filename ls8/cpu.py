"""CPU functionality."""

import sys
from datetime import datetime, timedelta
import time
import msvcrt 

# ALU OPS

ADD = 0b10100000 # Add two registry addresses together
SUB = 0b10100001
MUL = 0b10100010 # Multiply two registers together and store result in register A
DIV = 0b10100011
MOD = 0b10100100

INC = 0b01100101
DEC = 0b01100110 

CMP = 0b10100111

AND = 0b10101000
NOT = 0b01101001
OR = 0b10101010
XOR = 0b10101011 
SHL = 0b10101100
SHR = 0b10101101 

# PC MUTATORS

CALL = 0b01010000 # Jump to a subroutine's address
RET = 0b00010001 # Go to return address after subroutine is done

INT = 0b01010010
IRET = 0b00010011 # Interrupt Return

JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110
JGT = 0b01010111
JLT = 0b01011000
JLE = 0b01011001
JGE = 0b01011010

# OTHER

NOP = 0b00000000

HLT = 0b00000001 # Halt the program

LDI = 0b10000010 # Set a specific register to a specific value

LD = 0b10000011
ST = 0b10000100 # Store value from registerB in the address stored in registerA

PUSH = 0b01000101 # Push instruction onto the stack
POP = 0b01000110 # Pop instruction off the stack

PRN = 0b01000111 # Print a number
PRA = 0b01001000

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.register = [0] * 8
        self.interrupt_mask = 5
        self.interrupt_status = 6
        self.sp = 7

        self.FL = 0b00000000 # Flag Register
        '''
        Note to myself about flags
        '''
        # 00000LGE
        # L Less-than: during a CMP, set to 1 if registerA is less than registerB, zero otherwise.
        # G Greater-than: during a CMP, set to 1 if registerA is greater than registerB, zero otherwise.
        # E Equal: during a CMP, set to 1 if registerA is equal to registerB, zero otherwise.
        self.less_than = 0b00000100
        self.greater_than = 0b00000010
        self.equal_to = 0b00000001

        self.ram = [0] * 255
        self.pc = 0
        self.branchtable = {}
        
        self.branchtable[LDI] = self.handle_LDI
        self.branchtable[PRN] = self.handle_PRN
        self.branchtable[HLT] = self.handle_HLT
        self.branchtable[MUL] = self.handle_MUL
        self.branchtable[POP] = self.handle_POP
        self.branchtable[PUSH] = self.handle_PUSH
        self.branchtable[CALL] = self.handle_CALL
        self.branchtable[RET] = self.handle_RET
        self.branchtable[ADD] = self.handle_ADD
        self.branchtable[ST] = self.handle_ST
        self.branchtable[IRET] = self.handle_IRET
        self.branchtable[JMP] = self.handle_JMP
        self.branchtable[PRA] = self.handle_PRA
        self.branchtable[NOP] = self.handle_NOP
        self.branchtable[LD] = self.handle_LD
        self.branchtable[CMP] = self.handle_CMP
        self.branchtable[JLT] = self.handle_JLT
        self.branchtable[JNE] = self.handle_JNE
        self.branchtable[JEQ] = self.handle_JEQ
        self.branchtable[JGE] = self.handle_JGE
        self.branchtable[DEC] = self.handle_DEC
        self.branchtable[INC] = self.handle_INC
        self.branchtable[AND] = self.handle_AND
        self.branchtable[XOR] = self.handle_XOR

        self.register[self.sp] = 0xF4 # initialized to point at key press
        self.interrupt_handler_address = 0
        self.interrupts_enabled = True

        self.init_time = 0
    def handle_AND(self):
        regA = self.ram_read(self.pc + 1)
        regB = self.ram_read(self.pc + 2)
        self.register[regA] = self.register[regA] & self.register[regB]
        self.pc += 3
    def handle_XOR(self):
        regA = self.ram_read(self.pc + 1)
        regB = self.ram_read(self.pc + 2)
        self.register[regA] = self.register[regA] ^ self.register[regB]
        self.pc += 3
    def kbfunc(self): 
        '''
        Catches a keyboard input.
        Saves that value as a number in ram
        Adds 2 to the interrupt status
        '''
        x = msvcrt.kbhit()
        if x: 
            # Creates a number associated with the keyboard input
            ret = ord(msvcrt.getch()) 

            # Storing the keyboard press value in ram at this location
            # This value will be grabbed later by the interrupt operation to print out the letter
            self.ram[0xf4] = ret

            # Adding to the register instead of overwriting in case there are other interrupt statuses being created
            self.register[self.interrupt_status] += 0b00000010
    def handle_DEC(self):
        '''
        Decrement (subtract 1 from) the value in the given register.
        '''
        reg = self.ram_read(self.pc + 1)
        self.register[reg] -= 1

        self.pc += 2
    def handle_INC(self):
        '''
        Increment (Add 1 to) the value in the given register.
        '''
        reg = self.ram_read(self.pc + 1)
        self.register[reg] += 1

        self.pc += 2

    def handle_CMP(self):
        '''
        Compare the values in two registers.
        If they are equal, set the Equal E flag to 1, otherwise set it to 0.
        If registerA is less than registerB, set the Less-than L flag to 1, otherwise set it to 0.
        If registerA is greater than registerB, set the Greater-than G flag to 1, otherwise set it to 0.
        '''
        operand_a = self.ram_read(self.pc +1)
        operand_b = self.ram_read(self.pc +2)
        self.alu("CMP", operand_a, operand_b)
        self.pc += 3

    def handle_JLT(self):
        '''
        If less-than flag is set (true), jump to the address stored in the given register.
        '''
        if self.less_than & self.FL:
            reg = self.ram_read(self.pc + 1)
            self.pc = self.register[reg]
        else:
            self.pc +=2

    def handle_JNE(self):
        ''' 
        If E flag is clear (false, 0), jump to the address stored in the given register.
        '''
        if not self.equal_to & self.FL:
            reg = self.ram_read(self.pc + 1)
            self.pc = self.register[reg]
        else:
            self.pc += 2

    def handle_JGE(self):
        '''
        If greater-than flag or equal flag is set (true), jump to the address stored in the given register.
        '''
        if self.greater_than & self.FL:
            reg = self.ram_read(self.pc + 1)
            self.pc = self.register[reg]
        else:
            self.pc += 2

    def handle_JEQ(self):
        '''
        If equal flag is set (true), jump to the address stored in the given register.
        '''

        if self.equal_to & self.FL:
            reg = self.ram_read(self.pc + 1)
            self.pc = self.register[reg]
        else:
            self.pc += 2

    def handle_interrupt(self):
        '''
        Run timer interrupt every 1 second
        Check to see if any interrupt status have been triggered.
        If a masked interrupt exists from program code that was executed, run interrupt sequence relevant to that interrupt type
        '''

        # Find current time to check initialized time against. 
        current_time = time.time()

        # We find out if 1 second has passed
        if current_time - self.init_time >=1:
            
            # Reset base time to check against
            self.init_time = time.time() 

            # R6 is reserved for the interrupt_status
            self.register[self.interrupt_status] += 0b00000001 # Interrupt status is on? (0b00000001)

        # If interrupt mask is on and interrupt status is on, this will evaluate to 1
        masked_interrupts = self.register[self.interrupt_mask] & self.register[self.interrupt_status]

        # Check if interrupt status is switched on
        for i in range(8):

            # Right shift interrupts down by i, then mask with 1 to see if that bit was set
            interrupt_happened = ((masked_interrupts >> i) & 1) == 1

            # If a bit is set:
            if interrupt_happened:
                # Based on the type of interrupt, we set the interrupt handler the relevant ram address
                self.interrupt_handler_address = 247 + masked_interrupts

                # Disable further interrupts.
                self.interrupts_enabled = False

                # Clear the bit in the IS register.
                # Reset Interrupt status to 0
                self.register[self.interrupt_status] = 0

                # The PC register is pushed on the stack.
                self.register[self.sp] -= 1
                SP = self.register[self.sp]
                self.ram_write(self.pc, SP)

                # The FL register is pushed on the stack.
                self.register[self.sp] -= 1
                SP = self.register[self.sp]
                self.ram_write(self.FL, SP)
                
                # Registers R0-R6 are pushed on the stack in that order.
                for j in range(7):
                    self.register[self.sp] -= 1
                    SP = self.register[self.sp]
                    self.ram_write(self.register[j], SP)

                # The address (vector in interrupt terminology) of the appropriate handler is looked up from the interrupt vector table.
                # Set the PC is set to the handler address.
                self.pc = self.ram[self.interrupt_handler_address]

                # Stop further checking of maskedInterrupts.
                break

    def handle_NOP(self):
        print("THIS IS NOP. EXITING PROGRAM")
        sys.exit(1)
    
    def handle_PRA(self):
        '''
        Print alpha character value stored in the given register.

        Print to the console the ASCII character corresponding to the value in the register.
        
        '''
        reg = self.ram_read(self.pc + 1)
        print_char = self.register[reg]
        if self.interrupts_enabled == False:
            print(chr(print_char))
        else:
            print(chr(print_char),end="")
        self.pc += 2

    def handle_JMP(self):
        '''
        Jump to the address stored in the given register.
        Set the PC to the address stored in the given register.
        '''
        reg = self.ram_read(self.pc + 1)

        self.pc = self.register[reg]

    def handle_IRET(self):
        '''
        Handle Interrupt return
        Pop all items off the stack back to their original places.
        End interrupt
        '''

        # Registers R6-R0 are popped off the stack in that order.
        for i in range(6, -1, -1):

            SP = self.register[self.sp]
            value = self.ram[SP]
            self.register[i] = value
            self.register[self.sp] += 1

        # The FL register is popped off the stack.
        SP = self.register[self.sp]
        value = self.ram[SP]
        self.FL = value
        self.register[self.sp] += 1

        # The return address is popped off the stack and stored in PC.
        SP = self.register[self.sp]
        value = self.ram[SP]
        self.pc = value
        self.register[self.sp] += 1

        # Interrupts are re-enabled
        self.interrupts_enabled = True

    def handle_ST(self):
        '''
        Take the value in registerB and store in the RAM ADDRESS stored in registerA
        '''
        regA = self.ram[self.pc+1] # 0
        regB = self.ram[self.pc + 2] # 1
        reg_a_value = self.register[regA]
        reg_b_value = self.register[regB] 
        self.ram[reg_a_value] = reg_b_value
        self.pc += 3
    def handle_LD(self):
        '''
        Loads registerA with the value at the RAM address stored in registerB.
        '''
        regA = self.ram[self.pc+1] # 0
        regB = self.ram[self.pc + 2] # 1
        reg_b_value = self.register[regB] 
        self.register[regA] = self.ram[reg_b_value]
        print(f"regA is {regA}")
        print(f"regB is {regB}")
        print(f"reg_b_value is {reg_b_value}")
        self.pc += 3
    def handle_CALL(self):
        '''
        Set the PC to the address of a called subroutine.
        Save the address of the operation that follows CALL in the stack
        '''

        # Push that onto the stack
        self.handle_PUSH(True)

    def handle_RET(self):
        '''
        Pop saved PC address off stack and move PC to that location
        continue operations from there
        '''
        self.handle_POP(True)

    def handle_POP(self, ret = False):
        '''
        Copy value of most recently pushed stack item to given registry address.
        Move stack pointer to previously pushed stack item
        if ret = True, set PC to the popped value and don't save into register
        '''
        SP = self.register[self.sp]
        value = self.ram[SP]

        if not ret:
            reg = self.ram_read(self.pc + 1)
            self.register[reg] = value
            self.pc += 2
        else: # RET POP
            self.pc = value # Move PC back to the next operation after the CALL

        self.register[self.sp] += 1

    def handle_PUSH(self, call = False):
        '''
        Push value from given registry address onto next stack. 
        Leave stack pointer at most recently pushed value
        If call == True, store value of next operation and set pointer to the address saved in the next byte
        '''
        self.register[self.sp] -= 1
        SP = self.register[self.sp]

        if not call:
            reg = self.ram_read(self.pc + 1)
            value = self.register[reg]
            self.pc += 2
        else: # CALL PUSH
            value = self.pc + 2
            self.pc = self.register[self.ram_read(self.pc + 1)]

        self.ram_write(value, SP)

    def handle_LDI(self):
        '''
        Given a registry address and a number, put number into registry.
        '''
        reg = self.ram_read(self.pc + 1)
        num = self.ram_read(self.pc + 2)
        self.register[reg] = num
        self.pc += 3

    def handle_PRN(self):
        '''
        Given a registry address, print number value that exists there
        '''
        reg = self.ram_read(self.pc + 1)
        num = self.register[reg]
        print(num)
        self.pc += 2

    def handle_HLT(self):
        '''
        Halt Program
        '''
        sys.exit(1)

    def handle_MUL(self):
        '''
        Given two registry addresses, 
        multiply them together and save the value in the first registry
        '''
        operand_a = self.ram_read(self.pc + 1)
        operand_b = self.ram_read(self.pc + 2)
        self.alu("MUL", operand_a, operand_b)
        self.pc += 3
    def handle_ADD(self):
        operand_a = self.ram_read(self.pc + 1)
        operand_b = self.ram_read(self.pc + 2)
        self.alu("ADD", operand_a, operand_b)
        self.pc += 3

    def load(self):
        """Load a program into memory."""
        path = sys.argv[1]

        address = 0

        with open(path) as file:
            for line in file:
                if line[0] != "#" and line !='\n':
                    self.ram[address] = int(line[:8], 2)
                    address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        # Can set up ALU branchtable
        if op == "ADD":
            self.register[reg_a] += self.register[reg_b]
        elif op == "MUL":
            self.register[reg_a] *= self.register[reg_b]
            #elif op == "SUB": etc
        elif op =="CMP":
            if self.register[reg_a] < self.register[reg_b]:
                self.FL = self.less_than

            elif self.register[reg_a] == self.register[reg_b]:
                self.FL = self.equal_to

            elif self.register[reg_a] > self.register[reg_b]:
                self.FL = self.greater_than
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
            print(" %02X" % self.register[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        self.init_time = time.time()
        while True:
            self.kbfunc()
            if self.interrupts_enabled:
                self.handle_interrupt()
            IR = self.ram[self.pc]
            self.branchtable[IR]()

    def ram_read(self, MAR):
        '''
        Read a value from a given ram index
        '''
        return self.ram[MAR]

    def ram_write(self, MDR, MAR):
        '''
        Write a value into a given ram index
        '''
        self.ram[MAR] = MDR