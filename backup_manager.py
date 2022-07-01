from asyncio.subprocess import PIPE
import os
import platform
from pathlib import Path
from datetime import datetime, timedelta
from xmlrpc.client import Boolean

from metadata_manager import MetadataManager

# cat /sys/block/mmcblk0/device/cid  # Usable with built-in sd card readers
# sudo fdisk -l /dev/sda # Needed if external reader is used
# sudo dd bs=4M if=/dev/mmcblk0 of=/home/vuk/msd_archive/Ubuntu_test.img status=progress

def glob_format_json_data(data):
    """_summary_

    Args:
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    value = []
    if isinstance(data, dict):
        for key in data.keys():
            if isinstance(data[key], dict):
                value.append(key)
                value.extend(glob_format_json_data(data[key]))
            else:
                value.append(f"{key}:\t{str(data[key])}")
        value = [f"\t{x}" for x in value]
    return value


class BackupManager:
    """_summary_
    """

    def __init__(self):
        self.__supported = platform.system() == "Linux"
        self.__archive_path = ""
        self.__metadata_file_path = ""
        self.__new_archive = False

    def set_archive_path(self, path: Path):
        """ Setter of the archive path.
            Path will be used for storing of the image files.
        Args:
            path (Path): path to directory used for image storing
        """
        self.__archive_path = path
        self.__metadata_file_path = self.__archive_path.joinpath("metadata.json")
        self.__new_archive = not Path.is_file(self.__metadata_file_path)
        
    def is_card_known(self, cardid: str) -> Boolean:
        
        m = MetadataManager(self.__metadata_file_path)

        return m.check_if_field_exists([cardid])

    def read_metadata(self, cardid: str) -> str:
        if self.__new_archive:
            return "New archive, knows nothing"
        
        m = MetadataManager(self.__metadata_file_path)

        data = m.get_field([cardid])
        if data:
            printable_data = '\n'.join(glob_format_json_data(data))
            return f"{cardid}:\n{printable_data}"
        return f"This card id {cardid} is not known yet."


    def store_metadata(self, cardid: str, cardname: str, starttime: datetime):
        """ Method to store metadata for the SD card

        Args:
            cardid (str): unique identifier of the card
            cardname (str): name of the card to be used for user reference
            starttime (datetime): time the storing has started
        """
        update_date = f'{datetime.now().strftime("%d.%m.%Y  %H:%M")}'
        print(update_date)
        avg_time = datetime.now() - starttime
        print(str(avg_time))
        new_bckp_count = 1

        m = MetadataManager(self.__metadata_file_path, self.__new_archive)
        m.add_field([], cardid, {})
        m.add_field([cardid], "name", cardname)
        m.add_field([cardid], "DateOfCreation", update_date)
        m.add_field([cardid], "DateOfUpdate", update_date, True)

        if m.check_if_field_exists([cardid, "BackupAvgTime"]) and m.check_if_field_exists([cardid, "BackupsDone"]):
            bckp_count = int(m.get_field([cardid, "BackupsDone"]))
            timedelta_data = [int(x) for x in m.get_field([cardid, "BackupAvgTime"]).split(':')]
            all_time = bckp_count * timedelta(hours=timedelta_data[0], minutes=timedelta_data[1], seconds=timedelta_data[2])
            all_time = all_time + avg_time
            new_bckp_count = bckp_count + 1
            avg_time = all_time / new_bckp_count
                
        hours = avg_time.seconds // 3600
        minutes = (avg_time.seconds // 60) % 60
        seconds = avg_time.seconds % 60
        
        m.add_field([cardid], "BackupAvgTime", f'{hours:02d}:{minutes:02d}:{seconds:02d}', True)
        m.add_field([cardid], "BackupsDone", str(new_bckp_count), True)

        m.store()

    def get_cid_from_card(self, devicename: str) -> str:
        """ Method to get unique SD card identifier
            Will attempt to fetch CID, but this is not possible for some 
            SD card readers, in which case it will fallback to Disk identifier

        Args:
            devicename (str): device name according to Linux (i.e. /dev/sda1)
        """
        stream = os.popen(f'cat /sys/block/{devicename}/device/cid')
        cid = stream.read().rstrip()
        if not cid:
            stream = os.popen(f'sudo fdisk -l /dev/{devicename}')
            data = stream.read().split("\n")
            cid = [x for x in data if x.startswith("Disk identifier:")][0].split("Disk identifier: ")[1]
        return cid

    def backup_card_to_file(self, device_cid: str, devicename: str, cardname: str, bytesblockcopied: str = "4M") -> Boolean:
        
        if not self.__supported:
            print("This OS is not supported by the library")
            return False

        img_file_name = f'{datetime.now().strftime("%Y%m%d_%H%M")}.img'
        img_archive_path = self.__archive_path.joinpath(device_cid)
        if not img_archive_path.exists():
            img_archive_path.mkdir(parents=True)

        img_archive_path = img_archive_path.joinpath(img_file_name)

        start_time = datetime.now()
        print(start_time)
        cmd = f"sudo dd bs={bytesblockcopied} if=/dev/{devicename} of={img_archive_path} status=progress"
        stream = os.popen(cmd)
        print(stream.read())

        self.store_metadata(device_cid, cardname, start_time)
