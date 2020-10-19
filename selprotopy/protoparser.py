"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""

# Import Requirements
import re
import math
import struct
import binascii

# Local Imports
try:
    from .common import int_to_bool_list, ieee4bytefps
except:
    from common import int_to_bool_list, ieee4bytefps

# Define ID Block for RegEx
RE_ID_BLOCK_1 = re.compile(r'''"FID\=(SEL.*)","(\w*)"''')
RE_ID_BLOCK_2 = re.compile(r'''"BFID\=(SEL.*)","(\w*)"''')
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
    1: ieee4bytefps, # 4-Byte IEEE FPS
    2: None, # 8-Byte IEEE FPS
    3: None, # 8-Byte Time Stamp
}


# Define Simple Function to Cast Byte Array and Clean Ordering
def _cast_bytearray( data ):
    """
    
    """
    offset = data.find(b'\xa5')
    bytArr = bytearray(data)[offset:]
    return bytArr


###################################################################################
# Define Relay ID Block Parser
def RelayIdBlock( data, encoding='', verbose=False ):
    """
    `RelayIdBlock`
    
    Parser for a relay ID/Firmware ID block to describe the relay's
    firmware version, part number, and configuration.
    
    Parameters
    ----------
    data:       str
                The full ID string returned from the relay, may
                optionally be passed as a byte-string if the
                encoding is also described.
    encoding:   str, optional
                Optional encoding format to describe which encoding
                method should be used to decode the data passed.
    verbose:    bool, optional
                Control to optionally utilize verbose printing.
    
    Returns
    -------
    results:    dict of str
                Dictionary containing each of the string results
                from the various ID/FID fields.
    """
    if encoding:
        # Decode Bytes
        idstring = data.decode(encoding)
    else:
        # Pass Data Directly
        idstring = data
    # Iteratively Identify ID Parameters
    results = {}
    for id_key, re_param in RE_ID_BLOCKS.items():
        try:
            # Capture the Important Pieces from the Input
            key_result, checksum = re.findall(re_param, idstring)[0]
            # Store the Results
            results[id_key] = key_result
            results[id_key + '_checksum'] = checksum
        except:
            # Store Empty Results
            results[id_key] = ''
            results[id_key + '_checksum'] = ''
            if verbose:
                print(f'Unable to determine {id_key} parameter from relay ID.')
    # Return Parsed ID Components
    return results

# Define Relay DNA Block Parser
def RelayDnaBlock( data, encoding='', verbose=False ):
    """
    `RelayDnaBlock`
    
    Parser for a relay digital names block to describe the configured
    digital names for a relay.
    
    Parameters
    ----------
    data:       str
                The full DNA string returned from the relay, may
                optionally be passed as a byte-string if the
                encoding is also described.
    encoding:   str, optional
                Optional encoding format to describe which encoding
                method should be used to decode the data passed.
    verbose:    bool, optional
                Control to optionally utilize verbose printing.
    
    Returns
    -------
    binaries:   list of list
                List of the target rows with each element's label.
    """
    dnacontrol = '>DNA'
    if encoding:
        # Decode Bytes
        dnastring = data.decode(encoding)
    else:
        # Pass Data Directly
        dnastring = data
    dnastring = dnastring.upper()
    # Remove the Leading Command if Present
    if dnacontrol in dnastring:
        dnastring = dnastring[dnastring.find(dnacontrol)+len(dnacontrol):]
    # Remove Double Quotes
    dnastring = dnastring.replace('"','')
    # Format the List of Lists
    binaries = []
    for line in dnastring.split('\n'):
        # Verify that Comma is Present
        if ',' in line:
            columns = line.split(',')
            # Attempt Generating Binaries List
            try:
                row = columns[0:8]
                row.append([columns[8]])
                binaries.append( row )
            except:
                if verbose: print(f"Couldn't parse line: {line}")
        else:
            break
    return binaries

# Define Relay Status Bit Name Parser
def RelayBnaBlock( data, encoding='', verbose=False ):
    """
    `RelayBnaBlock`
    
    Parser for a relay bit names block to describe the configured
    bit names for a relay.
    
    Parameters
    ----------
    data:       str
                The full BNA string returned from the relay, may
                optionally be passed as a byte-string if the
                encoding is also described.
    encoding:   str, optional
                Optional encoding format to describe which encoding
                method should be used to decode the data passed.
    verbose:    bool, optional
                Control to optionally utilize verbose printing.
    
    Returns
    -------
    bitnames:   list of list
                List of the target rows with each element's label.
    """
    if encoding:
        # Decode Bytes
        bnastring = data.decode(encoding)
    else:
        # Pass Data Directly
        bnastring = data
    # Remove Double Quotes
    bnastring = bnastring.replace('"','')
    # Iteratively Process Lines
    bitnames = []
    for line in bnastring.split('\n'):
        # Verify that Comma is Present
        if ',' in line:
            entries = line.split(',')
            # Attempt Generating Binaries List
            try:
                names = entries[0:8]
                names.append( [entries[8]] )
                bitnames.append( names )
            except:
                if verbose: print(f"Couldn't parse line: {line}")
        else:
            break
        return bitnames
###################################################################################


###################################################################################
# Define Relay Definition Block Parser
def RelayDefinitionBlock( data, verbose=False ):
    """
    `RelayDefinitionBlock`
    
    Parser for a relay definition block to describe
    the relay's available functional message, control,
    and event blocks
    
    Parameters
    ----------
    data:       bytes
                The full byte-string returned from a
                relay using SEL protocol.
    verbose:    bool, optional
                Control to optionally utilize verbose printing.
    
    Returns
    -------
    struct:     dict
                Dictionary of key-value pairs describing
                the relay's definition block.
    """
    # Capture Byte Array for Parsing
    bytArr = _cast_bytearray(data)
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(bytArr[:2])
        struct['length']        = bytArr[2]
        struct['numprotocolsup']= bytArr[3]
        struct['fmmessagesup']  = bytArr[4]
        struct['statusflagssup']= bytArr[5]
        struct['protocolinfo']  = []
        struct['fmcommandinfo'] = []
        struct['statusflaginfo']= []
        if verbose:
            print("Generic Relay Definition Block Information")
            print(struct['command'])
            print(struct['length'])
            print(struct['numprotocolsup'])
            print(struct['fmmessagesup'])
            print(struct['statusflagssup'])
        # Iterate over the Fast Meter Commands
        ind = 6
        for _ in range(struct['fmmessagesup']):
            dict = {}
            dict['configcommand'] = bytes(bytArr[ind:ind+2])
            dict['command'] = bytes(bytArr[ind+2:ind+4])
            struct['fmcommandinfo'].append(dict)
            ind += 4
        struct['fmtype'] = bytArr[ind]
        if verbose:
            print("Fast Meter Command Information")
            print(struct['fmcommandinfo'],'\n',struct['fmtype'])
        ind += 1
        # Iterate Over the Status Flag Commands
        for _ in range(struct['statusflagssup']):
            dict = {}
            dict['statusbit'] = bytes(bytArr[ind:ind+2])
            dict['affectedcommand'] = bytes(bytArr[ind+2:ind+8])
            struct['statusflaginfo'].append(dict)
            ind += 8
        if verbose:
            print("Status Flag Information")
            print(struct['statusflaginfo'])
        # Return Resultant Structure
        return struct
    except:
        raise ValueError("Invalid data string response")

# Define Relay Definition Block Parser
def FastMeterConfigurationBlock( data, byteorder='big', signed=True, verbose=False ):
    """
    `FastMeterConfigurationBlock`
    
    Parser for a relay's fast meter block to describe
    the relay's available functional message, control,
    and event blocks
    
    Parameters
    ----------
    data:       bytes
                The full byte-string returned from a
                relay using SEL protocol.
    byteorder:  ['big', 'little'], optional
                Control of how bytes are interpreted as
                integers, using big-endian or little-endian
                operations. Defaults to 'big'
    signed:     bool, optional
                Control to specify whether the bytes should
                be interpreted as signed or unsigned integers.
                Defaults to True
    verbose:    bool, optional
                Control to optionally utilize verbose printing.
    
    Returns
    -------
    struct:     dict
                Dictionary of key-value pairs describing
                the relay's fast meter configuration block.
    """
    # Capture Byte Array for Parsing
    bytArr = _cast_bytearray(data)
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(bytArr[:2])
        struct['length']        = bytArr[2]
        struct['numstatusflags']= bytArr[3]
        struct['scalefactloc']  = bytArr[4]
        struct['numscalefact']  = bytArr[5]
        struct['numanalogins']  = bytArr[6]
        struct['numsampperchan']= bytArr[7]
        struct['numdigitalbank']= bytArr[8]
        struct['numcalcblocks'] = bytArr[9]
        # Determine Offsets
        struct['analogchanoff'] = int.from_bytes( bytArr[10:12],
                                                  byteorder=byteorder,
                                                  signed=signed )
        struct['timestmpoffset']= int.from_bytes( bytArr[12:14],
                                                  byteorder=byteorder,
                                                  signed=signed )
        struct['digitaloffset'] = int.from_bytes( bytArr[14:16],
                                                  byteorder=byteorder,
                                                  signed=signed )
        # Iteratively Interpret the Analog Channels
        ind = 16
        struct['analogchannels'] = []
        for _ in range(struct['numanalogins']):
            dict = {}
            bytstr = bytes(bytArr[ind:ind+6])
            dict['name'] = ''
            for byte in bytstr:
                char = chr(byte)
                if byte != 0:
                    dict['name']    += char
            ind += 6
            dict['channeltype'] = bytArr[ind]
            dict['factortype']  = bytArr[ind+1]
            dict['scaleoffset'] = int.from_bytes( bytArr[ind:ind+2],
                                                  byteorder=byteorder,
                                                  signed=signed )
            ind += 4
            # Append the Analog Channel Description:
            struct['analogchannels'].append( dict )
        # Iteratively Interpret the Calculation Blocks
        struct['calcblocks'] = []
        for _ in range(struct['numcalcblocks']):
            dict = {}
            # Determine the Line Configuration
            # rot:      Rotation
            # vConDP:   Delta Connected, Positive Sequence
            # vConDN:   Delta Connected, Negative Sequence
            # iConDP:   Delta Connected, Positive Sequence
            # iConDN:   Delta Connected, Negative Sequence
            val = bytArr[ind]
            [rot, vConDP, vConDN, iConDP, iConDN, na, na, na] = int_to_bool_list( val,
                byte_like=True)
            # Evaluate Rotation
            dict['line'] = val
            dict['rotation'] = 'ACB' if rot else 'ABC'
            # Evaluate Voltage Connection
            if vConDN:
                dict['voltage'] = 'AC-BA-CB'
            elif vConDP:
                dict['voltage'] = 'AB-BC-CA'
            else:
                dict['voltage'] = 'Y'
            # Evaluate Current Connection
            if iConDN:
                dict['current'] = 'AC-BA-CB'
            elif iConDP:
                dict['current'] = 'AB-BC-CA'
            else:
                dict['current'] = 'Y'
            ind += 1
            # Determine the Calculation Type
            val = bytArr[ind]
            dict['type'] = val
            ind += 1
            if val == 0:
                dict['typedesc'] = 'standard-power'
            elif val == 1:
                dict['typedesc'] = '2-1/2 element Δ power'
            elif val == 2:
                dict['typedesc'] = 'voltages only'
            elif val == 3:
                dict['typedesc'] = 'currents only'
            elif val == 4:
                dict['typedesc'] = 'single-phase IA and VA only'
            elif val == 5:
                dict['typedesc'] = 'standard-power with two sets of currents'
            else:
                dict['typedesc'] = '2-1/2 element Δ power with two sets of currents'
            # Determine Skew Correction offset, Rs offset, and Xs offset
            dict['skewoffset'] = bytes(bytArr[ind:ind+2])
            dict['rsoffset'] = bytes(bytArr[ind+2:ind+4])
            dict['xsoffset'] = bytes(bytArr[ind+4:ind+6])
            # Determine Current Indicies
            ind += 1
            dict['iaindex'] = bytArr[ind+0]
            dict['ibindex'] = bytArr[ind+1]
            dict['icindex'] = bytArr[ind+2]
            dict['vaindex'] = bytArr[ind+3]
            dict['vbindex'] = bytArr[ind+4]
            dict['vcindex'] = bytArr[ind+5]
            # Store Dictionary
            struct['calcblocks'].append(dict)
        if verbose:
            print("Generic Fast Meter Configuration Block Information")
            print("Command:", struct['command'])
            print("Message Length:",struct['length'])
            print("Number of Status Flags:",struct['numstatusflags'])
            print("Scale Factor Location:",struct['scalefactloc'])
            print("Number of Scale Factors:",struct['numscalefact'])
            print("Number of Analog Inputs:",struct['numanalogins'])
            print("Number of Samples per Channel:",struct['numsampperchan'])
            print("Number of Digital Banks:",struct['numdigitalbank'])
            print("Number of Calculation Blocks:",struct['numcalcblocks'])
            print("Analog Channel Offset:",struct['analogchanoff'])
            print("Time Stamp Offset:",struct['timestmpoffset'])
            print("Digital Channel Offset:",struct['digitaloffset'])
        # Return the Generated Structure
        return struct
    except:
        raise ValueError("Invalid data string response")
###################################################################################

###################################################################################
# Define Function to Parse a Fast Meter Response Given the Configuration
def FastMeterBlock( data, definition, byteorder='big', signed=True, verbose=False ):
    """
    `FastMeterBlock`
    
    Parser for a relay's fast meter block for the various analog
    and digital points.
    
    Parameters
    ----------
    data:       bytes
                The full byte-string returned from a
                relay using SEL protocol.
    definition: struct
                The previously defined relay definition
                for the applicable fast meter block.
    byteorder:  ['big', 'little'], optional
                Control of how bytes are interpreted as
                integers, using big-endian or little-endian
                operations. Defaults to 'big'
    signed:     bool, optional
                Control to specify whether the bytes should
                be interpreted as signed or unsigned integers.
                Defaults to True
    verbose:    bool, optional
                Control to optionally utilize verbose printing.
    
    Returns
    -------
    struct:     dict
                Dictionary of key-value pairs describing
                the relay's fast meter data points.
    """
    # Capture Byte Array for Parsing
    bytArr = _cast_bytearray( data )
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(bytArr[:2])
        struct['length']        = bytArr[2]
        struct['statusflag']    = bytArr[3:3+definition['numstatusflags']]
        if verbose:
            print("Generic Fast Meter Block Information")
            print("Command:", struct['command'])
            print("Message Length:",struct['length'])
            print("Status Flag:",struct['statusflag'])
        # Handle Analog Points
        struct['analogs'] = {}
        ind = definition['analogchanoff']
        samples = definition['numsampperchan']
        # Iterate over Samples
        for samp_n in range(samples):
            # Iterate over Analogs
            for analog_desc in definition['analogchannels']:
                name = analog_desc['name']
                type = analog_desc['channeltype']
                size = ANALOG_SIZE_LOOKUP[type]
                scale_type = analog_desc['factortype']
                # Handle Non-Scaling Values
                if scale_type == 255:
                    scale = 1
                # Extract Value to be Interpreted
                value = bytes(bytArr[ind:ind+size])
                # Apply Formatting
                value = ANALOG_TYPE_FORMATTERS[type]( value )
                # Evaluate Result
                analog_data = value*scale
                # Handle Different Analog Sample Types
                if samples == 1:        # Each is Magnitude
                    # Record Magnitude Directly
                    struct['analogs'][name] = analog_data
                elif samples == 2:      # Set of Imaginary, Real Group
                    # Manage Real/Imaginary Quantities
                    if samp_n == 0: # Imaginary
                        if analog_data > 1e-8:
                            struct['analogs'][name] = analog_data * 1j
                        else:
                            struct['analogs'][name] = 0
                    else:          # Real
                        struct['analogs'][name] += analog_data
                else:                   # 1st, 2nd, 5th, 6th qtr cycle
                    if samp_n == 0:
                        struct['analogs'][name] = [analog_data]
                    else:
                        struct['analogs'][name].append(analog_data)
                ind += size
                if verbose: print("Analog {}: {}".format(name,analog_data))
        # Iteratively Handle Digital Points
        struct['digitals'] = {}
        ind = definition['digitaloffset']
        print("Digital Offset",ind)
        # Return the Resultant Structure
        return struct
    except:
        raise ValueError("Invalid data string response")
###################################################################################



# END