################################################################################
"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""
################################################################################

# Import Requirements
import re

from selprotopy.common import ieee_4_byte_fps

# Define Clean Prompt Characters for RegEx
RE_CLEAN_PROMPT_CHARS = re.compile(r'\=\r\n')

# Define DNA Control Character String for RegEx
RE_DNA_CONTROL = re.compile(r'\>?.*DNA')

# Define ID Block for RegEx
RE_ID_BLOCK_1 = re.compile(r'''"FID\=(SEL.*)","(\w*)"''')
RE_ID_BLOCK_2 = re.compile(r'''"BFID\=(\w.*)","(\w*)"''')
RE_ID_BLOCK_3 = re.compile(r'''"CID\=(\w*)","(\w*)"''')
RE_ID_BLOCK_4 = re.compile(r'''"DEVID\=(.*)","(\w*)"''')
RE_ID_BLOCK_5 = re.compile(r'''"DEVCODE\=(\w*)","(\w*)"''')
RE_ID_BLOCK_6 = re.compile(r'''"PARTNO\=(\w*)","(\w*)"''')
RE_ID_BLOCK_7 = re.compile(r'''"CONFIG\=(\d*)","(\w*)"''')
RE_ID_BLOCK_8 = re.compile(r'''"SPECIAL\=(\d*)","(\w*)"''')

RE_ID_BLOCKS = {
    'FID':      RE_ID_BLOCK_1,
    'BFID':     RE_ID_BLOCK_2,
    'CID':      RE_ID_BLOCK_3,
    'DEVID':    RE_ID_BLOCK_4,
    'DEVCODE':  RE_ID_BLOCK_5,
    'PARTNO':   RE_ID_BLOCK_6,
    'CONFIG':   RE_ID_BLOCK_7,
    'SPECIAL':  RE_ID_BLOCK_8,
}

# Define RegEx for Hex Character Replacement
RE_HEX_CHAR = re.compile(r'[^\x20-\x7F]+')

# Define Look-Up-Table for Number of Bytes Associated with an Analog Type
ANALOG_SIZE_LOOKUP = {
    0: 2,
    1: 4,
    2: 8,
    3: 8,
}

# Define Look-Up-Table for Formatting Functions for Various Analog Channel Types
ANALOG_TYPE_FORMATTERS = {
    0: int.from_bytes, # 2-Byte Integer
    1: ieee_4_byte_fps, # 4-Byte IEEE FPS
    2: None, # 8-Byte IEEE FPS
    3: None, # 8-Byte Time Stamp
}