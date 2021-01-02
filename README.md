# SELProtoPy <img src="https://raw.githubusercontent.com/engineerjoe440/selprotopy/master/logo/selprotopy.png" width="250" alt="logo" align="right">
Schweitzer Engineering Laboratories (SEL) Protocol Bindings in Python

[![](https://img.shields.io/pypi/v/selprotopy.svg?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/selprotopy/)
[![](https://pepy.tech/badge/selprotopy)](https://pepy.tech/project/selprotopy)
[![](https://img.shields.io/github/stars/engineerjoe440/selprotopy?logo=github)](https://github.com/engineerjoe440/selprotopy/)
[![](https://img.shields.io/pypi/l/selprotopy.svg?color=blue)](https://github.com/engineerjoe440/selprotopy/blob/master/LICENSE.txt)

***This project is still in early stages, much is still to come.***

## Description:
`selprotopy` is intended to be used as a protocol binding suite for the SEL Protocol
suite which includes SEL Fast Meter, SEL Fast Message, and SEL Fast Operate; each of
which are proprietary protocols designed by
[Schweitzer Engineering Laboratories](https://selinc.com/) for use primarily with
protective electric relays, and other intelligent electronic devices.

## Protocol Documentation:
SEL Protocol was introduced in the early 1990s to support various communications and
control of SEL protective relays. SEL provided a very supportive
[application guide](https://selinc.com/api/download/5026/?lang=en) which provides great
detail about the protocol's implementation.

## Installation:

**From PyPI as a Python Package**

Just go ahead and issue: `pip install selprotopy`

**From Source on Github**

To install `selprotopy` from GitHub:

1. Download the repository as a zipped package.
2. Unzip the repository.
3. Open a terminal (command-prompt) and navigate to the new folder that's been unzipped.
(*Hint:* Use `cd <the-path-to-the-folder-you-unzipped-in>/selprotopy`)
4. Use `pip` or `python` to install with the following commands, respectively:
    - `$> pip install .`
    - `$> python setup.py install`
5. Verify that it's been installed by opening a Python instance and importing:
    `>>> import selprotopy` If no errors arise, the package has been installed.

## Contributing:

Want to get involved? We'd love to have your help!

Please help us by identifying any issues that you come across. If you find an error,
bug, or just have questions, jump over to the
[issue](https://github.com/engineerjoe440/selprotopy/issues) page.

If you want to add features, or contribute yourself, feel free to open a pull-request.

### Contact Info:
For issues found in the source code itself, please feel free to open an
[issue](https://github.com/engineerjoe440/selprotopy/issues), but for general inquiries
and other contact, feel free to address Joe Stanley.

- [joe_stanley@selinc.com](mailto:joe_stanley@selinc.com)