"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""

# Define Relay Definition Block Parser
def RelayDefinitionBlock( data, verbose=False):
    """
    
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





# END