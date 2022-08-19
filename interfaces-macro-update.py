#!/usr/bin/env python3
from pprint import pformat
from pyzabbix import ZabbixAPI
from config import *

devices = {}
file = FILE
with open(file, "r") as file:
    for line in file:
        l = line.split(";")
        device = l[0].strip()
        interface = l[1].strip()
        ap_interfaces = l[2].strip()
        if device not in devices:
            devices.update({
                device: {
                    'interfaces': {},
                    'ap_interfaces': {}}})
        devices[device]['interfaces'].update({interface: True})
        if len(ap_interfaces) > 0:
            devices[device]['ap_interfaces'].update({ap_interfaces: True})

devices_dict = {}
for k in devices.keys():
    interfaces_list = []
    ap_interfaces_list = []
    for i in devices[k]['interfaces'].keys():
        interfaces_list.append(i)
    for apisl in devices[k]['ap_interfaces'].keys():
        apis = apisl.split(" ")
        for i in apis:
            ap_interfaces_list.append(i)
    aggregated_list = ap_interfaces_list + interfaces_list
    regexp = '(^'
    regexp += '|'.join(aggregated_list)
    regexp += '$)'
    devices_dict.update({k: regexp})
print(pformat(devices_dict))

zapi = ZabbixAPI(
        url=REMOTE_ZABBIX_URL,
        user=REMOTE_ZABBIX_USER,
        password=REMOTE_ZABBIX_PASSWORD)

macro_name = '{$NET.IF.IFDESCR.MATCHES}'
for host in devices_dict.keys():
    regexp = devices_dict[host]
    host_current_data = zapi.host.get(
            selectMacros='extend',
            filter={'host': [host]},
            output=['host'])
    print('\n' + pformat(host_current_data))
    updated = False
    if len(host_current_data) > 0:
        for m in host_current_data[0]['macros']:
            hostid = host_current_data[0]['hostid']
            if m['macro'] == macro_name and m['value'] != regexp:
                hostmacroid = m['hostmacroid']
                try:
                    result = zapi.usermacro.update(
                            hostmacroid=hostmacroid,
                            value=regexp)
                    print(pformat(result))
                    print("UPDATED")
                    updated = True
                except Exception as e:
                    print(pformat(e))
            elif m['macro'] == macro_name and m['value'] == regexp:
                updated = True
                print("Already up-to-date.")
        if updated == False:
            try:
                result = zapi.usermacro.create(
                        hostid=hostid,
                        macro=macro_name,
                        value=regexp)
                print(pformat(result))
                print("CREATED")
            except Exception as e:
                print(pformat(e))
    else:
        print('host', host, 'not found?')

