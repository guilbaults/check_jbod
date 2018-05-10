# check_jbod.py
This tool is used to monitor a 84 slots Xyratex JBOD, also known as:

- Seagate/Xyratex SP-2584
- Dell MD1280
- Lenovo D3284

## Requirements
* `sg_ses`

## Usage
This script can be runned with NRPE.

```
usage: check_jbod.py [-h] [-v] [--fan_min FAN_MIN] [--fan_max FAN_MAX]
                     [--volt_min VOLT_MIN] [--volt_max VOLT_MAX]
                     [--current_min CURRENT_MIN] [--current_max CURRENT_MAX]
                     [--psu_status] [--check_temp]
                     device

Monitor Fans, PSU and temperature in a Xyratex 84 slots JBOD

positional arguments:
  device                sg device (/dev/sg0 by default)

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbosity       increase output verbosity
  --fan_min FAN_MIN     Minimum fans RPMs
  --fan_max FAN_MAX     Maximum fans RPMs
  --volt_min VOLT_MIN   Minimum voltage
  --volt_max VOLT_MAX   Maximum voltage
  --current_min CURRENT_MIN
                        Minimum current
  --current_max CURRENT_MAX
                        Maximum current
  --psu_status          PSU status
  --check_temp          Check temperatures based on internal thresholds
```
