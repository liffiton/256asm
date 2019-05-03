# Example SAM ISA code
# Lights up LEDs, then turns them off, repeatedly.
# Pressing any button changes direction.

    # ~0 = 0 (constant 0)
    seti ~0 0
    # ~1 = 1 (constant 1: for sending to LED output)
    seti ~1 1
    # ~2 = 63 (constant 63: highest pixel address)
    seti ~2 63
    # ~3 = 0 (current pixel address)
    seti ~3 0

up:
    out ~1 ~3    # turn on current pixel
    addi ~3 1    # move to next pixel
    # check whether address (~3) is 63; move to down if so
    seti ~7 0    # first, copy 63 into BEQ special register ~7
    add ~7 ~2
    beq ~3 down  # change direction if we hit the last address
    in ~4 ~0     # read from address 0 (button)
    seti ~7 0    # setup 0 value for comparison
    beq ~4 up    # continue w/ same direction if button value = 0
    # fall through to change direction if button *is* pressed

down:
    out ~0 ~3   # turn off current pixel
    addi ~3 -1  # move to next pixel
    # check whether ~3 is 0 yet; move to up if so
    seti ~7 0
    beq ~3 up   # change direction if we hit zero
    in ~4 ~0    # read from address 0 (button)
    beq ~4 down # continue w/ same direction if button value = 0
    beq ~7 up   # otherwise change direction (unconditional jump)
