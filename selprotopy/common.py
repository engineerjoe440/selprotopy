"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""

# Import Requirements
import math
import struct


# Define Simple Function to Cast Binary Integer to List of Bools
def int_to_bool_list( number, byte_like=False ):
    """
    `int_to_bool_list`
    
    This function converts an integer to a list of boolean values,
    where the most significant value is stored in the highest point
    of the list. That is, a binary number: 8 would be represented as
    [False, False, False, True]
    
    Parameters
    ----------
    number:     int
                Integer to be converted to list of boolean values
                according to binary representation.
    byte_like:  bool, optional
                Control to verify that the integer is broken into a
                list of booleans that could be composed into a byte
                string object (i.e. length of list is divisible by 8),
                defaults to False.
    
    Returns
    -------
    bin_list:   list of bool
                List of boolean values cast from the binary
                representation of the integer passed to the
                function.
    """
    bin_string = format(number, '04b')
    bin_list = [x == '1' for x in bin_string[::-1]]
    # Extend List of Bytes if Needed
    if byte_like:
        len_needed = ((len(bin_list)//8)+1) * 8
        apnd_list  = [False] * (len_needed - len(bin_list))
        bin_list.extend(apnd_list)
    return bin_list

# Define Simple Function to Cast Binary Representation of IEEE 4-Byte FPS
def ieee4bytefps( binary_bytes, total_digits=7 ):
    """
    
    """
    # Define the Internal Functions to Utilize
    def magnitude(x):
        return 0 if x==0 else int(math.floor(math.log10(abs(x)))) + 1
    def round_total_digits(x, digits=7):
        return round(x, digits - magnitude(x))
    # Perform Calculation
    return round_total_digits(  x=struct.unpack('>f', binary_bytes)[0],
                                digits=total_digits )


# END