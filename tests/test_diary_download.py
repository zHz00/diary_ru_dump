import download
import pytest
import settings as s
import diary_edit
import time
import logging as l
import datetime
import db

usernames=["user_new_anon","user_new_logged_in","user_old_anon","user_old_logged_in"]

@pytest.mark.parametrize("username_file",usernames)
def test_download_with_comments(username_file:str):
    db.close()
    time.sleep(5.0)
    s.settings_file_name="tests/data/"+username_file+".txt"
    s.wait_time=5
    s.download_html=True

    anon=(username_file.find("anon")!=-1)
    s.load_username(postfix="_a" if anon else "_i")
    if anon:
        assert diary_edit.check_session() == False
    else:
        assert diary_edit.check_session() == True

    logger=l.getLogger()
    while len(logger.handlers)>0:
        logger.removeHandler(logger.handlers[0])
    file_handler=l.FileHandler(filename=s.dump_folder+"py_log"+datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+".log",mode="w",encoding="utf-8")
    file_handler.setFormatter(l.Formatter("%(asctime)s %(levelname)s %(message)s"))
    file_handler.setLevel(l.INFO)
    logger.addHandler(file_handler)
    logger.setLevel(l.INFO)
    l.info("Starting test: "+username_file)
    time.sleep(5.0)
    download.download(update=False,auto_find=True)
    download.download_comments(update=False)

    db_compare_name="posts_"+username_file+"_s1.db"

    db.connect(create=False)
    res=db.check_connection()
    assert res == 0

    report=db.compare_with_other_db("tests/data/"+db_compare_name)

    assert report["POSTS"][0]==[]
    assert report["POSTS"][1]==[]

    assert report["TAGS"][0]==[]
    assert report["TAGS"][1]==[]

    assert report["TAGS_LINKED"][0]==[]
    assert report["TAGS_LINKED"][1]==[]

    assert report["LINKS"][0]==[]
    assert report["LINKS"][1]==[]

    assert report["PICS"][0]==[]
    assert report["PICS"][1]==[]

    assert report["COMMENTS"][0]==[]
    assert report["COMMENTS"][1]==[]
    db.close()

if __name__=="__main__":
    test_download_with_comments("user_new_logged_in")