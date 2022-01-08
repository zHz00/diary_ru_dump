import time
import datetime
import os
import settings as s
from win32_setctime import setctime
import init

init.create_folders()

file_list=os.listdir(s.base_folder)

counter=0

for post_file_name in file_list:
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

print(f"End update_times. Counter={counter}")