# check_jbod.py
This tool is used to monitor Xyratex JBOD, also known as:

- Seagate/Xyratex SP-2584
- Seagate/Xyratex SP-3584
- Seagate Exos E 4U106
- Dell MD1420

These JBODs are probably also supported with some slight modifications:
- Dell MD1280
- Lenovo D3284

## Requirements
* `sg_ses`

## Usage
This script is intended to be used with NRPE. The device ID is the number on the LCD screen or set via the CLI on the Exos 4U106.

```
usage: check_jbod.py [-h] [-v] [--fan] [--volt] [--current] [--psu_status]
                     [--temp]
                     device

Monitor Fans, PSU and temperature in a Xyratex JBOD

positional arguments:
  device         JBOD ID to check

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  increase output verbosity
  --fan          Check fan
  --volt         Check voltage
  --current      Check current
  --psu_status   PSU status
  --temp         Check temperatures based on internal thresholds
```
