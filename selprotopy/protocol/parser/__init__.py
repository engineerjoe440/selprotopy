################################################################################
"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""
################################################################################

from typing import AnyStr, List

# Local Imports
from selprotopy.protocol import commands
from selprotopy.common import int_to_bool_list, eval_checksum
from selprotopy.exceptions import MalformedByteArray, ChecksumFail
from selprotopy.exceptions import MissingA5Head, DnaDigitalsMisMatch
from selprotopy.protocol.parser import common


# Define Simple Function to Validate Checksum for Byte Array
def _validate_checksum(byte_array: bytearray):
    """Use last byte in a byte array as checksum to verify preceding bytes."""
    # Assume Valid Message, and Find the Length of the Data
    data_length = byte_array[2]  # Third Byte, Message Length
    # Collect the Checksum from the Data
    try:
        checksum_byte = byte_array[data_length - 1]  # Extract checksum byte
    except IndexError as err:
        # Indicate Malformed Byte Array
        raise MalformedByteArray(
            f"Length of byte array extracted ({data_length}) appears invalid. "
            f"Attempted extracting byte at position {data_length-1} but length "
            f"is {len(byte_array)}."
        ) from err
    data = byte_array[:data_length - 1]  # Don't include last byte
    confirmed = eval_checksum(data, constrain=True)
    if checksum_byte != confirmed:
        raise ChecksumFail(
            "Invalid Checksum Found for Data Stream. "+
            f"Found: '{checksum_byte}'; Expected: '{confirmed}' \n{byte_array}"
        )

# Simple Function to Cast Byte Array and Clean Ordering
def _cast_bytearray(data: AnyStr, debug: bool = True):
    """Cast the data to a byte-array."""
    offset = data.find(b'\xa5')
    # Determine Invalid Criteria
    if offset == -1:
        # Indicate that response is missing 'A5' binary heading
        if debug:
            print("Debug Cast Data:", data )
        raise MissingA5Head(
            "Invalid response request; missing 'A5' binary heading."
        )
    byte_array = bytearray(data)[offset:]
    # Strip any Trailing Characters that are Not Needed
    if commands.LEVEL_0 in byte_array:
        byte_array = byte_array.split(commands.LEVEL_0)[0]
    if byte_array.endswith(commands.CR):
        byte_array = byte_array[:-2]
    _validate_checksum( byte_array=byte_array )
    return byte_array


################################################################################
# Define Clear Prompt Interpreter
def clean_prompt(data: AnyStr, encoding: str = 'utf-8' ):
    """Repeatedly use Carriage-Returns to Clear the Prompt for new Commands."""
    if encoding:
        # Decode Bytes
        try:
            data = data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return common.RE_CLEAN_PROMPT_CHARS.search(data) is not None

################################################################################
# Define Relay ID Block Parser
def relay_id_block(data: AnyStr, encoding: str = '', byteorder: str = 'big',
                   signed: bool = True, verbose: bool = False):
    """
    Parse Relay ID Block.

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
        id_string = data.decode(encoding)
    else:
        # Pass Data Directly
        id_string = data
    # Iteratively Identify ID Parameters
    results = {}
    for id_key, re_param in common.RE_ID_BLOCKS.items():
        try:
            # Capture the Important Pieces from the Input
            key_result, checksum_chars = re_param.findall(id_string)[0]
            # Validate Checksum
            calc_checksum = eval_checksum( f'"{id_key}={key_result}",' )
            checksum = int.from_bytes( bytes.fromhex(checksum_chars),
                                        byteorder=byteorder,
                                        signed=signed )
            if checksum != calc_checksum:
                # Indicate Checksum Failure
                raise ChecksumFail(f"Invalid Checksum Found for {id_key}")
            # Store the Results
            results[id_key] = key_result
        except KeyError:
            # Store Empty Results
            results[id_key] = ''
            if verbose:
                print(f'Unable to determine {id_key} parameter from relay ID.')
        except Exception:
            print(id_string, re_param.findall(id_string))
    # Return Parsed ID Components
    return results

# Define Relay DNA Block Parser
def relay_dna_block(data: AnyStr, encoding: str = '', byteorder: str = 'big',
                    signed: bool = True, verbose: bool = False):
    """
    Parse Relay DNA Response Block.

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
    if encoding:
        # Decode Bytes
        dna_string = data.decode(encoding)
    else:
        # Pass Data Directly
        dna_string = data
    dna_string = dna_string.upper()
    # Remove the Leading Command if Present
    if common.RE_DNA_CONTROL.search(dna_string) is not None:
        dna_string = common.RE_DNA_CONTROL.split(dna_string)[1]
    # Remove Double Quotes
    dna_string = dna_string.replace('"','')
    # Format the List of Lists
    binaries = []
    for line in dna_string.split('\n'):
        # Verify that Comma is Present
        if ',' in line:
            columns = line.split(',')
            # Attempt Generating Binaries List
            try:
                # Capture and Clean the Columns
                row = [
                    common.RE_HEX_CHAR.sub('', target) for target in columns[0:8]
                ]
                # Verify Checksum
                calc_checksum = eval_checksum(
                    '"{}",'.format('","'.join(row))
                )
                checksum = int.from_bytes(
                    bytes.fromhex(columns[8]),
                    byteorder=byteorder,
                    signed=signed
                )
                # Indicate Failed Checksum Validation
                if calc_checksum != checksum:
                    # Indicate Checksum Failure
                    raise ChecksumFail(f"Invalid Checksum Found for {line}")
                binaries.append( row )
            except Exception:
                if verbose: print(f"Couldn't parse line: {line}")
    return binaries

# Define Relay Status Bit Name Parser
def RelayBnaBlock(data: AnyStr, encoding: str = '', verbose: bool = False):
    """
    Parse Relay BNA Response Block.

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
    list[list[str]]: List of the target rows with each element's label.
    """
    if encoding:
        # Decode Bytes
        bna_string = data.decode(encoding)
    else:
        # Pass Data Directly
        bna_string = data
    # Remove Double Quotes
    bna_string = bna_string.replace('"','')
    # Iteratively Process Lines
    bit_names = []
    for line in bna_string.split('\n'):
        # Verify that Comma is Present
        if ',' in line:
            entries = line.split(',')
            # Attempt Generating Binaries List
            try:
                names = entries[0:8]
                names.append( [entries[8]] )
                bit_names.append( names )
            except Exception:
                if verbose:
                    print(f"Couldn't parse line: {line}")
        else:
            break
        return bit_names
################################################################################


################################################################################
# Define Relay Definition Block Parser
def relay_definition_block(data: AnyStr, verbose: bool = False):
    """
    Parse Relay Definition Block.

    Parser for a relay definition block to describe the relay's available
    functional message, control, and event blocks.

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
    byre_array = _cast_bytearray(data, verbose)
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(byre_array[:2])
        struct['length']        = byre_array[2]
        struct['numprotocolsup']= byre_array[3]
        struct['fmmessagesup']  = byre_array[4]
        struct['statusflagssup']= byre_array[5]
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
            data_dict = {}
            data_dict['configcommand'] = bytes(byre_array[ind:ind+2])
            data_dict['command'] = bytes(byre_array[ind+2:ind+4])
            struct['fmcommandinfo'].append(data_dict)
            ind += 4
        struct['fmtype'] = byre_array[ind]
        if verbose:
            print("Fast Meter Command Information")
            print(struct['fmcommandinfo'],'\n',struct['fmtype'])
        ind += 1
        # Iterate Over the Status Flag Commands
        for _ in range(struct['statusflagssup']):
            data_dict = {}
            data_dict['statusbit'] = bytes(byre_array[ind:ind+2])
            data_dict['affectedcommand'] = bytes(byre_array[ind+2:ind+8])
            struct['statusflaginfo'].append(data_dict)
            ind += 8
        if verbose:
            print("Status Flag Information")
            print(struct['statusflaginfo'])
        # Manage Protocol Specific Data
        struct['protocols'] = []
        struct['fopcommandinfo']  = ''
        struct['fmsgcommandinfo'] = ''
        for _ in range(struct['numprotocolsup']):
            data = int_to_bool_list( byre_array[ind] )
            data.extend([False,False]) # This should be at least two bits
            prot = byre_array[ind+1]
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
    except IndexError as err:
        raise ValueError("Invalid data string response") from err

# Define Relay Definition Block Parser
def fast_meter_configuration_block(data: AnyStr, byteorder: str = 'big',
                                   signed: bool = True, verbose: bool = False):
    """
    Parse Relay Fast Meter Configuration Block.

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
    byte_arr = _cast_bytearray(data)
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(byte_arr[:2])
        struct['length']        = byte_arr[2]
        struct['numstatusflags']= byte_arr[3]
        struct['scalefactloc']  = byte_arr[4]
        struct['numscalefact']  = byte_arr[5]
        struct['numanalogins']  = byte_arr[6]
        struct['numsampperchan']= byte_arr[7]
        struct['numdigitalbank']= byte_arr[8]
        struct['numcalcblocks'] = byte_arr[9]
        # Determine Offsets
        struct['analogchanoff'] = int.from_bytes(
            byte_arr[10:12],
            byteorder=byteorder,
            signed=signed
        )
        struct['timestmpoffset']= int.from_bytes(
            byte_arr[12:14],
            byteorder=byteorder,
            signed=signed
        )
        struct['digitaloffset'] = int.from_bytes(
            byte_arr[14:16],
            byteorder=byteorder,
            signed=signed
        )
        # Iteratively Interpret the Analog Channels
        ind = 16
        struct['analogchannels'] = []
        for _ in range(struct['numanalogins']):
            data_dict = {}
            bytstr = bytes(byte_arr[ind:ind+6])
            data_dict['name'] = ''
            for byte in bytstr:
                char = chr(byte)
                if byte != 0:
                    data_dict['name']    += char
            ind += 6
            data_dict['channeltype'] = byte_arr[ind]
            data_dict['factortype']  = byte_arr[ind+1]
            data_dict['scaleoffset'] = int.from_bytes(
                byte_arr[ind:ind+2],
                byteorder=byteorder,
                signed=signed
            )
            ind += 4
            # Append the Analog Channel Description:
            struct['analogchannels'].append( data_dict )
        # Iteratively Interpret the Calculation Blocks
        struct['calcblocks'] = []
        for _ in range(struct['numcalcblocks']):
            data_dict = {}
            # Determine the Line Configuration
            # rot:      Rotation
            # vConDP:   Delta Connected, Positive Sequence
            # vConDN:   Delta Connected, Negative Sequence
            # iConDP:   Delta Connected, Positive Sequence
            # iConDN:   Delta Connected, Negative Sequence
            val = byte_arr[ind]
            [rot, vConDP, vConDN, iConDP, iConDN, _, _, _] = int_to_bool_list(
                val,
                byte_like=True
            )
            # Evaluate Rotation
            data_dict['line'] = val
            data_dict['rotation'] = 'ACB' if rot else 'ABC'
            # Evaluate Voltage Connection
            if vConDN:
                data_dict['voltage'] = 'AC-BA-CB'
            elif vConDP:
                data_dict['voltage'] = 'AB-BC-CA'
            else:
                data_dict['voltage'] = 'Y'
            # Evaluate Current Connection
            if iConDN:
                data_dict['current'] = 'AC-BA-CB'
            elif iConDP:
                data_dict['current'] = 'AB-BC-CA'
            else:
                data_dict['current'] = 'Y'
            ind += 1
            # Determine the Calculation Type
            val = byte_arr[ind]
            data_dict['type'] = val
            ind += 1
            if val == 0:
                data_dict['typedesc'] = 'standard-power'
            elif val == 1:
                data_dict['typedesc'] = '2-1/2 element Δ power'
            elif val == 2:
                data_dict['typedesc'] = 'voltages only'
            elif val == 3:
                data_dict['typedesc'] = 'currents only'
            elif val == 4:
                data_dict['typedesc'] = 'single-phase IA and VA only'
            elif val == 5:
                data_dict['typedesc'] = \
                    'standard-power with two sets of currents'
            else:
                data_dict['typedesc'] = (
                    '2-1/2 element Δ power with two sets of currents'
                )
            # Determine Skew Correction offset, Rs offset, and Xs offset
            data_dict['skewoffset'] = bytes(byte_arr[ind:ind+2])
            data_dict['rsoffset'] = bytes(byte_arr[ind+2:ind+4])
            data_dict['xsoffset'] = bytes(byte_arr[ind+4:ind+6])
            # Determine Current Indicies
            ind += 1
            data_dict['iaindex'] = byte_arr[ind+0]
            data_dict['ibindex'] = byte_arr[ind+1]
            data_dict['icindex'] = byte_arr[ind+2]
            data_dict['vaindex'] = byte_arr[ind+3]
            data_dict['vbindex'] = byte_arr[ind+4]
            data_dict['vcindex'] = byte_arr[ind+5]
            # Store Dictionary
            struct['calcblocks'].append(data_dict)
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
    except IndexError as err:
        raise ValueError("Invalid data string response") from err

# Define Function to Parse a Fast Operate Configuration Block
def fast_op_configuration_block(data: AnyStr, byteorder: str = 'big',
                                signed: bool = True, verbose: bool = False):
    """
    Parse Fast Operate Configuration Block.

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
    byte_array = _cast_bytearray(data)
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(byte_array[:2])
        struct['length']        = byte_array[2]
        struct['numbreakers']   = byte_array[3]
        struct['numremotebits'] = int.from_bytes( byte_array[4:6],
                                                  byteorder=byteorder,
                                                  signed=signed )
        struct['pulsesupported']= byte_array[6]
        _                       = byte_array[7]  # reservedpoint
        # Iterate Over Breaker Bits
        ind = 8
        struct['breakerconfig'] = []
        for _ in range(struct['numbreakers']):
            struct['breakerconfig'].append({
                'open'  : byte_array[ind],
                'close' : byte_array[ind+1],
            })
            ind += 2
        # Iterate Over Remote Bits
        struct['remotebitconfig'] = []
        for _ in range(struct['numremotebits']):
            remotebitstruct = {
                'clear' : byte_array[ind],
                'set'   : byte_array[ind+1],
            }
            ind += 2
            if struct['pulsesupported'] == 1:
                remotebitstruct['pulse'] = byte_array[ind]
                ind += 1
            # Append Structure
            struct['remotebitconfig'].append(remotebitstruct)
        if verbose:
            print("Generic Fast Operate Configuration Block Information")
            print("Command:", struct['command'])
            print("Message Length:",struct['length'])
            print("Number of Breakers:",struct['breakerconfig'])
            print("Number of Remote Bits:",struct['numremotebits'])
            print("Pulse Command Supported:", int(struct['pulsesupported'])==1)
        # Return Structure
        return struct
    except IndexError as err:
        raise ValueError("Invalid data string response") from err
################################################################################

################################################################################
# Define Function to Parse a Fast Meter Response Given the Configuration
def fast_meter_block(data: AnyStr, definition: dict, dna_def: List[List[str]],
                     byteorder: str = 'big', signed: str = True,
                     verbose: bool = False ):
    """
    Parse Fast Meter Response Block.

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
    byte_array = _cast_bytearray( data )
    struct = {}
    try:
        # Parse Data, Load Attributes
        struct['command']       = bytes(byte_array[:2])
        struct['length']        = byte_array[2]
        struct['statusflag']    = byte_array[3:3+definition['numstatusflags']]
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
                size = common.ANALOG_SIZE_LOOKUP[type]
                scale_type = analog_desc['factortype']
                # Handle Non-Scaling Values
                if scale_type == 255:
                    scale = 1
                # Extract Value to be Interpreted
                value = bytes(byte_array[ind:ind+size])
                # Apply Formatting
                value = common.ANALOG_TYPE_FORMATTERS[type]( value )
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
                # Indicate number of digitals in definition does not match DNA
                raise DnaDigitalsMisMatch(
                    'Number of digital banks does not match DNA definition.'
                )
            # Grab the Applicable Names for this Target Row (byte)
            point_names = dna_def[target_row_index][:8] # grab first 8 entries
            # Grab the list of binary statuses from the target row info
            target_data = int_to_bool_list(byte_array[ind+target_row_index],
                                            byte_like=True, reverse=True)
            target_row = dict(zip(point_names,target_data))
            # Load the Digital Dictionary with new Points
            struct['digitals'].update(target_row)
        # Remove the '*' Key from Dictionary
        struct['digitals'].pop('*')
        # Return the Resultant Structure
        return struct
    except IndexError:
        raise ValueError("Invalid data string response")
################################################################################

# END
