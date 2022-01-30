# ROT2Prog

This is a python interface to the [Alfa ROT2Prog Controller](http://alfaradio.ca/docs/Manuals/RAS/Alfa_ROT2Prog_Controller-28March2019-Master.pdf). The ROT2Prog is an electronic controller used for turning rotators. The Controller may be connected to one Azimuth and Elevation rotator and operates with direct current motors. The ROT2Prog is designed to work with either an Alfa RAS or BIGRAS or a combination of one azimuth rotator RAU, RAK and a REAL rotator.

This package is responsible for implementing the serial [protocol](#protocol) to interact with the ROT2Prog controller. There is also a [simulation model](#simulation) of the ROT2Prog controller included in the package, which can be used for testing when hardware is not available.

### Contents

- [Getting Started](#getting-started)
	+ [Installation](#installation)
	+ [Usage](#usage)
	+ [Simulation](#simulation)
- [Protocol](#protocol)
	+ [Command Packet](#command-packet)
	+ [Response Packet](#response-packet)
	+ [Degrees Per Pulse](#degrees-per-pulse)
	+ [Stop Command](#stop-command)
		* [Example](#stop-command-example)
	+ [Status Command](#status-command)
		* [Example](#status-command-example)
	+ [Set Command](#set-command)
		* [Example](#set-command-example)

# Getting Started

If you intend to use this package with hardware:

1. Press setup key `S` until `PS` is displayed on the far left screen of the controller.
2. Use the `<` `>` keys to set the value (to the right of `PS`) to `SP`.
3. Press the function key `F` until `A` is displayed on the far left screen of the controller.
4. Congratulations! Your ROT2Prog will now respond to SPID commands.

> NOTE: The hardware is not required for testing, see [Simulation](#simulation).

### Installation

The `rot2prog` package is published on PyPi and can be installed in the terminal.

```
pip install rot2prog
```

This package was developed using Python `3.10.2`, and has not yet been tested with earlier releases of Python. If using an earlier version of Python, it is recommended to proceed with caution, running the [simulation](#simulation) and [standalone script](#usage) together to exercise all commands.

### Usage

1. Importing

	```python
	import rot2prog

	rot = rot2prog.ROT2Prog('COM1')
	```

	> NOTE: For more information, reference the [rot2prog API](https://github.com/tj-scherer/rot2prog/docs/rot2prog) in `/docs/rot2prog`.

2. Standalone

	```
	python -m rot2prog.utils.run
	```

	> NOTE: The standalone mode offers direct access to the `stop`, `status`, and `set` commands, allowing the hardware to be controlled directly from the terminal.

### Simulation

Begin by establishing a connection between the two desired ports:

1. Use a tool such as [Free Virtual Serial Ports](https://freevirtualserialports.com/) to connect two virtual ports of the same host.
2. Use a male-male USB cable connected to two physical ports of the same host.
3. Use a male-male USB cable connected to two physical ports on different hosts. In this case, each host must run its own software to communicate.

```
python -m rot2prog.utils.sim
```

> NOTE: The simulator's serial connection should be established first.

> NOTE: The simulator does not perfectly match real-world behavior in regard to executing commands. The real system cannot move to a new position instantaneously, whereas the simulator currently does.

# Protocol

- The SPID protocol supports 3 commands:
	+ **STOP**: Stops the rotator in its current position.
	+ **STATUS**: Returns the current position of the rotator.
	+ **SET**: Tells the rotator to rotate to a given position.
- The rotator controller communicates with the host using a serial port. The serial communication parameters are:
	+ `600 bps`
	+ `8 bits`
	+ `no parity`
	+ `1 stop bit`
- All commands are issued as 13 byte packets.
- All responses are received as 12 byte packets.

### Command Packet

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value** | 0x57  | 0x3? | 0x3? | 0x3? | 0x3? | 0x0? | 0x3? | 0x3? | 0x3? | 0x3? | 0x0? | 0x?F | 0x20 |

- **START** - Start byte (always 0x57)
- **H1 - H4** - Azimuth as ASCII characters 0-9
- **PH** - Azimuth resolution in pulses per degree (ignored in command packet)
- **V1 - V4** - Elevation as ASCII characters 0-9
- **PV** - Elevation resolution in pulses per degree (ignored in command packet)
- **K** - Command
	+ 0x0F = STOP
	+ 0x1F = STATUS
	+ 0x2F = SET
- **END** - End byte (always 0x20)

### Response Packet

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | END  |
| **Value** | 0x57  | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x20 |


- **START** - Start byte (always 0x57)
- **H1 - H4** - Azimuth as byte values
- **PH** - Azimuth resolution in pulses per degree
- **V1 - V4** - Elevation as byte values
- **PV** - Elevation resolution in pulses per degree
- **END** - End byte (always 0x20)

Positions from the response packet are decoded using the following formulas:

```python
az = (H1 * 100) + (H2 * 10) + H3 + (H4 / 10) - 360
el = (V1 * 100) + (V2 * 10) + V3 + (V4 / 10) - 360
```

### Degrees Per Pulse

The PH and PV values in the response packet reflect the settings of the rotator controller. The ROT2Prog supports the following resolutions (the value is always the same for azimuth and elevation):

| Degrees per pulse | PH   | PV   |
|:------------------|:-----|:-----|
| 1                 | 0x01 | 0x01 |
| 0.5               | 0x02 | 0x02 |
| 0.25              | 0x04 | 0x04 |

### Stop Command

The stop command stops the rotator immediately in the current position and returns the current position.

*Command Packet*

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value** | 0x57  | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x0F | 0x20 |

> NOTE: The H1-H4, PH, V1-V4 and PV fields are ignored, so only the S, K and END fields are used.

##### Stop Command Example

*Example Response Packet*

| Byte      | 0     | 1        | 2        | 3        | 4        | 5    | 6        | 7        | 8        | 9        | 10   | 11   |
|:----------|:------|:---------|:---------|:---------|:---------|:-----|:---------|:---------|:---------|:---------|:-----|:-----|
| **Field** | START | H1       | H2       | H3       | H4       | PH   | V1       | V2       | V3       | V4       | PV   | END  |
| **Value** | 0x57  | 0x0**3** | 0x0**7** | 0x0**2** | 0x0**5** | 0x02 | 0x0**3** | 0x0**9** | 0x0**4** | 0x0**0** | 0x02 | 0x20 |

*Decoding Example Response Packet*

```python
az = (3 * 100) + (7 * 10) + 2 + (5 / 10) - 360 = 12.5
el = (3 * 100) + (9 * 10) + 4 + (0 / 10) - 360 = 34.0
PH = PV = 0x02
```

### Status Command

The status command returns the current position of the antenna.

> NOTE: Status commands can be issued while the rotator is moving and will always return the current position.

*Command Packet*

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value** | 0x57  | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x1F | 0x20 |

> NOTE: The H1-H4, PH, V1-V4 and PV fields are ignored, so only the S, K and END fields are used.

##### Status Command Example

*Example Response Packet*

| Byte      | 0     | 1        | 2        | 3        | 4        | 5    | 6        | 7        | 8        | 9        | 10   | 11   |
|:----------|:------|:---------|:---------|:---------|:---------|:-----|:---------|:---------|:---------|:---------|:-----|:-----|
| **Field** | START | H1       | H2       | H3       | H4       | PH   | V1       | V2       | V3       | V4       | PV   | END  |
| **Value** | 0x57  | 0x0**3** | 0x0**7** | 0x0**2** | 0x0**5** | 0x02 | 0x0**3** | 0x0**9** | 0x0**4** | 0x0**0** | 0x02 | 0x20 |

*Decoding Example Response Packet*

```python
az = (3 * 100) + (7 * 10) + 2 + (5 / 10) - 360 = 12.5
el = (3 * 100) + (9 * 10) + 4 + (0 / 10) - 360 = 34.0
PH = PV = 0x02
```

### Set Command

The set command tells the rotator to turn to a specific position. The controller does not send a response to this command.

*Encoding Command Packet*

```python
H = PH * (az + 360)
V = PV * (el + 360)
```

> NOTE: H1-H4 and V1-V4 are H and V converted to ASCII (0x30-0x39, i.e., '0'-'9').

##### Set Command Example

*Encoding Example Command Packet*

```
az = 123.5
el = 77.0
PH = PV = 0x2
```

```python
H = 2 * (123.5 + 360) = 967
V = 2 * (77.0 + 360) = 874
```

*Example Command Packet*

```
H = 0967
V = 0874
PH = PV = 0x2
```

| Byte      | 0     | 1        | 2        | 3        | 4        | 5    | 6        | 7        | 8        | 9        | 10   | 11   | 12   |
|:----------|:------|:---------|:---------|:---------|:---------|:-----|:---------|:---------|:---------|:---------|:-----|:-----|:-----|
| **Field** | START | H1       | H2       | H3       | H4       | PH   | V1       | V2       | V3       | V4       | PV   | K    | END  |
| **Value** | 0x57  | 0x3**0** | 0x3**9** | 0x3**6** | 0x3**7** | 0x02 | 0x3**0** | 0x3**8** | 0x3**7** | 0x3**4** | 0x02 | 0x2F | 0x20 |

> NOTE: The PH and PV values are ignored. The values used by the rotator control unit are set by choosing resolution in the setup menu directly on the controller. These values can be read using the status command if they are unknown.