start:
  add $0 $1
  addi $1 2
  assigni $2 3
  sub $3 $4
  load $4 $5
  store $5 $6
stop:
  beq $6 start
  bne $7 stop
  in $7 $6
  out $6 $5
  sgt $5 $4
  rand $4 3
