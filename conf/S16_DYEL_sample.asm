# Example DYEL ISA code
# Lights up LEDs, then turns them off, repeatedly.
# Pressing any button changes direction.

    # $1 = 0 (current pixel address)
    sub $1 $1
    # $2 = 63 (constant 63: highest pixel address)
    sub $2 $2
    addi $2 63

up:
    light $1 1   # turn on current pixel
    addi $1 1    # move to next
    # check whether $1 is 63 yet using $6 as temp register
    # NOTE: this should check if it's 64 (one above highest),
    #       but if we only have 6-bit registers.....
    copy $6 $1
    sub $6 $2
    zj $6 down    # change direction if we hit the last address
    zj $input up  # continue as long as no button is pressed
    # fall through to change direction if button *is* pressed

down:
    light $1 0  # turn off current pixel
    addi $1 -1  # move to next
    # check whether $1 is 0 yet
    zj $1 up        # change direction if we hit zero
    zj $input down  # continue as long as no button is pressed
    zj $zero up     # change direction if button *is* pressed
