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
    from . import commands
    from .common import int_to_bool_list, ieee4bytefps, eval_checksum
except:
    import commands
    from common import int_to_bool_list, ieee4bytefps, eval_checksum

# Define Clean Prompt Characters for RegEx
RE_CLEAN_PROMPT_CHARS = re.compile(r'^[^\=\r\n\> ]*$')

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
    1: ieee4bytefps, # 4-Byte IEEE FPS
    2: None, # 8-Byte IEEE FPS
    3: None, # 8-Byte Time Stamp
}


# Define Simple Function to Validate Checksum for Byte Array
def _validate_checksum( bytArr ):
    """ Use the last byte in a byte array as checksum to verify preceding bytes. """
    # Assume Valid Message, and Find the Length of the Data
    dataLen = bytArr[2]  # Third Byte, Message Length
    # Collect the Checksum from the Data
    checksum_byte = bytArr[dataLen - 1]  # Extract checksum byte
    data = bytArr[:dataLen - 1]  # Don't include last byte
    if checksum_byte != eval_checksum(data, constrain=True):
        raise ValueError("Invalid Checksum Found for Data Stream.")

# Define Simple Function to Cast Byte Array and Clean Ordering
def _cast_bytearray( data, debug=True ):
    """ Cast the data to a byte-array. """
    offset = data.find(b'\xa5')
    # Determine Invalid Criteria
    if offset == -1:
        # TODO: Make more useful error
        if debug:
            print("Debug Cast Data:", data )
        raise ValueError("Invalid response request.")
    bytArr = bytearray(data)[offset:]
    _validate_checksum( bytArr=bytArr )
    return bytArr


###################################################################################
# Define Clear Prompt Interpreter
def CleanPrompt( data, encoding='utf-8' ):
    """
    """
    if encoding:
        # Decode Bytes
        data = data.decode(encoding)
    match = re.match(RE_CLEAN_PROMPT_CHARS, data)
    if match == None or match.match == '':
        return True
    else:
        return False
###################################################################################
# Define Relay ID Block Parser
def RelayIdBlock( data, encoding='', byteorder='big', signed=True, verbose=False ):
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
            key_result, checksum_chars = re.findall(re_param, idstring)[0]
            # Validate Checksum
            calc_checksum = eval_checksum( f'"{id_key}={key_result}",' )
            checksum = int.from_bytes( bytes.fromhex(checksum_chars),
                                        byteorder=byteorder,
                                        signed=signed )
            if checksum != calc_checksum:
                # TODO Raise more Useful Error
                raise ValueError(f"Invalid Checksum Found for {id_key}")
            # Store the Results
            results[id_key] = key_result
        except KeyError:
            # Store Empty Results
            results[id_key] = ''
            if verbose:
                print(f'Unable to determine {id_key} parameter from relay ID.')
        except:
            print(idstring, re.findall(re_param, idstring))
    # Return Parsed ID Components
    return results

# Define Relay DNA Block Parser
def RelayDnaBlock( data, encoding='', byteorder='big', signed=True, verbose=False ):
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
                # Capture and Clean the Columns
                row = [re.sub(RE_HEX_CHAR, '', target) for target in columns[0:8]]
                # Verify Checksum
                calc_checksum = eval_checksum( '"{}",'.format('","'.join(row)) )
                checksum = int.from_bytes( bytes.fromhex(columns[8]),
                                        byteorder=byteorder,
                                        signed=signed )
                # Indicate Failed Checksum Validation
                if calc_checksum != checksum:
                    # TODO Raise more Useful Error
                    raise ValueError(f"Invalid Checksum Found for {id_key}")
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
    bytArr = _cast_bytearray(data, verbose)
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
            print("Command:",struct['command'])
            print("Length:",struct['length'])
            print("Number of Supported Protocols:",struct['numprotocolsup'])
            print("Fast Meter Message Support:",struct['fmmessagesup'])
            print("Status Flag Support:",struct['statusflagssup'])
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
        # Manage Protocol Specific Data
        struct['protocols'] = []
        struct['fopcommandinfo']  = ''
        struct['fmsgcommandinfo'] = ''
        for _ in range(struct['numprotocolsup']):
            data = int_to_bool_list( bytArr[ind] )
            data.extend([False,False]) # This should be at least two bits
            prot = bytArr[ind+1]
            # Manage SEL-Protocol Types
            if prot == 0:
                proto_desc = {
                    'type'          : 'SEL_STANDARD',
                    'fast_op_en'    : data[0],
                    'fast_msg_en'   : data[1]
                }
                if data[0]:
                    struct['fopcommandinfo'] = commands.FO_CONFIG_BLOCK
                if data[1]:
                    struct['fmsgcommandinfo'] = commands.FAST_MSG_CONFIG_BLOCK
            elif prot == 1:
                proto_desc = {
                    'type'          : 'SEL_LMD',
                    'fast_op_en'    : data[0],
                    'fast_msg_en'   : data[1]
                }
                if data[0]:
                    struct['fopcommandinfo'] = commands.FO_CONFIG_BLOCK
                if data[1]:
                    struct['fmsgcommandinfo'] = commands.FAST_MSG_CONFIG_BLOCK
            elif prot == 2:
                proto_desc = {
                    'type'  : 'MODBUS'
                }
            elif prot == 3:
                proto_desc = {
                    'type'  : 'SY_MAX'
                }
            elif prot == 4:
                proto_desc = {
                    'type'  : 'R_SEL'
                }
            elif prot == 5:
                proto_desc = {
                    'type'  : 'DNP3'
                }
            elif prot == 6:
                proto_desc = {
                    'type'  : 'R6_SEL'
                }
            if verbose:
                print('Protocol Type:',proto_desc['type'])
                if 'fast_op_en' in proto_desc.keys():
                    print('Fast Operate Enable:',proto_desc['fast_op_en'])
                    print('Fast Message Enable:',proto_desc['fast_msg_en'])
            struct['protocols'].append(proto_desc)
            ind += 2
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

# Define Function to Parse a Fast Operate Configuration Block
def FastOpConfigurationBlock( data, byteorder='big', signed=True, verbose=False ):
    """
    `FastOpConfigurationBlock`
    
    Parser for a fast operate configuration block to describe
    the relay's available fast operate options.
    
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
        struct['numbreakers']   = bytArr[3]
        struct['numremotebits'] = int.from_bytes( bytArr[4:6],
                                                  byteorder=byteorder,
                                                  signed=signed )
        struct['pulsesupported']= bytArr[6]
        reservedpoint           = bytArr[7]
        # Iterate Over Breaker Bits
        ind = 8
        struct['breakerconfig'] = []
        for _ in range(struct['numbreakers']):
            struct['breakerconfig'].append({
                'opencode'  : bytArr[ind],
                'closecode' : bytArr[ind+1],
            })
            ind += 2
        # Iterate Over Remote Bits
        struct['remotebitconfig'] = []
        for _ in range(struct['numremotebits']):
            remotebitstruct = {
                'clearcode' : bytArr[ind],
                'setcode'   : bytArr[ind+1],
            }
            ind += 2
            if struct['pulsesupported'] == 1:
                remotebitstruct['pulsecode'] = bytArr[ind]
                ind += 1
            # Append Structure
            struct['remotebitconfig'].append(remotebitstruct)
        if verbose:
            print("Generic Fast Operate Configuration Block Information")
            print("Command:", struct['command'])
            print("Message Length:",struct['length'])
            print("Number of Breakers:",struct['breakerconfig'])
            print("Number of Remote Bits:",struct['numremotebits'])
            print("Pulse Command Supported:",struct['pulsesupported'])
        # Return Structure
        return struct
    except:
        raise ValueError("Invalid data string response")
###################################################################################

###################################################################################
# Define Function to Parse a Fast Meter Response Given the Configuration
def FastMeterBlock( data, definition, dna_def, byteorder='big', signed=True,
        verbose=False ):
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
    dna_def:    list of list of str
                The previously defined relay digital name
                alias reference.
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
        for target_row_index in range(definition['numdigitalbank']):
            # Verify Length of Points
            if definition['numdigitalbank'] != len(dna_def):
                # TODO - Create more useful exception!
                raise ValueError('Number of digital banks does not match DNA definition.')
            # Grab the Applicable Names for this Target Row (byte)
            point_names = dna_def[target_row_index][:8] # grab first 8 entries
            # Grab the list of binary statuses from the target row info
            target_data = int_to_bool_list(bytArr[ind+target_row_index],
                                            byte_like=True, reverse=True)
            target_row = dict(zip(point_names,target_data))
            # Load the Digital Dictionary with new Points
            struct['digitals'].update(target_row)
        # Remove the '*' Key from Dictionary
        struct['digitals'].pop('*')
        # Return the Resultant Structure
        return struct
    except:
        raise ValueError("Invalid data string response")
###################################################################################



# END