# ROT2Prog

This is a control interface for the [Alfa ROT2Prog Controller](http://alfaradio.ca/docs/Manuals/RAS/Alfa_ROT2Prog_Controller-28March2019-Master.pdf). Credit to [jaidenfe](https://github.com/jaidenfe/rot2proG) for the original script.

The SPID protocol supports 3 commands: stop, status and set. The stop command stops the rotor in its current position and returns the aproximate position it has stopped in. The status command returns the current position of the rotor. The set command tells the rotor to rotate to a given position.

The rotor controller communicates with the PC using a serial connection. Communication parameters are 600 bps, 8 bits, no parity and 1 stop bit. In order for the computer to communicate with the rotor, the controller must be set to the "Auto" setting. This can be done by pressing the function key ("F") until you see an "A" displayed in the left-most screen on the controller.

All commands are issued as 13 byte packets, and responses are received as 12 byte packets.

### Command Packet

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value** | 0x57  | 0x3? | 0x3? | 0x3? | 0x3? | 0x0? | 0x3? | 0x3? | 0x3? | 0x3? | 0x0? | 0x?F | 0x20 |

- <b>START</b> - Start byte (always 0x57)
- <b>H1 - H4</b> - Azimuth as ASCII characters 0-9
- <b>PH</b> - Azimuth resolution in pulses per degree (ignored in command packet)
- <b>V1 - V4</b> - Elevation as ASCII characters 0-9
- <b>PV</b> - Elevation resolution in pulses per degree (ignored in command packet)
- <b>K</b> - Command (0x0F = STOP | 0x1F = STATUS | 0x2F = SET)
- <b>END</b> - End byte (always 0x20)

### Response Packet

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | END  |
| **Value** | 0x57  | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x0? | 0x20 |


- <b>START</b> - Start byte (always 0x57)
- <b>H1 - H4</b> - Azimuth as byte values
- <b>PH</b> - Azimuth resolution in pulses per degree
- <b>V1 - V4</b> - Elevation as byte values
- <b>PV</b> - Elevation resolution in pulses per degree
- <b>END</b> - End byte (always 0x20)

Positions are decoded using the following formulas:

*az = H1 * 100 + H2 * 10 + H3 + H4 / 10 - 360* <br>
*el = V1 * 100 + V2 * 10 + V3 + V4 / 10 - 360*

### Degree Per Pulse

| Deg/pulse | PH   | PV   |
|:----------|:-----|:-----|
| 1         | 0x01 | 0x01 |
| 0.5       | 0x02 | 0x02 |
| 0.20      | 0x04 | 0x04 |

> NOTE: The PH and PV values in the response packet reflect the settings of the rotator controller. The Rot2Prog supports the following resolutions (always the same for azimuth and elevation):

### Stop Command

*Command Packet*

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value** | 0x57  | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x0F | 0x20 |

*Response Packet Example*

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | END  |
| **Value** | 0x57  | 0x03 | 0x07 | 0x02 | 0x05 | 0x02 | 0x03 | 0x09 | 0x04 | 0x00 | 0x02 | 0x20 |

*az = 372.5 - 360 = 12.5* <br>
*el = 394.0 - 360 = 34.0* <br>
*PH = PV = 0x02 (pulse for each 0.5 deg)*

### Status Command

The status command returns the current position of the antenna

*Command Packet*

| Byte   | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:--------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value**  | 0x57  | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x00 | 0x1F | 0x20 |

*Response Packet Example*

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | END  |
| **Value** | 0x57  | 0x03 | 0x07 | 0x02 | 0x05 | 0x02 | 0x03 | 0x09 | 0x04 | 0x00 | 0x02 | 0x20 |


*az = 372.5 - 360 = 12.5* <br>
*el = 394.0 - 360 = 34.0* <br>
*PH = PV = 0x02 (pulse for each 0.5 deg)*

> NOTE: Status commands can be issued while the rotator is moving and will always return the current position

### Set Command

The set command tells the rotator to turn to a specific position. The controller does not send a response to this command.

Azimuth and elevation is calculated as number of pulses, with a +360 degree offset (so that negative position can be encoded with positive numbers).

Rot2Prog supports different resolutions:

*H = PH * (360 + az)* <br>
*V = PV * (360 + el)*

H1-H4 and V1-V4 are these numbers encoded as ASCII (0x30-0x39, i.e., '0'-'9').

##### Example
Pointing a Rot2Prog to azimuth 123.5, elevation 77.0 and a 0.5 degree per pulse value (PH=PV=2):

*H = 2 * (360 + 123.5) = 967* <br>
*V = 2 * (360 + 77.0) = 874*

| Byte      | 0     | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 11   | 12   |
|:----------|:------|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|:-----|
| **Field** | START | H1   | H2   | H3   | H4   | PH   | V1   | V2   | V3   | V4   | PV   | K    | END  |
| **Value** | 0x57  | 0x30 | 0x39 | 0x36 | 0x37 | 0x02 | 0x30 | 0x38 | 0x37 | 0x34 | 0x02 | 0x2F | 0x20 |


> NOTE: The PH and PV values sent are ignored. The values used by the rotator control unit are set by choosing resolution in the setup menu. These values can be read using the status command if they are not known.

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