#!/usr/bin/env python
import re
import sys
import commands
import argparse


def sg_ses_info(device, page):
    raw_info = {}
    status, output = commands.getstatusoutput(
        'sg_ses --page={page} {device}'.format(
            page=page,
            device=device,
        ))
    if status != 0:
        # Unknown
        sys.exit(3)

    current_section = ''
    lines = output.split('\n')
    for line in lines:
        section_name = re.match(r'^\s\s\s\sElement type: (.*),.*$', line)
        if section_name:
            current_section = section_name.group(1)
        if current_section not in raw_info:
            raw_info[current_section] = []
        raw_info[current_section].append(line.strip())
    return raw_info


def split_list(input_list, split_count):
    # This function will return a splitted list into sublists
    l_range = xrange(0, len(input_list), split_count)
    return [input_list[i:i+split_count] for i in l_range]

parser = argparse.ArgumentParser(description='Monitor Fans, PSU and \
temperature in a  Xyratex 84 slots JBOD')
parser.add_argument("-v", "--verbosity", action="count",
                    help="increase output verbosity")
parser.add_argument("device", help="sg device (/dev/sg0 by default)",
                    action="store", default="/dev/sg0")
parser.add_argument("--fan_min", help="Minimum fans RPMs", type=int,
                    action="store")
parser.add_argument("--fan_max", help="Maximum fans RPMs", type=int,
                    action="store")
parser.add_argument("--volt_min", help="Minimum voltage", type=float,
                    action="store")
parser.add_argument("--volt_max", help="Maximum voltage", type=float,
                    action="store")
parser.add_argument("--current_min", help="Minimum current", type=float,
                    action="store")
parser.add_argument("--current_max", help="Maximum current", type=float,
                    action="store")
parser.add_argument("--psu_status", help="PSU status", action="store_true")
parser.add_argument("--check_temp", help="Check temperatures based on internal thresholds",
                    action="store_true")

args = parser.parse_args()

perfdata = []
criticals = []
warnings = []
raw_info = sg_ses_info(args.device, '0x02')

if args.verbosity:
    print raw_info.keys()

if args.fan_min or args.fan_max:
    fans = raw_info['Cooling'][5:]
    for fan in [fans[i:i+4] for i in xrange(0, len(fans), 4)]:
        fan_number = int(fan[0].split()[1])
        status = re.match(r'.*status: (.*)', fan[1]).group(1)
        speed = int(re.match(r'^Actual speed=(\d+) rpm', fan[3]).group(1))
        if args.fan_min and speed < args.fan_min:
            criticals.append('Fan{fan} is too slow ({rpm} RPM)'.format(
                fan=fan_number,
                rpm=speed,
            ))
        if args.fan_max and speed > args.fan_max:
            criticals.append('Fan{fan} is too fast ({rpm} RPM)'.format(
                fan=fan_number,
                rpm=speed,
            ))
        if status != 'OK':
            criticals.append('Fan{fan} is not OK'.format(
                fan=fan_number,
            ))
        perfdata.append('Fan{fan}_RPM={speed};;{MIN_FAN}:{MAX_FAN};;'.format(
            fan=fan_number,
            speed=speed,
            MIN_FAN=args.fan_min,
            MAX_FAN=args.fan_max,
        ))

if args.check_temp:
    threshold_info = sg_ses_info(args.device, '0x05')
    temperatures_info = raw_info['Temperature sensor'][6:]
    temp_threshold = threshold_info['Temperature sensor'][4:]
    temperature_thresholds = []

    for threshold in split_list(temp_threshold, 3):
        high = re.match(r"high critical=(\d+), high warning=(\d+)",
                        threshold[1])
        low = re.match(r"low warning=(\d+), low critical=(\d+)",
                       threshold[2])
        thresholds = {
            'high_critical': int(high.group(1)),
            'high_warning': int(high.group(2)),
            'low_critical': int(low.group(2)),
            'low_warning': int(low.group(1)),
        }
        temperature_thresholds.append(thresholds)

    for sensor in split_list(temperatures_info, 5):
        sensor_id = int(sensor[0].split()[1])
        status = re.match(r'.*status: (.*)', sensor[1]).group(1)
        temperature = int(re.match(r'Temperature=(\d+) C', sensor[4]).group(1))

        perfdata.append(
            'Temperature{number}={temperature};;{MIN}:{MAX};;'.format(
                number=sensor_id,
                temperature=temperature,
                MIN=temperature_thresholds[sensor_id]['low_critical'],
                MAX=temperature_thresholds[sensor_id]['high_critical'],
            ))

        if temperature > temperature_thresholds[sensor_id]['high_critical']:
            criticals.append(
                'Sensor #{number} is too hot, {temp} > {th}'.format(
                    number=sensor_number,
                    temp=temperature,
                    th=temperature_thresholds[sensor_id]['high_critical']
                ))
        elif temperature > temperature_thresholds[sensor_id]['high_warning']:
            warnings.append(
                'Sensor #{number} is too hot, {temp} > {th}'.format(
                    number=sensor_id,
                    temp=temperature,
                    th=temperature_thresholds[sensor_id]['high_warning']
                ))
        if temperature < temperature_thresholds[sensor_id]['low_critical']:
            criticals.append(
                'Sensor #{number} is too cold, {temp} < {th}'.format(
                    number=sensor_id,
                    temp=temperature,
                    th=temperature_thresholds[sensor_id]['low_critical']
                ))
        elif temperature < temperature_thresholds[sensor_id]['low_warning']:
            warnings.append(
                'Sensor #{number} is too cold, {temp} < {th}'.format(
                    number=sensor_id,
                    temp=temperature,
                    th=temperature_thresholds[sensor_id]['low_warning']
                ))

if args.psu_status is True:
    psus = raw_info['Power supply'][6:]
    for psu in [psus[i:i+5] for i in xrange(0, len(psus), 5)]:
        psu_number = int(psu[0].split()[1])
        status = re.match(r'.*status: (.*)', psu[1]).group(1)
        if psu[1] != 'Predicted failure=0, Disabled=0, Swap=0, status: OK':
            criticals.append('PSU{number} {status}'.format(
                number=psu_number,
                status=psu[1],
            ))
        if psu[3] != 'Hot swap=1, Fail=0, Requested on=0, Off=0, \
Overtmp fail=0':
            criticals.append('PSU{number} {status}'.format(
                number=psu_number,
                status=psu[1],
            ))
        if psu[4] != 'Temperature warn=0, AC fail=0, DC fail=0':
            criticals.append('PSU{number} {status}'.format(
                number=psu_number,
                status=psu[1],
            ))

if args.volt_min or args.volt_max:
    for name, position in [('volt1', 10), ('volt2', 20)]:
        volt = float(re.match(r'Voltage: (.*) volts',
                     raw_info['Voltage sensor'][position]).group(1))
        if args.volt_max and volt > args.volt_max:
            criticals.append('{name} is too high ({volt} V)'.format(
                name=name,
                volt=volt,
            ))
        if args.volt_max and volt < args.volt_min:
            criticals.append('{name} is too low ({volt} V)'.format(
                name=name,
                volt=volt,
            ))
        perfdata.append('{name}={volt};;{MIN_VOLT}:{MAX_VOLT};;'.format(
            name=name,
            volt=volt,
            MIN_VOLT=args.volt_min,
            MAX_VOLT=args.volt_max,
        ))

if args.current_min or args.current_max:
    for name, position in [('current1', 8), ('current2', 16)]:
        current = float(re.match(r'Current: (.*) amps',
                        raw_info['Current sensor'][position]).group(1))
        if args.current_max and current > args.current_max:
            criticals.append('{name} is too high ({current} A)'.format(
                name=name,
                current=current,
            ))
        if args.current_min and current < args.current_min:
            criticals.append('{name} is too low ({current} A)'.format(
                name=name,
                current=current,
            ))
        perfdata.append(
            '{name}={current};;{MIN_CURRENT}:{MAX_CURRENT};;'.format(
                name=name,
                current=current,
                MIN_CURRENT=args.current_min,
                MAX_CURRENT=args.current_max,
            ))

if len(criticals) > 1:
    print '{criticals} | {perfdata}'.format(
        criticals=', '.join(criticals) + ', '.join(warnings),
        perfdata=' '.join(perfdata),
    )
    sys.exit(2)
elif len(warnings) > 1:
    print '{warnings} | {perfdata}'.format(
        warnings=', '.join(warnings),
        perfdata=' '.join(perfdata),
    )
    sys.exit(1)
else:
    print 'JBOD OK | {perfdata}'.format(
        perfdata=' '.join(perfdata),
    )
    sys.exit(0)
