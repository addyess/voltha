#
# Copyright 2018 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
BBSim adapter based on a acme adapter
"""
import structlog
from copy import deepcopy

from voltha.protos.device_pb2 import DeviceType
from voltha.protos.adapter_pb2 import AdapterConfig
from voltha.protos.adapter_pb2 import Adapter
from voltha.protos.common_pb2 import LogLevel
from voltha.adapters.openolt.openolt import OpenoltAdapter, OpenOltDefaults
from voltha.adapters.bbsimolt.bbsimolt_flow_mgr import BBSimOltFlowMgr
from voltha.adapters.bbsimolt.bbsimolt_statistics import BBSimOltStatisticsMgr
from voltha.adapters.bbsimolt.bbsimolt_bw import BBSimOltBW
from voltha.adapters.bbsimolt.bbsimolt_alarms import BBSimOltAlarmMgr
from voltha.adapters.bbsimolt.bbsimolt_platform import BBSimOltPlatform
from voltha.adapters.bbsimolt.bbsimolt_device import BBSimOltDevice

log = structlog.get_logger()

class BBSimOltAdapter(OpenoltAdapter):
    name = 'bbsimolt'

    supported_device_types = [
        DeviceType(
            id=name,
            adapter=name,
            accepts_bulk_flow_update=True,
            accepts_direct_logical_flows_update=True
        )
    ]

    def __init__(self, adapter_agent, config):
        super(BBSimOltAdapter, self).__init__(adapter_agent, config)

        # overwrite the descriptor
        self.descriptor = Adapter(
            id=self.name,
            vendor='CORD',
            version='0.1',
            config=AdapterConfig(log_level=LogLevel.INFO)
        )
        self.bbsim_id = 17  #TODO: This should be modified later

    def adopt_device(self, device):
        self.bbsim_id += 1
        log.info('adopt-device', device=device)

        support_classes = deepcopy(OpenOltDefaults)['support_classes']

        # Customize platform
        support_classes['platform'] = BBSimOltPlatform
        support_classes['flow_mgr'] = BBSimOltFlowMgr
        support_classes['alarm_mgr'] = BBSimOltAlarmMgr
        support_classes['stats_mgr'] = BBSimOltStatisticsMgr
        support_classes['bw_mgr'] = BBSimOltBW
        kwargs = {
            'support_classes': support_classes,
            'adapter_agent': self.adapter_agent,
            'device': device,
            'device_num': self.num_devices + 1,
            'dp_id': '00:00:00:00:00:' + hex(self.bbsim_id)[-2:]
        }
        try:
            self.devices[device.id] = BBSimOltDevice(**kwargs)
        except Exception as e:
            log.error('Failed to adopt BBSimOLT device', error=e)
            del self.devices[device.id]
            raise
        else:
            self.num_devices += 1

    def delete_device(self, device):
        self.bbsim_id -= 1
        super(BBSimOltAdapter, self).delete_device(device)
        self.num_devices -= 1