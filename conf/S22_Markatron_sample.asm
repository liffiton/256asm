# Meaningless code demonstrating each of the different instructions
label1:
  add $0 $1 $2
  sub $branch $zero $input
  seti $8 -128
  rand $5
  sb $5 $15
  lb $5 $15
label2:
  j label1
  j label2
  j label1
  beq label2 $zero
  bgt label2 $zero
  blt label2 $zero
