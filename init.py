import settings as s
import os
import shutil
from pathlib import Path

def create_folders() -> None:
    os.makedirs(s.base_folder+s.pics_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.indexes_folder+s.days_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.tags_folder,exist_ok=True)
    os.makedirs(s.dump_folder,exist_ok=True)
    if(not Path(s.base_folder+s.obsidian_settings_folder).is_dir()):
        os.makedirs(s.base_folder+s.obsidian_settings_folder)
        shutil.copytree(s.obsidian_default_settings_folder,s.base_folder,dirs_exist_ok=True)
    os.makedirs(s.base_folder_db+s.pics_folder,exist_ok=True)
    os.makedirs(s.base_folder_db+s.indexes_folder+s.days_folder,exist_ok=True)
    os.makedirs(s.base_folder_db+s.tags_folder,exist_ok=True)
    os.makedirs(s.dump_folder,exist_ok=True)
    if(not Path(s.base_folder_db+s.obsidian_settings_folder).is_dir()):
        os.makedirs(s.base_folder_db+s.obsidian_settings_folder)
        shutil.copytree(s.obsidian_default_settings_folder,s.base_folder_db,dirs_exist_ok=True)


def reset_vault() -> None:
    print("Resetting vault...",end="")
    for file in os.listdir(s.base_folder):
        path=s.base_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(s.base_folder+s.tags_folder):
        path=s.base_folder+s.tags_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(s.base_folder+s.indexes_folder):
        path=s.base_folder+s.indexes_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(s.base_folder+s.indexes_folder+s.days_folder):
        path=s.base_folder+s.indexes_folder+s.days_folder+file
        if(Path(path).is_file()):
            os.remove(path)

    for file in os.listdir(s.base_folder_db):
        path=s.base_folder_db+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(s.base_folder_db+s.tags_folder):
        path=s.base_folder_db+s.tags_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(s.base_folder_db+s.indexes_folder):
        path=s.base_folder_db+s.indexes_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(s.base_folder_db+s.indexes_folder+s.days_folder):
        path=s.base_folder_db+s.indexes_folder+s.days_folder+file
        if(Path(path).is_file()):
            os.remove(path)

    print("Done.")

#тут получается сильное дублирование кода, но я хочу оставить так, поскольку папки очень различаются по смыслу
#я хочу чётко видеть, что удаляется

def delete_obsidian_settings() -> None:
    for file in os.listdir(s.base_folder+s.obsidian_settings_folder):
        path=s.base_folder+s.obsidian_settings_folder+file
        if(Path(path).is_file()):
            os.remove(path)

def delete_pics() -> None:
    for file in os.listdir(s.base_folder+s.pics_folder):
        path=s.base_folder+s.pics_folder+file
        if(Path(path).is_file()):
            os.remove(path)

def delete_tags() -> None:
    for file in os.listdir(s.base_folder+s.tags_folder):
        path=s.base_folder+s.tags_folder+file
        if(Path(path).is_file()):
            os.remove(path)

def delete_indexes() -> None:
    for file in os.listdir(s.base_folder+s.indexes_folder+s.days_folder):
        path=s.base_folder+s.indexes_folder+s.days_folder+file
        if(Path(path).is_file()):
            os.remove(path)

    for file in os.listdir(s.base_folder+s.indexes_folder):
        path=s.base_folder+s.indexes_folder+file
        if(Path(path).is_file()):
            os.remove(path)

def delete_dump() -> None:
    for file in os.listdir(s.dump_folder):
        path=s.dump_folder+file
        if(Path(path).is_file()):
            os.remove(path)

def delete_folder_without_exception(folder: str) -> None:
    try:
        os.rmdir(folder)
    except:
        print("WARNING! Folder already removed: "+folder)

def delete_folders() -> None:
    #опять-таки, я мог бы удалить rmtree, но не хочу, чтобы случайно удалилось лишнее, поэтому удаляю по одной папке
    delete_folder_without_exception(s.dump_folder)
    delete_folder_without_exception(s.base_folder+s.pics_folder)
    delete_folder_without_exception(s.base_folder+s.tags_folder)
    delete_folder_without_exception(s.base_folder+s.indexes_folder+s.days_folder)
    delete_folder_without_exception(s.base_folder+s.indexes_folder)
    delete_folder_without_exception(s.base_folder+s.obsidian_settings_folder)
    delete_folder_without_exception(s.base_folder)
    