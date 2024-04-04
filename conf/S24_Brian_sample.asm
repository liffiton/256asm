# Meaningless code demonstrating each of the different instructions
label1:
  lb $0 $1
  sb $2 $3
  add $3 $4 $5
  sub $6 $7 $0
  move $1 $2
 
  addi $3 45
  seti $6 7
  
  jr $ra

label2:
  jal label1
  jal label2
  jal label1
  beq $0 label1
  bne $1 label2
  blt $3 label1
