import sys

PRINT_BEEJ = 1
HALT = 2
PRINT_NUM = 3
SAVE = 4 # Save a value to a register
PRINT_REGISTER = 5 # PRint a value in a register
ADD = 6 # ADD 2 registers. Store the results in the first register


memory = [
    PRINT_BEEJ,
    SAVE, # SAVE 65 in R2
    65,
    2,
    SAVE, # SAVE 20 in R3
    20,
    3,
    ADD, # R2 += R3
    2,
    3,
    PRINT_REGISTER, # PRINT R2
    2,
    HALT
]
pc = 0 

register = [0] * 8

while True:
    command = memory[pc]

    if command == PRINT_BEEJ:
        print("BEEJ")
        pc += 1
    elif command == PRINT_NUM:
        num = memory[pc + 1]
        print(num)
        pc += 2
    elif command == SAVE:
        num = memory[pc + 1] 
        reg = memory[pc + 2]
        register[reg] = num
        pc += 3
    elif command == PRINT_REGISTER:
        reg = memory[pc+1]
        print(register[reg])
        pc += 2
    elif command == ADD:
        reg_a = memory[pc+1]
        reg_b = memory[pc+2]
        register[reg_a] += register[reg_b]
        pc += 3
    elif command == HALT:
        # HALT
        sys.exit(1)
    else:
        print("I DID NOT UNDERSTAND THAT COMMAND")
        sys.exit(1)
