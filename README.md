# ROT2Prog

This is a control interface for the [Alfa ROT2Prog Controller](http://alfaradio.ca/docs/Manuals/RAS/Alfa_ROT2Prog_Controller-28March2019-Master.pdf).

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

### Contents

- [Setup](#setup)
	+ [Hardware](#hardware-setup)
	+ [Software](#software-setup)
- [Usage](#usage)
	+ [Dependencies](#dependencies)
	+ [Simulation](#simulation)
	+ [Implementation](#implementation)
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

# Setup

### Hardware Setup

1. Press setup key `S` until `PS` is displayed on the far left screen of the controller.
2. Use the `<` `>` keys to set the value (to the right of `PS`) to `SP`.
3. Press the function key `F` until `A` is displayed on the far left screen of the controller.
4. Congratulations! Your ROT2Prog will now respond to SPID commands.

### Software Setup

1. Create a virtual environment and install dependencies.

	Windows:
	
	```sh
	python -m venv .venv
	".venv/Scripts/activate"
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	```
	
	Unix and MacOS:

	```sh
	python -m venv .venv
	source .venv/bin/activate
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	```

2. Run scripts (see [Usage](#usage)).
3. Deactivate the virtual environment.

	```sh
	deactivate
	```

	> This step is only necessary when you would like to use the terminal for something else.

# Usage

The file `rot2prog.py` contains the class definition `rot2prog` with the following methods:

```python
def __init__(self, port):
	# opens serial port
	self.status()

def status(self):
	# send status command
	return [az, el]
	# 	az: azimuth angle
	# 	el: elevation angle

def stop(self):
	# send stop command
	return [az, el]
	# 	az: current azimuth angle
	# 	el: current elevation angle

def set(self, az, el):
	# send set command
	# 	az: new azimuth angle
	# 	el: new elevation angle
```

These methods are used to send commands and receive responses. As shown below, the class constructor requires the serial port to be specified to connect to the simulator or physical controller.

```python
def __init__(self, port):
```

### Simulation

The file `rot2prog_sim.py` is a script designed to simulate the ROT2Prog hardware interface. In order to use this script for testing, it must be connected to a serial port as well. There are two approaches to connecting the respective serial ports for `rot2prog.py` and `rot2prog_sim.py`:

1. Software Implementation: Use a free tool such as [Free Virtual Serial Ports](https://freevirtualserialports.com/) to connect two virtual ports
2. Hardware Implementation: Use a male-male USB cable connected to two physical ports of the host

> NOTE: Start the simulator `rot2prog_sim.py` first

### Implementation

The file `rot2prog.py` can be run independently for testing, but it is most practical to use it as part of a larger design. This is as simple as calling the constructor and passing in the name of the serial port where the hardware is connected. An example of this instantiation and usage is shown below:

```python
rot = rot2prog('COM1')
rot.test()
status = rot.status()
```

# Protocol

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

***

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.