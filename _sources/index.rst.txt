.. selprotopy documentation master file, created by


SELPROTOPY: Python Bindings for the SEL Protocol Suite
======================================================

`selprotopy` is intended to be used as a protocol binding suite for the SEL Protocol
suite which includes SEL Fast Meter, SEL Fast Message, and SEL Fast Operate; each of
which are proprietary protocols designed by
`Schweitzer Engineering Laboratories <https://selinc.com/>`_ for use primarily with
protective electric relays, and other intelligent electronic devices.

Protocol Documentation:
-----------------------

SEL Protocol was introduced in the early 1990s to support various communications and
control of SEL protective relays. SEL provided a very supportive
`application guide <https://selinc.com/api/download/5026/?lang=en>`_ which provides great
detail about the protocol's implementation.

.. toctree::
   :maxdepth: 1
   
   selprotopy


Dependencies
------------

This package requires connection to an SEL relay, and to support this connection, one of
two connections is standard. SEL relays are typically connected to by way of a serial
connection or an Telnet channel over Ethernet. As a result of this requirement, it is
necessary to use either the standard Python `telnetlib <https://docs.python.org/3/library/telnetlib.html>`_,
however, there is also the option of using `pySerial <https://pyserial.readthedocs.io/en/latest/pyserial.html>`_
for direct serial connections. One, or perhaps both, of these libraries will be required
for use of this package.


Project Information
-------------------

For additional information related to this project, please refer to the links and materials
linked below.

Contact Info:
~~~~~~~~~~~~~

For issues found in the source code itself, please feel free to open an
`issue <https://github.com/engineerjoe440/sel-proto-py/issues>`_, but for general inquiries
and other contact, feel free to address `Joe Stanley <mailto:joe_stanley@selinc.com>`_.


Source Repository and Package Release (PyPI):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- GitHub: https://github.com/engineerjoe440/sel-proto-py
- PyPI: https://pypi.org/project/selprotopy/

