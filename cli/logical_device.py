#!/usr/bin/env python
#
# Copyright 2016 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Logical device level CLI commands
"""
from cmd2 import Cmd
from simplejson import dumps

from cli.table import print_pb_as_table, print_pb_list_as_table
from cli.utils import pb2dict
from cli.utils import print_flows
from voltha.protos import third_party
from google.protobuf.empty_pb2 import Empty

_ = third_party
from voltha.protos import voltha_pb2


class LogicalDeviceCli(Cmd):

    def __init__(self, get_channel, logical_device_id):
        Cmd.__init__(self)
        self.get_channel = get_channel
        self.logical_device_id = logical_device_id
        self.prompt = '(' + self.colorize(
            self.colorize('logical device {}'.format(logical_device_id), 'red'),
            'bold') + ') '

    def cmdloop(self):
        self._cmdloop()

    def get_logical_device(self, depth=0):
        stub = voltha_pb2.VolthaLocalServiceStub(self.get_channel())
        res = stub.GetLogicalDevice(voltha_pb2.ID(id=self.logical_device_id),
                                    metadata=(('get-depth', str(depth)), ))
        return res

    def get_device(self, id):
        stub = voltha_pb2.VolthaLocalServiceStub(self.get_channel())
        return stub.GetDevice(voltha_pb2.ID(id=id))

    def get_devices(self):
        stub = voltha_pb2.VolthaLocalServiceStub(self.get_channel())
        res = stub.ListDevices(Empty())
        return res.items

    do_exit = Cmd.do_quit

    def do_show(self, _):
        """Show detailed logical device information"""
        omit_fields = {
            'flow_groups',
            'flows',
            'ports',
            'switch_features.auxiliary_id',
            'switch_features.capabilities',
            'switch_features.datapath_id',
            'switch_features.n_buffers',
            'switch_features.n_tables',
            'desc.dp_desc',
            'desc.hw_desc',
            'desc.mfr_desc',
            'desc.serial_num',
            'desc.sw_desc',
            'datapath_id'
        }
        print_pb_as_table('Logical device {}'.format(self.logical_device_id),
                          self.get_logical_device(depth=-1), omit_fields)

    def do_ports(self, _):
        """Show ports of logical device"""
        device = self.get_logical_device(depth=-1)
        omit_fields = {
            'ofp_port.advertised',
            'ofp_port.peer',
            'ofp_port.max_speed',
        }
        print_pb_list_as_table('Logical device ports:', device.ports,
                               omit_fields, self.poutput)

    def do_flows(self, _):
        """Show flow table for logical device"""
        logical_device = pb2dict(self.get_logical_device(-1))
        print_flows(
            'Logical Device',
            self.logical_device_id,
            type='n/a',
            flows=logical_device['flows']['items'],
            groups=logical_device['flow_groups']['items']
        )

    def do_devices(self, line):
        """List devices that belong to this logical device"""
        logical_device = self.get_logical_device()
        root_device_id = logical_device.root_device_id
        devices = [self.get_device(root_device_id)]
        for d in self.get_devices():
            if d.parent_id == root_device_id:
                devices.append(d)
        omit_fields = {
            'adapter',
            'vendor',
            'model',
            'hardware_version',
            'software_version',
            'firmware_version',
            'serial_number',
            'parent_port_no',
            'vlan',
            'ports',
            'reason',
            'root',
            'parent_id'
        }
        print_pb_list_as_table('Devices:', devices, omit_fields, self.poutput)

