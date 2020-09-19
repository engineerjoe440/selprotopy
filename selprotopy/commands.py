"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""

# Define Various Binary Requests
RELAY_DEFENITION        = bytes.fromhex('A5C0') # The relay definition block.
FM_CONFIG_BLOCK         = bytes.fromhex('A5C1') # A configuration block for regular Fast Meter command if available.
FM_DEMAND_CONFIG_BLOCK  = bytes.fromhex('A5C2') # A configuration block for demand Fast Meter if available.
FM_PEAK_CONFIG_BLOCK    = bytes.fromhex('A5C3') # A configuration block for peak demand Fast Meter if available.
FO_CONFIG_BLOCK         = bytes.fromhex('A5CE') # A configuration block for Fast Operate if available.
FO_CONFIG_BLOCK_ALT     = bytes.fromhex('A5CF') # Alternate configuration block for Fast Operate if available.
FM_OLD_STD_BLOCK        = bytes.fromhex('A5DC') # One of the old standard Fast Meter blocks if available.
FM_OLD_EXT_BLOCK        = bytes.fromhex('A5DA') # One of the old extended Fast Meter blocks if available.
FAST_METER_REGULAR      = bytes.fromhex('A5D1') # Regular Fast Meter defined by configuration block.
FAST_METER_DEMAND       = bytes.fromhex('A5D2') # Demand Fast Meter defined by configuration block. 
FAST_METER_PEAK_DEMAND  = bytes.fromhex('A5D3') # Peak demand Fast Meter defined by configuration block.
FAST_OP_REMOTE_BIT      = bytes.fromhex('A5E0') # Fast Operate command for remote bit operation.
FAST_OP_BREAKER_BIT     = bytes.fromhex('A5E3') # Fast Operate command for breaker operation.
FAST_OP_OPEN_COMMAND    = bytes.fromhex('A5E5') # Fast Operate OPEN Command.
FAST_OP_CLOSE_COMMAND   = bytes.fromhex('A5E6') # Fast Operate CLOSE Command. 
FAST_OP_SET_COMMAND     = bytes.fromhex('A5E7') # Fast Operate SET Command.
FAST_OP_CLEAR_COMMAND   = bytes.fromhex('A5E8') # Fast Operate CLEAR Command.
FAST_OP_PULSE_COMMAND   = bytes.fromhex('A5E9') # Fast Operate PULSE Command.
OLDEST_UNAK_EVNT_REP    = bytes.fromhex('A5B2') # Oldest unacknowledged event report packet.
ACK_RECNT_SENT_EVNT_REP = bytes.fromhex('A5B5') # Acknowledge event report most recently sent.
CLEAR_STA_POWER_SETTING = bytes.fromhex('A5B9') # Clear status bits: power-up, setting change.
MOST_RECENT_EVNT_REP    = bytes.fromhex('A560') # Most recent event report packet.

# Define Various ASCII Requests
CR  = b"\r\n" # Carriage Return to be Used Throughout
ID  = b"ID" + CR
ENA = b"ENA" + CR
DNA = b"DNA" + CR
BNA = b"BNA" + CR


# Define Simple Function to Evaluate Request String for Numbered Event Record
def event_record_request(event_number):
    """
    `event_record_request`
    
    A simple function to evaluate the request byte-string
    to request a numbered event (zero-based) from the relay's
    event history.
    
    Parameters
    ----------
    event_number:   int
                    The zero-based event number index. Zero (0)
                    is the most recent event.
    
    Returns
    -------
    request:        bytes
                    The byte-string request which to provide the
                    indexed event desired.
    
    Raises
    ------
    ValueError:     Raised when the requested event number is
                    greater than 64.
    """
    if event_number <= 64:
        # Prepare leading portion of request
        request = bytes.fromhex('A5')
        # Append the event number plus the minimum event command
        request += hex(96 + event_number)
        return request
    else:
        raise ValueError("Event number may not be greater than 64.")





# END