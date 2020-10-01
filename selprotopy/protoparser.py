"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""

# Import Requirements
import re


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


###################################################################################
# Define Relay ID Block Parser
def RelayIdBlock( data, encoding='', verbose=False ):
    """
    
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
            if verbose:
                print(f'Unable to determine {id_key} parameter from relay ID.')
    # Return Parsed ID Components
    return results

# Define Relay DNA Block Parser
def RelayDnaBlock( data, encoding='', verbose=False ):
    """
    
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
    for line in bnastring.split('\n')
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
def RelayDefinitionBlock( data, verbose=False):
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
    
    Returns
    -------
    dict
                Dictionary of key-value pairs describing
                the relay's definition block.
    """
    # Capture Byte Array for Parsing
    bytArr = bytearray(data)
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
        if verbose: print(struct['fmcommandinfo'],'\n',struct['fmtype'])
        ind += 1
        # Iterate Over the Status Flag Commands
        for _ in range(struct['statusflagssup']):
            dict = {}
            dict['statusbit'] = bytes(bytArr[ind:ind+2])
            dict['affectedcommand'] = bytes(bytArr[ind+2:ind+8])
            struct['statusflaginfo'].append(dict)
            ind += 8
        if verbose: print(struct['statusflaginfo'])
        # Return Resultant Structure
        return struct
    except:
        raise ValueError("Invalid data string response")
###################################################################################




# END