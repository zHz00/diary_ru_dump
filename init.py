import settings as s
import os
import shutil
from pathlib import Path

def create_folders():
    os.makedirs(s.base_folder+s.pics_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.indexes_folder+s.days_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.tags_folder,exist_ok=True)
    os.makedirs(s.dump_folder,exist_ok=True)
    if(not Path(s.base_folder+s.obsidian_settings_folder).is_dir()):
        os.makedirs(s.base_folder+s.obsidian_settings_folder)
        shutil.copytree(s.obsidian_default_settings_folder,s.base_folder,dirs_exist_ok=True)