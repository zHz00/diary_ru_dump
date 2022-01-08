import requests
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urlparse
from pathlib import Path
import settings as s
import init

init.create_folders()



pic_list_file=open(s.base_folder+s.pics_file,"r",encoding=s.pics_file_encoding)
pics_list_text=pic_list_file.readlines()
pic_list_file.close()

link_list_file=open(s.base_folder+s.links_file,"r",encoding=s.pics_file_encoding)
links_list_text=link_list_file.readlines()
link_list_file.close()


phase=0
for link in links_list_text:
    phase+=1
    #в списке смотрим только каждую третью строку, остальное -- служебная информация
    if phase%3==1:
        continue
    if phase%3==2:
        continue
    #теперь у нас есть урл
    test_url=link.strip()
    for extention in s.pic_checking:
        if test_url.lower().endswith(extention)!=False:
            print("Also: "+test_url)
            pics_list_text.append("notused")
            pics_list_text.append("notused")
            #чтобы эмулировать список картинок, мы должны добавить две строчки... 
            #брать оригинальные две строчки из файла со ссылками не имеет смысла
            #потому что они всё равно не используются
            pics_list_text.append(test_url)





phase=0
pic_names=set()
pic_counter=0
pic_skipped=0
pic_errors=0

warnings=[]

for line in pics_list_text:
    phase+=1
    #в списке смотрим только каждую третью строку, остальное -- служебная информация
    if phase%3==1:
        continue
    if phase%3==2:
        continue
    #теперь у нас есть урл
    pic_url=line.strip()
    pic_name=os.path.basename(urlparse(line.strip()).path).strip()
    if pic_name=='':
        #почему имя оказалось пустым?
        warning="WARNING! URL is empty! line=["+line+"]"
        warnings.append(warning)
        print(warning)
        pic_errors+=1
        continue
    if pic_name in pic_names:
        #очень серьёзный сигнал -- повторение имени картинки. картинки берутся со случайными нечитаемыми названиями, поэтому не должны повторяться
        warning="WARNING! DUPLICATE PIC NAME! ["+pic_name+"]"
        warnings.append(warning)
        print(warning)
        pic_errors+=1
        pic_name="!!!"+pic_name
        #если у нас не две одинаковые картинки, а три или больше -- это всё равно. нам с двумя надо разобраться. я даже сюда поставлю брейкпоинт
        #тем не менее, если я использую одну и ту же картинку в постах несколько раз, а такое бывало, то это не страшно.
        #в этом случае картинка фактически одна и та же, т.е. не только имя файла, но и урл. но пусть остаются три воскл. знака как сигнал
    else:
        pic_names.add(pic_name)


    pic_full_name=s.base_folder+s.pics_folder+pic_name
    if(Path(pic_full_name).is_file()):
        print(pic_url+" already downloaded. Skipping...")
        pic_skipped+=1
        continue
    print("Downloading "+pic_url+"...")
    try:
        pic=requests.get(pic_url,verify=False,headers=s.user_agent)
    except:
        open(s.base_folder+s.pics_folder+pic_name,"wb").close()
        warning="Error during downloading ["+pic_url+"]! Skipping..."
        warnings.append(warning)
        print(warning)
        pic_errors+=1
        continue
    print(f"Done. Size={len(pic.content)}")
    out_pic=open(s.base_folder+s.pics_folder+pic_name,"wb")
    out_pic.write(pic.content)
    out_pic.close()
    print(f"Done saving. Waiting for {s.wait_time} sec...")
    pic_counter+=1
    time.sleep(s.wait_time)

print("Warning list (one more time):")
for warning in warnings:
    print(warning)

print(f"End (download_pics). Downloaded={pic_counter}, skipped={pic_skipped}, errors={pic_errors}")
