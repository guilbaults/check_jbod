import re
import sys
import argparse
import logging
import subprocess


def sg_ses_info(device, page):
    raw_info = {}

    page_cmd = '--page={}'.format(page)
    cmdargs = ['sg_ses', page_cmd, device]
    logging.debug('sg_ses_info: executing: %s', cmdargs)
    try:
        proc = subprocess.Popen(cmdargs,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()
    except OSError as err:
        logging.warning('sg_ses_info: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        logging.debug('sg_ses_info: sg_ses(stderr): %s', line)
        raise subprocess.CalledProcessError

    for line in stdout.decode("utf-8").splitlines():
        logging.debug('sg_ses_info: sg_ses: %s', line)

    if proc.returncode != 0:
        # Unknown
        sys.exit(3)

    current_section = ''
    lines = stdout.decode("utf-8").split('\n')
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
    l_range = range(0, len(input_list), split_count)
    return [input_list[i:i+split_count] for i in l_range]


def ses_get_id_xyratex(sg_name):
    """Get the ID on the LED display on the front of the JBOD"""
    cmdargs = ['sg_ses', '--page=0x02', '--index=14,0', '/dev/' + sg_name]
    logging.debug('ses_get_id_xyratex: executing: %s', cmdargs)
    try:
        stdout, stderr = subprocess.Popen(cmdargs,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
    except OSError as err:
        logging.warning('ses_get_id_xyratex: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        logging.debug('ses_get_id_xyratex: sg_ses(stderr): %s', line)
        raise subprocess.CalledProcessError

    for line in stdout.decode("utf-8").splitlines():
        logging.debug('ses_get_id_xyratex: sg_ses: %s', line)
        # The last 2 digits contain the ID in hex
        mobj = re.match(
            r'\s+Vendor specific element type, status in hex: \w\w \w\w \w\w (\w\w)',  # noqa: E501
            line)
        if mobj:
            return int(mobj.group(1), 16)


def get_sg_jbods():
    """Return the sg device of the enclosures"""
    cmdargs = ['lsscsi', '-g']
    logging.debug('ses_get_enclosure_from_wwn: executing: %s', cmdargs)
    jbods = {}
    try:
        stdout, stderr = subprocess.Popen(cmdargs,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
    except OSError as err:
        logging.warning('get_sg_jbods: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        logging.debug('get_sg_jbods: sg_ses(stderr): %s', line)
        raise subprocess.CalledProcessError

    for line in stdout.decode("utf-8").splitlines():
        logging.debug('get_sg_jbods: sg_ses: %s', line)
        if 'enclosu' in line:
            mobj = re.match(
                r'\[\d+:\d+:\d+:\d+\]\s+enclosu \w+\s+([\w-]+).*\/dev\/(sg\d+)',  # noqa: E501
                line)
            if mobj:
                model = mobj.group(1)
                if model in ['SP-34106-CFFE12P', 'UD-8435-E6EBD', 'MD1420',
                             'SP-3584-E12EBD']:
                    # A JBOD we know
                    sg = mobj.group(2)
                    jbod_id = ses_get_id_xyratex(sg)
                    jbods[jbod_id] = {'model': model, 'sg': '/dev/' + sg}
    return jbods


parser = argparse.ArgumentParser(description='Monitor Fans, PSU and \
temperature in a Xyratex JBOD')
parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")
parser.add_argument("device", help="JBOD ID to check",
                    action="store", default=0, type=int)
parser.add_argument("--fan", help="Check fan", action="store_true")
parser.add_argument("--volt", help="Check voltage", action="store_true")
parser.add_argument("--current", help="Check current", action="store_true")
parser.add_argument("--psu_status", help="PSU status", action="store_true")
parser.add_argument("--temp",
                    help="Check temperatures based on internal thresholds",
                    action="store_true")

args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)

jbods = get_sg_jbods()

if args.device not in jbods:
    print('JBOD with the request ID not found, only found:')
    for jbod in jbods.keys():
        print("model {} with id {}".format(jbods[jbod]['model'], jbod))
    sys.exit(3)

perfdata = []
criticals = []
warnings = []
model = jbods[args.device]['model']
raw_info = sg_ses_info(jbods[args.device]['sg'], '0x02')

if args.verbose:
    print(raw_info.keys())

if args.fan:
    fans = raw_info['Cooling'][5:]
    if model == 'SP-34106-CFFE12P':
        fan_min = [6000, 6000, 6000, 6000, 6000, 6000, 6000, 6000, 2000, 2000]
        fan_max = [9000, 9000, 9000, 9000, 9000, 9000, 9000, 9000, 5000, 5000]
    elif model == 'UD-8435-E6EBD' or model == 'SP-3584-E12EBD':
        fan_min = [6000] * 10
        fan_max = [8000] * 10
    elif model == 'MD1420':
        fan_min = [3000] * 4
        fan_max = [5000] * 4

    for fan in [fans[i:i+4] for i in range(0, len(fans), 4)]:
        fan_number = int(fan[0].split()[1])
        status = re.match(r'.*status: (.*)', fan[1]).group(1)
        speed = int(re.match(r'^Actual speed=(\d+) rpm', fan[3]).group(1))
        if speed < fan_min[fan_number]:
            criticals.append('Fan{fan} is too slow ({rpm} RPM)'.format(
                fan=fan_number,
                rpm=speed,
            ))
        if speed > fan_max[fan_number]:
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
            MIN_FAN=fan_min[fan_number],
            MAX_FAN=fan_max[fan_number],
        ))

if args.temp:
    threshold_info = sg_ses_info(jbods[args.device]['sg'], '0x05')
    temperatures_info = raw_info['Temperature sensor'][6:]
    temp_threshold = threshold_info['Temperature sensor'][4:]
    temperature_thresholds = []

    for threshold in split_list(temp_threshold, 3):
        high = re.match(r"high critical=(\d+), high warning=(\d+)",
                        threshold[1])
        low = re.match(r"low warning=(\d+), low critical=(\d+)",
                       threshold[2])

        # some sensor might not have a threshold defined
        if low is None and high is None:
            temperature_thresholds.append(None)
        else:
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
        if 'reserved' in sensor[4]:
            # no data for this sensor
            continue
        if temperature_thresholds[sensor_id] is None:
            # no thresholds for this sensor
            continue
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
                    number=sensor_id,
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
    if model == 'SP-34106-CFFE12P':
        online_psu = [0, 2]
    elif model == 'UD-8435-E6EBD' or model == 'SP-3584-E12EBD':
        online_psu = [0, 2]
    elif model == 'MD1420':
        online_psu = [0, 1]

    psus = raw_info['Power supply'][6:]
    for psu in [psus[i:i+5] for i in range(0, len(psus), 5)]:
        psu_number = int(psu[0].split()[1])
        if psu_number not in online_psu:
            continue

        status = re.match(r'.*status: (.*)', psu[1]).group(1)
        if psu[1] != 'Predicted failure=0, Disabled=0, Swap=0, status: OK':
            criticals.append('PSU{number} {status}'.format(
                number=psu_number,
                status=psu[1],
            ))
        if psu[3] != 'Hot swap=1, Fail=0, Requested on=0, Off=0, Overtmp fail=0' and psu[3] != 'Hot swap=1, Fail=0, Requested on=1, Off=0, Overtmp fail=0':  # noqa: E501
            criticals.append('PSU{number} {status}'.format(
                number=psu_number,
                status=psu[1],
            ))
        if psu[4] != 'Temperature warn=0, AC fail=0, DC fail=0':
            criticals.append('PSU{number} {status}'.format(
                number=psu_number,
                status=psu[1],
            ))

if args.volt:
    if model == 'SP-34106-CFFE12P':
        volt_min = [11.5, 190, None, None, 11.5, 190, None, None]
        volt_max = [12.5, 255, None, None, 12.5, 255, None, None]
    elif model == 'UD-8435-E6EBD' or model == 'SP-3584-E12EBD':
        volt_min = [11.5, None, 11.5, None]
        volt_max = [12.5, None, 12.5, None]
    elif model == 'MD1420':
        volt_min = [190, 190, 11.5, 11.5, 4.5, 4.5]
        volt_max = [255, 255, 12.5, 12.5, 5.5, 5.5]

    sensors = split_list(raw_info['Voltage sensor'], 5)[2:]

    for position in range(len(sensors)):
        if volt_min[position] is None or volt_max[position] is None:
            continue

        volt = float(re.match(r'Voltage: (.*) volts',
                     sensors[position][0]).group(1))
        name = 'Volt_{}'.format(position)
        if volt > volt_max[position]:
            criticals.append('{name} is too high ({volt} V)'.format(
                name=name,
                volt=volt,
            ))
        if volt < volt_min[position]:
            criticals.append('{name} is too low ({volt} V)'.format(
                name=name,
                volt=volt,
            ))
        perfdata.append('{name}={volt};;{MIN_VOLT}:{MAX_VOLT};;'.format(
            name=name,
            volt=volt,
            MIN_VOLT=volt_min[position],
            MAX_VOLT=volt_max[position],
        ))

if args.current:
    if model == 'SP-34106-CFFE12P':
        current_min = [25, 1, None, None, 25, 1, None, None]
        current_max = [50, 3, None, None, 50, 3, None, None]
    elif model == 'UD-8435-E6EBD' or model == 'SP-3584-E12EBD':
        current_min = [37.5, None, 37.5, None]
        current_max = [45, None, 45, None]
    elif model == 'MD1420':
        current_min = [0.25, 0.25, 3, 3, 0.1, 0.1]
        current_max = [0.45, 0.45, 6, 6, 2, 2]
    sensors = split_list(raw_info['Current sensor'], 4)[2:]

    for position in range(len(sensors)):
        if current_min[position] is None or current_max[position] is None:
            continue

        current = float(re.match(r'Current: (.*) amps',
                        sensors[position][0]).group(1))
        name = 'Current_{}'.format(position)
        if current > current_max[position]:
            criticals.append('{name} is too high ({current} A)'.format(
                name=name,
                current=current,
            ))
        if current < current_min[position]:
            criticals.append('{name} is too low ({current} A)'.format(
                name=name,
                current=current,
            ))
        perfdata.append(
            '{name}={current};;{MIN_CURRENT}:{MAX_CURRENT};;'.format(
                name=name,
                current=current,
                MIN_CURRENT=current_min[position],
                MAX_CURRENT=current_max[position],
            ))

if len(criticals) > 1:
    print('{criticals} | {perfdata}'.format(
        criticals=', '.join(criticals) + ', '.join(warnings),
        perfdata=' '.join(perfdata),
    ))
    sys.exit(2)
elif len(warnings) > 1:
    print('{warnings} | {perfdata}'.format(
        warnings=', '.join(warnings),
        perfdata=' '.join(perfdata),
    ))
    sys.exit(1)
else:
    print('JBOD OK | {perfdata}'.format(
        perfdata=' '.join(perfdata),
    ))
    sys.exit(0)
