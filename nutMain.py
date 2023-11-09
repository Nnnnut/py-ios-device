# from tests.test_ios_device import TestIOSDevice # python -m pip install pytest pyopenssl pyasn1 coloredlogs construct six requests dataclasses
# from ios_device.util import Log

# nutL.info('TestIOSDevice()')


# if __name__ == '__main__':
#     tdevice = TestIOSDevice()
#     nutL.info('tdevice.create_device()')
#     tdevice.create_device()
#     nutL.info('tdevice.test_start_get_fps()')
#     tdevice.test_start_get_fps()
#     nutL.info('end')

from ios_device.py_ios_device import PyiOSDevice
from ios_device.util import Log
import time

nutL = Log.getLogger('Nut')

def call_back(res):
    print(res)

if __name__ == '__main__':
    nutL.info('PyiOSDevice() init')
    server = PyiOSDevice()
    nutL.info('start_get_fps() call')
    chanl = server.start_get_fps(callback = call_back)
    nutL.info('time.sleep(10)')
    time.sleep(3)
    nutL.info('stop_get_fps() call')
    # server.stop_get_fps()
    server.stop()
    nutL.info('start_get_fps() end')