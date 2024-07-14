import pytest
import logging as l
import datetime
import shutil
import zipfile

import db
import settings as s
from markdown_all_diary import markdown_all_diary
from download_pics import download_pics
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
from init import dircmp_deep


usernames=["user_new_anon","user_new_logged_in","user_old_anon","user_old_logged_in"]
pics_enabled_list=[True,False]

@pytest.mark.parametrize("pics_enabled",pics_enabled_list)
@pytest.mark.parametrize("username_file",usernames)
def test_markup(username_file:str,pics_enabled:bool):
    db.close()
    s.settings_file_name="tests/data/"+username_file+".txt"
    s.wait_time=5
    s.download_html=True
    s.download_pics=pics_enabled

    anon=(username_file.find("anon")!=-1)
    postfix="_a" if anon else "_i"
    pics_postfix="" if pics_enabled else "_nopics"
    s.load_username(postfix=postfix)

    logger=l.getLogger()
    while len(logger.handlers)>0:
        logger.removeHandler(logger.handlers[0])
    file_handler=l.FileHandler(filename=s.dump_folder+"py_log"+datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+".log",mode="w",encoding="utf-8")
    file_handler.setFormatter(l.Formatter("%(asctime)s %(levelname)s %(message)s"))
    file_handler.setLevel(l.INFO)
    logger.addHandler(file_handler)
    logger.setLevel(l.INFO)
    l.info("Starting test: "+username_file)

    shutil.copy("tests/data/posts_"+username_file+"_s1.db",s.dump_folder+"posts.db")

    shutil.copytree("tests/data/.obsidian/",s.base_folder+"/.obsidian/",dirs_exist_ok=True)

    if pics_enabled:#копируем
        shutil.copytree("tests/data/pics/",s.base_folder+s.pics_folder,dirs_exist_ok=True)

    
    markdown_all_diary(reset=True)
    download_pics()
    replace_urls()
    create_indexes()
    update_times()

    #готовим каталог для сравнения

    dc=dircmp_deep(s.base_folder,"tests/data/"+username_file+pics_postfix,ignore=["pics"])
    #dc.clear_cache()
    report=dc.report_full_closure_as_list()
    l.info("LEFT:"+str(report.left_only))
    l.info("RIGHT (test):"+str(report.right_only))
    l.info("FILES:"+str(report.diff_files))

if __name__=="__main__":
    test_markup("user_new_logged_in",True)