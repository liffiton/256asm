# PingPong in GoTwoAssembly
#
# Authors: Duc Tran and Ryan Ozelie
# Date: April, 2018
#
# All variables
#    ballPos: x/y $1,$2 (x is horizontal)
#    ballPixel $14
#    direction: horizontal/vertical (+1/-1) $3,$4
#    left pad (+8 for 'mid' pixel) $5
#    right pad (+8 for 'mid' pixel) $6
#    left pad score $8 (store as pixel position, display from left of bottom row)
#    right pad score $9 (store as pixel position, display from right of bottom row)

# initialize special registers, reduct seti instruction
    seti $13 8             #also 1000
    seti $12 4             #also 0100
    seti $11 2             #also 0010
    seti $10 1             #also 0001

# initialize
resetScore:
    seti $8 55             #score left pad, currently 0
    seti $9 64             #score right pad, currently 0
    
    #clear all scoring pixels
    seti $7 56
    out $7 0
    addi $7 1
    out $7 0
    addi $7 1
    out $7 0
    addi $7 1
    out $7 0
    addi $7 1
    out $7 0
    addi $7 1
    out $7 0
    addi $7 1
    out $7 0
    addi $7 1
    out $7 0
reset:        
    out $5 0               #clear pad1
    addi $5 8
    out $5 0
    addi $5 8
    out $5 0
    out $6 0               #clear pad2
    addi $6 8
    out $6 0
    addi $6 8
    out $6 0
start:
    #turn off previous ball
    out $14 0

    seti $5 8              #initialize pad1
    seti $6 15             #initialize pad2

    out $5 1               #out pad1 1st pixel
    add $7 $5 $13
    out $7 1               #out pad1 2nd pixel
    add $7 $7 $13
    out $7 1               #out pad1 3rd pixel

    out $6 1               #out pad2 1st pixel
    add $7 $6 $13
    out $7 1               #out pad2 2nd pixel
    add $7 $7 $13
    out $7 1               #out pad2 3rd pixel
     
    seti $1 1              #initialize x,y
    seti $2 1
    seti $3 1              #initialize direction
    seti $4 1
    add $7 $2 $2          #multiply y by 8
    add $7 $7 $7
    add $7 $7 $7
    add $7 $7 $1          #add x for ball pixel
    out $7 1               #out ball
    add $14 $zero $7      #always keep ball display pos in $14 update after every loop
    
updateLoop:
    add $1 $1 $3          #update x
    add $2 $2 $4          #update y

    add $7 $2 $2          #multiply y by 8
    add $7 $7 $7
    add $7 $7 $7
    add $7 $7 $1          #add x for ball pixel
    out $14 0
    out $7 1
    add $14 $zero $7      #update ball pixel

#check ball die
checkBallDie:
    bz $1 scoreleft        #die on left edge
    seti $7 7
    sub $7 $1 $7
    bz $7 scoreright       #die on right edge

# check pad contact with horizontal position
leftPadContact:
    sub $7 $3 $10         #right or left?
    bz $7 rightPadContact  #right pad
    add $7 $zero $14      #left pad
    addi $7 -1
    sub $7 $7 $5
    bz $zero padContact
rightPadContact:
    add $7 $zero $14
    addi $7 1
    sub $7 $7 $6
padContact:
    bz $7 reverseX         #check for match with pad-8/pad-16/pad-24
    addi $7 -8
    bz $7 reverseX
    addi $7 -8
    bz $7 reverseX
    bz $zero cornerPad     #no contact then skip to next check
reverseX:
    seti $7 1
    sub $7 $3 $7
    bz $7 xToLeft          #change direction to left
    seti $3 1              #change direction to right
    bz $zero checkY
xToLeft:
    seti $3 -1
    bz $zero checkY

# check corner case
cornerPad:
    # top corner?
    sub $7 $4 $10         #what vertical direction? if 1 check top case, else check bot case
    bz $7 topCorner
    bz $zero botCorner

topCorner:
    #top left corner
    sub $7 $5 $13         #subtract 8 from pad 'high' pixel
    addi $7 1              #add 1 to match with ball pixel
    sub $7 $7 $14
    bz $7 reverseXY

    # top right corner
    sub $7 $6 $13         #subtract 8 from pad 'high' pixel
    addi $7 -1             #subtract 1 to match with ball pixel
    sub $7 $7 $14
    bz $7 reverseXY
    bz $zero checkY        #no need to reverse, skip to next check

# bottom corner
botCorner:
    #botom left corner
    seti $7 25
    add $7 $5 $7          #add 25 for 'low' pad pixel+1
    sub $7 $7 $14         #check if match ball pixel
    bz $7 reverseXY

    #bottom right corner
    seti $7 23
    add $7 $6 $7          #add 23 for 'low' pad pixel-1
    sub $7 $7 $14         #check if match ball pixel
    bz $7 reverseXY
    bz $zero checkY        #no need to reverse, skip to next check

#reverse in corner case
reverseXY:
    sub $7 $3 $10         #check if x-direction equal to 1
    bz $7 xToNegative
    seti $3 1
    bz $zero reverseY 
xToNegative:
    seti $3 -1

reverseY:
    sub $7 $4 $10         #check if y-direction equal to 1
    bz $7 yToNegative
    seti $4 1
    bz $zero checkY
yToNegative:
    seti $4 -1

# check contact with top/bottom edge
checkY:
    bz $2 ydirUp           #at top edge?
    seti $7 6
    sub $7 $2 $7
    bz $7 ydirDown         #at bottom edge?
    bz $zero input
ydirUp:
    seti $4 1
    bz $zero input
ydirDown:
    seti $4 -1

#input check and update pad
input:
    and $7 $13 $input     #first button - pad1 down
    bz $7 Btn2
    out $5 0               #turn off top pixel
    addi $5 8
    seti $7 16             #turn on pixel 2 blocks away
    add $7 $5 $7
    out $7 1
Btn2:
    and $7 $12 $input     #second button - pad1 up
    bz $7 Btn3
    addi $5 -8
    out $5 1
    seti $7 24             #turn off pixel 3 blocks away from $5
    add $7 $5 $7
    out $7 0
Btn3:
    and $7 $11 $input     #third button - pad2 down
    bz $7 Btn4
    out $6 0
    addi $6 8
    seti $7 16
    add $7 $6 $7
    out $7 1 
Btn4:
    and $7 $10 $input     #forth button - pad2 up
    bz $7 done
    addi $6 -8
    out $6 1
    seti $7 24
    add $7 $6 $7
    out $7 0
done:
    bz $zero updateLoop    #end of game loop

#scoring left pad
scoreright:
    addi $8 1              #increment score
    out $8 1
    seti $7 59             #win when score pixel reach 59
    sub $7 $8 $7
    bz $7 resetScore       #reset match
    bz $zero reset         #next game

#scoring right pad
scoreleft:
    addi $9 -1
    out $9 1
    seti $7 60             #win when score pixel reach 60
    sub $7 $9 $7
    bz $7 resetScore       #reset match
    bz $zero reset         #next game
