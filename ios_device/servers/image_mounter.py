import logging
import os
import typing


class MobileImageMounter(object):

    SERVICE_NAME = 'com.apple.mobile.mobile_image_mounter'

    def __init__(self, lockdown=None, udid=None, logger=None,service=None): # (service=`LockdownClient`._start_service("com.apple.mobile.mobile_image_mounter"))
        from ..util.lockdown import LockdownClient
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid)
        self.service = service or self.lockdown.start_service(self.SERVICE_NAME)

        if not self.lockdown:
            raise Exception("Unable to start lockdown")
        if not self.service:
            raise Exception("installation_proxy init error : Could not start com.apple.mobile.mobile_image_mounter")

    def lookup(self, image_type="Developer") -> typing.List[bytes]:
        """
        Check image signature
        """
        ret = self.service.plist_request({
            "Command": "LookupImage",
            "ImageType": image_type,
        })
        if 'Error' in ret:
            raise Exception(ret['Error'])
        return ret.get('ImageSignature', [])

    def is_developer_mounted(self) -> bool:
        """
        Check if developer image mounted

        Raises:
            MuxError("DeviceLocked")
        """
        return len(self.lookup()) > 0

    def _check_error(self, ret: dict):
        if 'Error' in ret:
            raise Exception(ret['Error'])

    def mount(self,
              image_path: str,              # C:\Users\blue2\AppData\Local\Temp\tmprjvd8_tm\16.3\DeveloperDiskImage.dmg
              image_signature_path: str):   # C:\Users\blue2\AppData\Local\Temp\tmprjvd8_tm\16.3\DeveloperDiskImage.dmg.signature
        """ Mount developer disk image from local files """
        assert os.path.isfile(image_path), image_path
        assert os.path.isfile(image_signature_path), image_signature_path

        with open(image_signature_path, 'rb') as f:
            signature_content = f.read()

        image_size = os.path.getsize(image_path) # 返回指定文件的字节大小

        with open(image_path, "rb") as image_reader:
            return self.mount_fileobj(image_reader, image_size, signature_content)

    def mount_fileobj(self,
                      image_reader: typing.IO,  # open(DeveloperDiskImage.dmg)
                      image_size: int,          # os.path.getsize(DeveloperDiskImage.dmg)
                      signature_content: bytes, # open(DeveloperDiskImage.dmg.signature).read()
                      image_type: str = "Developer"):

        ret = self.service.plist_request({ # 发送 DeveloperDiskImage.dmg.signature
            "Command": "ReceiveBytes",
            "ImageSignature": signature_content,
            "ImageSize": image_size,
            "ImageType": image_type,
        })
        self._check_error(ret)
        assert ret['Status'] == 'ReceiveBytesAck'

        # Send data through SSL
        logging.info("Pushing DeveloperDiskImage.dmg")
        chunk_size = 1 << 14 # 16384

        while True:                                 # 发送 DeveloperDiskImage.dmg
            chunk = image_reader.read(chunk_size)   # 一次读取最多16384 bytes
            if not chunk:
                break
            self.service.sock.sendall(chunk)

        ret = self.service.recv_plist()
        self._check_error(ret)

        assert ret['Status'] == 'Complete'
        logging.info("Push complete")

        self.service.send_plist({
            "Command": "MountImage",
            "ImagePath": "/private/var/mobile/Media/PublicStaging/staging.dimag",
            "ImageSignature": signature_content,
            "ImageType": image_type,
        })
        ret = self.service.recv_plist()
        if 'DetailedError' in ret:
            if 'is already mounted at /Developer' in ret['DetailedError']:
                raise Exception("DeveloperImage is already mounted")
            if 'Developer mode is not enabled' in ret['DetailedError']:
                raise Exception('Developer mode is not enabled. try `pyidevice enable_developer_mode`')

