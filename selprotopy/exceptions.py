"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""


# Define Various Custom Exception Types
class CommError(Exception):
    """Base Class for Communications Errors."""
    
    pass


class ParseError(CommError):
    """Base Class for Parsing Errors."""
    
    pass


class ProtoError(Exception):
    """Base Class for Protocol Errors."""

    pass


###############################################################################

# Define Custom Exception for Array Extraction Error
class MalformedByteArray(CommError):
    """
    Malformed Byte Array.

    Byte array does not appear in expected format, likely due to truncated
    communications caused by a communications failure.
    """

    pass


# Define Custom Exception for Invalid Checksum
class ChecksumFail(CommError):
    """
    Checksum Comparison Failure.
    
    Checksum validation has failed for the captured message, likely due to
    communications failure.
    """

    pass


# Define Custom Exception to Indicate Connection Verification Failure
class ConnVerificationFail(CommError):
    """Communications could not be verified."""

    pass

###############################################################################


# Define Custom Exception for SEL Protocol Message Response Extraction
class MissingA5Head(ParseError):
    """
    Response Message Missing A5 Byte Heading.
    
    Parsing of returned binary SEL Protocol message failed due to lack of
    required A5[C1] heading.
    """

    pass


# Define Custom Exception for SEL Protocol DNA/Digitals Count Mismatch
class DnaDigitalsMisMatch(ParseError):
    """
    DNA Digital Sequence Doesn't Match Definition.
    
    Dereferencing of digitals in response does not match the relay's DNA
    definition, may be caused by a communications error, or failed parse.
    """
    
    pass

###############################################################################


# Define Custom Exception for Invalid Command Type
class InvalidCommandType(ProtoError):
    """
    Invalid CommandType.
    
    Invalid command type provided for Fast Operate, must be member of:
    ['SET', 'CLEAR', 'PULSE', 'OPEN', 'CLOSE'].
    """
    
    pass


# Define Custom Exception for Invalid Control Type
class InvalidControlType(ProtoError):
    """
    Invalid Control Type.
    
    Invalid control type provided for Fast Operate, must be member of:
    ['REMOTE_BIT', 'BREAKER_BIT'].
    """
    
    pass


# END
