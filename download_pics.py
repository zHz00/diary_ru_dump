import requests
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urlparse
from pathlib import Path
import settings as s



pic_list_file=open(s.base_folder+s.pics_file,"r",encoding=s.pics_file_encoding)
pics_list_text=pic_list_file.readlines()

phase=0
pic_names=set()

for i in pics_list_text:
    phase+=1
    if phase%3==1:
        continue
    if phase%3==2:
        continue
    #теперь у нас есть урл
    pic_url=i.strip()
    pic_name=os.path.basename(urlparse(i).path).strip()
    if pic_name=='':
        #почему имя оказалось пустым?
        print("WARNING! URL is empty!")
        continue
    if pic_name in pic_names:
        #очень серьёзный сигнал -- повторение имени картинки. картинки берутся со случайными нечитаемыми названиями, поэтому не должны повторяться
        print("WARNING! DUPLICATE PIC NAME!")
        pic_name="!!!"+pic_name
        #если у нас не две одинаковые картинки, а три или больше -- это всё равно. нам с двумя надо разобраться. я даже сюда поставлю брейкпоинт
        #тем не менее, если я использую одну и ту же картинку в постах несколько раз, а такое бывало, то это не страшно.
        #в этом случае картинка фактически одна и та же, т.е. не только имя файла, но и урл. но пусть остаются три воскл. знака как сигнал
    else:
        pic_names.add(pic_name)


    pic_full_name=s.base_folder+s.pics_folder+pic_name
    if(Path(pic_full_name).is_file()):
        print(pic_url+" already downloaded. Skipping...")
        continue
    print("Downloading "+pic_url+"...")
    try:
        pic=requests.get(pic_url,verify=False)
    except:
        print("Error during downloading! Skipping...")
        open(s.base_folder+s.pics_folder+pic_name,"wb").close()
        continue
    print(f"Done. Size={len(pic.content)}")
    out_pic=open(s.base_folder+s.pics_folder+pic_name,"wb")
    out_pic.write(pic.content)
    out_pic.close()
    print("Done saving. Waiting for 1 minute...")
    time.sleep(s.wait_time)

    print("End (download_pics)")
