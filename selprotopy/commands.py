"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""
# Standard Package Imports
import re

# Local Imports
from selprotopy.common import eval_checksum

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
FAST_MSG_CONFIG_BLOCK   = bytes.fromhex('A546') # A configuration block for Fast Message command.

# Define Various ASCII Requests
CR  = b"\r\n" # Carriage Return to be Used Throughout
ID  = b"ID" + CR
ENA = b"ENA" + CR
DNA = b"DNA" + CR
BNA = b"BNA" + CR
QUIT   = b"QUI" + CR
GO_ACC = b"ACC" + CR
GO_2AC = b"2AC" + CR

# Define Default SEL Relay Passwords
PASS_ACC = b"OTTER"
PASS_2AC = b"TAIL"

# Define Access Level Indicators
LEVEL_0 = b"="
LEVEL_1 = b"=>"
LEVEL_2 = b"=>>"
LEVEL_C = b"==>>"
PROMPT = CR + LEVEL_0
PASS_PROMPT = b"Password:"


###################################################################################
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
###################################################################################
# Define Function to Prepare Fast Operate Command
def prepare_fastop_command(control_type, control_point, command,
                            fastop_def):
    """
    Prepare a fast operate command for a relay.

    Prepare the binary message required to set/clear/pulse/open/close
    the respective control point using fast operate.
    """
    # Prepare the Point Number
    if isinstance(control_point, str):
        control_point = int(re.findall(r'(\d+)',control_point)[0])
    # Verify the Command Type
    if command.lower() not in ['set', 'clear', 'pulse', 'open', 'close']:
        # Indicate invalid command type
        raise ValueError("Invalid command type")
    # Set up Breaker or Remote Control
    if control_type.lower() == 'remote_bit':
        command_string = FAST_OP_REMOTE_BIT
    elif control_type.lower() == 'breaker_bit':
        command_string = FAST_OP_BREAKER_BIT
    else:
        # Indicate invalid control type
        raise InvalidControlType("Invalid control type described.")
    command_string += bytes([6]) # Length (in bytes)
    try:
        control = fastop_def['remotebitconfig'][control_point-1][command]
        print("control", control)
    except KeyError as e:
        raise ValueError("Improper command type for control point.") from e
    op_validation = (control * 4 + 1) & 0xff
    # Clean Control and Validation (format as hex)
    command_string += bytes([control, op_validation])
    command_string += bytes([eval_checksum(command_string, constrain=True)])
    # Return the Configured Command
    return command_string



# END