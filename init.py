import os
import filecmp
import shutil
from pathlib import Path
import logging as l
import inspect

import settings as s

def create_folders() -> None:
    os.makedirs(s.base_folder,exist_ok=True)
    os.makedirs(s.dump_folder,exist_ok=True)

    os.makedirs(s.base_folder+s.pics_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.pics_folder+s.pics_censor_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.pics_folder+s.pics_duplicate_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.indexes_folder+s.days_folder,exist_ok=True)
    os.makedirs(s.base_folder+s.tags_folder,exist_ok=True)
    os.makedirs(s.dump_folder,exist_ok=True)
    if(not Path(s.base_folder+s.obsidian_settings_folder).is_dir()):
        os.makedirs(s.base_folder+s.obsidian_settings_folder)
        shutil.copytree(s.obsidian_default_settings_folder,s.base_folder,dirs_exist_ok=True)

    os.makedirs(s.dump_folder+s.temp_md_folder+s.pics_folder,exist_ok=True)
    os.makedirs(s.dump_folder+s.temp_md_folder+s.pics_folder+s.pics_censor_folder,exist_ok=True)
    os.makedirs(s.dump_folder+s.temp_md_folder+s.pics_folder+s.pics_duplicate_folder,exist_ok=True)
    os.makedirs(s.dump_folder+s.temp_md_folder+s.indexes_folder+s.days_folder,exist_ok=True)
    os.makedirs(s.dump_folder+s.temp_md_folder+s.tags_folder,exist_ok=True)
    if(not Path(s.dump_folder+s.temp_md_folder+s.obsidian_settings_folder).is_dir()):
        os.makedirs(s.dump_folder+s.temp_md_folder+s.obsidian_settings_folder)
        shutil.copytree(s.obsidian_default_settings_folder,s.dump_folder+s.temp_md_folder,dirs_exist_ok=True)



def reset_vault(folder) -> None:
    print("Resetting vault...",end="")
    for file in os.listdir(folder):
        path=folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(folder+s.tags_folder):
        path=folder+s.tags_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(folder+s.indexes_folder):
        path=folder+s.indexes_folder+file
        if(Path(path).is_file()):
            os.remove(path)
    for file in os.listdir(folder+s.indexes_folder+s.days_folder):
        path=folder+s.indexes_folder+s.days_folder+file
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
    
def log_call(func):
    def wrap(*args, **kwargs):
        # Log the function name and arguments
        l.info(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        
        # Call the original function
        result = func(*args, **kwargs)
        
        # Log the return value
        #l.info(f"{func.__name__} returned: {result}")
        
        # Return the result
        l.info(f"Returning {func.__name__}: {result}")
        return result
    return wrap

def get_function_name():
    # get the frame object of the function
    frame = inspect.currentframe()
    return frame.f_back.f_code.co_name

class dircmp_report:
    left_only=[]
    right_only=[]
    diff_files=[]

class dircmp_deep(filecmp.dircmp):
    """
    Compare the content of dir1 and dir2. In contrast with filecmp.dircmp, this
    subclass compares the content of files with the same path.
    """
    def phase3(self):
        """
        Find out differences between common files.
        Ensure we are using content comparison with shallow=False.
        """
        fcomp = filecmp.cmpfiles(self.left, self.right, self.common_files,
                                 shallow=False)
        self.same_files, self.diff_files, self.funny_files = fcomp

    def report_full_closure_as_list(self):
        r=dircmp_report()
        """        r.left_only=[self.left+ x for x in self.left_only]
        r.right_only=[self.right+ x for x in self.right_only]
        r.diff_files=[self.left+ x for x in self.diff_files]#показываем путь лефт, потому что всё равно, показывать лефт или райт
        self.subdirs
        for sd in self.subdirs.values():
            r_tmp=dircmp_report()
            sd_dircmp=dircmp_deep(sd.left,sd.right)#игнор пока не настраивается
            r_tmp=sd_dircmp.report_full_closure_as_list()
            r.left_only.extend([self.left+ x for x in r_tmp.left_only])
            r.right_only.extend([self.right+ x for x in r_tmp.right_only])
            r.diff_files.extend([self.left+ x for x in r_tmp.diff_files])
        return r"""

        """r.left_only=self.left_only.copy()
        r.right_only=self.right_only.copy()
        r.diff_files=self.diff_files.copy()#показываем путь лефт, потому что всё равно, показывать лефт или райт"""
        r.left_only=[self.left+"/"+ x for x in self.left_only]
        r.right_only=[self.right+"/"+ x for x in self.right_only]
        r.diff_files=[self.left+"/"+ x for x in self.diff_files]#показываем путь лефт, потому что всё равно, показывать лефт или райт
        for sd in self.subdirs.values():
            r_tmp=dircmp_report()
            sd_dircmp=dircmp_deep(sd.left,sd.right)#игнор пока не настраивается
            r_tmp=sd_dircmp.report_full_closure_as_list()
            r.left_only.extend(r_tmp.left_only.copy())
            r.right_only.extend(r_tmp.right_only.copy())
            r.diff_files.extend(r_tmp.diff_files.copy())
        return r