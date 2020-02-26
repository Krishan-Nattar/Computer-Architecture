"""CPU functionality."""

import sys
from datetime import datetime, timedelta
import time

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
        # R5 = IM = Interrupt Mask
        # R6 = IS = Interrupt Status
        # R7 = SP = Stack Pointer

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

        self.sp = 7
        self.register[self.sp] = 0xF4 # initialized to point at key press
        # self.time = datetime.now().time()
        # print(datetime.now())
        self.time = time.time()
        self.interrupt_handler_address = 0xf8
        self.interrupt_mask = 5
        self.interrupt_status = 6
        self.interrupts_enabled = True
    def handle_JMP(self):
        '''
        Jump to the address stored in the given register.
        Set the PC to the address stored in the given register.
        '''
        set_pointer = self.ram_read(self.pc + 1)
        self.pc = set_pointer

        pass
    def handle_IRET(self):
        '''
        Handle Interrupt return
        '''
        # While an interrupt is being serviced (between the handler being called and the IRET), further interrupts are disabled.

        # Return from an interrupt handler.
        # The following steps are executed:


        # Registers R6-R0 are popped off the stack in that order.

        # The FL register is popped off the stack.

        # The return address is popped off the stack and stored in PC.

        # Interrupts are re-enabled
        self.interrupts_enabled = True
        pass

    def handle_ST(self):
        '''
        Take the value from registerB and store in the ADDRESS stored in registerB
        '''
        regA = self.register[self.pc+1]
        regB = self.register[self.pc + 2]
        self.ram[regA] = self.register[regB]
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
        
        while True:

            # Prior to instruction fetch, the following steps occur:

            #DONE # The IM register is bitwise AND-ed with the IS register and the results stored as maskedInterrupts.
            
            #DONE # Each bit of maskedInterrupts is checked, starting from 0 and going up to the 7th bit, one for each interrupt.
            
            # TODO
            # If a bit is found to be set, follow the next sequence of steps. 
            
            # DONE # Stop further checking of maskedInterrupts.
            
            '''
            Add the timer interrupt to the LS-8 emulator
            '''

            '''
            Interrupt numbers
            0: Timer interrupt. This interrupt triggers once per second.
            1: Keyboard interrupt. This interrupt triggers when a key is pressed. The value of the key pressed is stored in address 0xF4.
            '''
            # Do we ever need self.interrupts_enabled to actually be False???
            if self.interrupts_enabled:
                current_time = time.time()
                if current_time >= 1:
                    self.time = time.time() # Reset base time to check against

                    # R6 is reserved for the interrupt_status
                    self.register[self.interrupt_status] = 1 # Interrupt status is on? (0b00000001)


                    # TEMP CODE ***********
                    # LDI WILL CREATE THIS FOR US
                    # R5 is our Interrupt Mask slot
                    self.register[self.interrupt_mask] = 0b00000001
                    # TEMP CODE **********

                    
                # If interrupt mask is on and interrupt status is on, this will evaluate to 1
                masked_interrupts = self.register[self.interrupt_mask] & self.register[self.interrupt_status]

                print(f"Masked interrupts is {masked_interrupts}")
                
                # Check if interrupt status is switched on
                for i in range(8):
                    # Right shift interrupts down by i, then mask with 1 to see if that bit was set
                    interrupt_happened = ((masked_interrupts >> i) & 1) == 1

                    # If a bit is set:
                    if interrupt_happened:
                        print(f"Interrupt Happened: {interrupt_happened} i: {i}")
                        # Interrupt can really only happen in i = 1, so why the others?!

                        # Disable further interrupts.
                        self.interrupts_enabled = False

                        # Clear the bit in the IS register.
                        # Reset Interrupt status to 0
                        self.register[self.interrupt_status] = 0



                        '''
                        ***With interrupts, why do we push everything on the stack?***

                        The idea is that if you save the machine state on the stack, then after you service the interrupt you can restore it and seamlessly pick up where you left off.

                        The CPU might have been in the middle of something important when the interrupt occurred, and it'll want to get back to that once the interrupt handler is complete.

                        So we push the general purpose registers and internal registers on the stack, then do interrupt stuff, then restore all those registers from the stack so the CPU can carry on with what it was doing before the interrupt occurred.
                        '''
                        # TODO
                        # The PC register is pushed on the stack.
                        # The FL register is pushed on the stack.
                        # Registers R0-R6 are pushed on the stack in that order.
                        # The address (vector in interrupt terminology) of the appropriate handler is looked up from the interrupt vector table.
                        # Set the PC is set to the handler address.


                        # Stop further checking of maskedInterrupts.
                        break
            else:
                pass

            # # self.trace()
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

