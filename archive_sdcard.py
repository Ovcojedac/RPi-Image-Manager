import os
from argparse import ArgumentParser
from pathlib import Path
from backup_manager import BackupManager

parser = ArgumentParser(description='SD Card backup script')
parser.add_argument('-a', '--archive', help='Archive directory, will use default from env var IMAGE_ARCHIVE', default=os.environ['IMAGE_ARCHIVE'])
parser.add_argument('-d', '--device', help='Device name of the sd card (i.e. sda, mmblock)', required=True)
parser.add_argument('-n', '--name', help='Name of the sd card for the archive (i.e. My RPI 3 card), defaults to \"An SD Card\"')
args = parser.parse_args()

B = BackupManager()
B.set_archive_path(Path(args.archive))

device = args.device
device_id = B.get_cid_from_card(device)
print("\n" + B.read_metadata(device_id))

sd_card_name = args.name or "An SD Card"
B.backup_card_to_file(device_id, device, sd_card_name, "16M")