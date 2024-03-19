import pytest
import sys
import os
  
sys.path.append('./')

from download import download
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
import settings as s
import init

'''
from .. import settings
from .. import download
from .. import download_pics
from .. import markdown_all_diary
from .. import replace_urls
from .. import create_indexes
from .. import update_times
from .. import init
'''

def test_always_pass() -> None:
    assert True

@pytest.mark.xfail
def test_always_fail() -> None:
    assert False

def test_new_design_file() -> None:
    s.change_username("testname","")
    s.diary_url=s.test_folder+"new_design"
    s.diary_url_mode=s.dum.from_file
    s.start=20
    s.stop=20
    s.wait_time=5
    init.create_folders()
    init.reset_vault(s.base_folder)
    init.delete_obsidian_settings()
    init.delete_pics()
    init.delete_indexes()
    init.delete_tags()

    init.delete_dump()
    '''
    download(update=False,auto_find=False)
    markdown_all_diary(reset=True)
    download_pics()
    replace_urls()
    create_indexes()
    update_times()'''
    init.delete_folders()

if __name__=="__main__":
    test_always_pass()
    #test_always_fail()
    test_new_design_file()
