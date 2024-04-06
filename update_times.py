import time
import datetime
import os
from win32_setctime import setctime
import tqdm

import settings as s
import init

def update_times() -> None:
    print("Stage 7 of 7: Update file creation time...")
    if os.name!="nt":
        print("Skip.\nupdate_times now work only on Windows! Sorry...")
        return

    file_list=os.listdir(s.base_folder)

    counter=0

    for post_file_name in tqdm.tqdm(file_list,ascii=True):
        if post_file_name.endswith(".md")==False:
            continue
        post_file_name=s.base_folder+post_file_name.strip()
        post_file=open(post_file_name,"r",encoding=s.post_list_encoding)
        post_contents=post_file.readlines()
        if len(post_contents)<5:
            continue #это не настоящий пост а какая-то ерунда
        post_date=post_contents[4].strip()
        post_file.close()
        post_time=time.mktime(datetime.datetime.strptime(post_date,"%Y-%m-%d, %H:%M").timetuple())
        setctime(post_file_name, post_time)
        counter+=1

    print(f"Done\nEnd update_times. Counter={counter}")

if __name__=="__main__":
    init.create_folders()
    update_times()