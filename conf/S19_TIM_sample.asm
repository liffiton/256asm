# Example TIM ISA code

again:
    add $1 $2 $3
    addi $4 $5 6
    beq $0 $0 again
    andi $1 $7 0b101010
    sb $1 $2 $0
    lb $3 $5 $7
    slt $1 $3 $0
