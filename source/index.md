# SELPROTOPY: Python Bindings for the SEL Protocol Suite

`selprotopy` is intended to be used as a protocol binding suite for the SEL
Protocol suite which includes SEL Fast Meter, SEL Fast Message, and SEL Fast
Operate; each of which are proprietary protocols designed by
[Schweitzer Engineering Laboratories](https://selinc.com/) for use primarily
with protective electric relays, and other intelligent electronic devices.

```{note}
    This project, although binding SEL Protocol, is not sponsored, tested, or
    vetted in any way by Schweitzer Engineering Laboratories (SEL). This project
    is authored and maintained as an open-source project. Testing is performed
    on a very small set of hardware running in the author's basement. In short,
    this project has no association with SEL.
```

## Protocol Documentation

SEL Protocol was introduced in the early 1990s to support various communications
and control of SEL protective relays. SEL provided a very supportive
[application guide](https://selinc.com/api/download/5026/) which provides great
detail about the protocol's implementation.

```{toctree}
---
    maxdepth: 1
---
   
    selprotopy
```

```{warning}
    *Since this project is not rigorously tested across all SEL devices or in a
    wide variety of use-cases, any time this project is used, it should first be
    thoroughly tested. This project is not intended to serve protection-class
    systems in any capacity. It should primarily be used for research,
    exploration, and other learning objectives.*
```

### Installation

#### Typical Installation (From PyPI)

```shell
pip install selprotopy[full]
```

#### From Source (Development)

To install `selprotopy` from GitHub:

1. Download the repository as a zipped package.
2. Unzip the repository.
3. Open a terminal (command-prompt) and navigate to the new folder that's been unzipped.

    ```{hint}
    Use `cd <the-path-to-the-folder-you-unzipped-in>/selprotopy`
    ```

4. Use `pip` or `python` to install with the following commands, respectively:

    ```shell
    pip install -e .
    ```

5. Verify that it's been installed by opening a Python instance and importing:

    ```python
    >>> import selprotopy
    ```

    If no errors arise, the package has been installed.

## Project Information

For additional information related to this project, please refer to the links
and materials linked below.

### Contact Info

As mentioned in the
[caution](https://engineerjoe440.github.io/selprotopy/#selprotopy-python-bindings-for-the-sel-protocol-suite)
above, this project is not associated with Schweitzer Engineering Laboratories
(SEL) in any way, and as such, all contacts for questions, support, or other
items should be directed to the resources listed here.

For issues found in the source code itself, please feel free to open an
[issue](https://github.com/engineerjoe440/selprotopy/issues), but for general
inquiries and other contact, feel free to address
[Joe Stanley](mailto:engineerjoe440@yahoo.com).
