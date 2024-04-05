import requests
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urlparse
from pathlib import Path

import settings as s
import init
import db

def check_length(name:str)->str:
    name=name.replace("%","-")#с процентами в именах беда
    if len(name)<200:
        return name
    #расширение попробуем сохранить
    print("Warning! Too long name! ["+name+"]")
    return name[:195]+name[-5:]

def download_pics(post_id=-1) -> None:
    print("Stage 4 of 7: Downloading images...")
    if s.download_pics==False:
        print("Skip.")
        return

    #DB
    db.connect()
    if s.diary_url_mode==s.dum.one_post:
        pics_list_db=db.get_pics_list_plain(post_id)
    else:
        pics_list_db=db.get_pics_list_plain()
    print(f"[DB]Ordinary pictures:{len(pics_list_db)}")

    links_list_db=db.get_links_list_plain(post_id)

    pics_from_urls=0
    for link in links_list_db:
        test_url=link.strip()
        for extention in s.pic_checking:
            if test_url.lower().endswith(extention)!=False:
                #print("Also: "+test_url)
                pics_from_urls+=1
                #чтобы эмулировать список картинок, мы должны добавить две строчки... 
                #брать оригинальные две строчки из файла со ссылками не имеет смысла
                #потому что они всё равно не используются
                pics_list_db.append(test_url)


    print(f"[DB]Pictures from urls:{pics_from_urls}")
    total_pics=len(pics_list_db)
    print(f"[DB]Total: {total_pics} images.")


    pic_names=set()
    pic_counter=0
    pic_skipped=0
    pic_errors=0
    n=0

    warnings=[]
    pic_names_for_replace=[]

    for line in pics_list_db:
        pic_url=line.strip()
        n+=1
        percentage=int(n/total_pics*100)
        percentage_header=f"[DB][{percentage}%]"
        pic_name=os.path.basename(urlparse(line.strip()).path).strip()
        pic_names_for_replace.append([line,pic_name])
        if pic_name=='':
            #почему имя оказалось пустым?
            warning="WARNING! URL is empty! line=["+line+"]"
            warnings.append(warning)
            print(percentage_header+warning)
            pic_errors+=1
            continue
        if pic_name in pic_names:
            #очень серьёзный сигнал -- повторение имени картинки. картинки берутся со случайными нечитаемыми названиями, поэтому не должны повторяться
            warning="WARNING! DUPLICATE PIC NAME! ["+pic_name+"]"
            warnings.append(warning)
            print(percentage_header+warning)
            pic_errors+=1
            pic_name="!!!"+pic_name
            #если у нас не две одинаковые картинки, а три или больше -- это всё равно. нам с двумя надо разобраться. я даже сюда поставлю брейкпоинт
            #тем не менее, если я использую одну и ту же картинку в постах несколько раз, а такое бывало, то это не страшно.
            #в этом случае картинка фактически одна и та же, т.е. не только имя файла, но и урл. но пусть остаются три воскл. знака как сигнал
        else:
            pic_names.add(pic_name)


        pic_full_name=s.base_folder+s.pics_folder+check_length(pic_name)
        if(Path(pic_full_name).is_file()):
            print(percentage_header+pic_url+" already downloaded. Skipping...")
            pic_skipped+=1
            continue
        print(percentage_header+"[DB]Downloading "+pic_url+"...")

        if s.diary_url_mode!=s.dum.from_file:
            try:
                pic=requests.get(pic_url,headers=s.user_agent)
            except:
                open(s.base_folder+s.pics_folder+pic_name,"wb").close()
                warning="[DB]Error during downloading ["+pic_url+"]! Skipping..."
                warnings.append(warning)
                print(percentage_header+warning)
                pic_errors+=1
                continue
        else:
            try:
                src_pic=open(s.test_folder+pic_name,"rb")
                pic.content=src_pic.read()
            except:
                open(s.base_folder+s.pics_folder+pic_name,"wb").close()
                warning="[DB]Error during downloading ["+pic_url+"]! Skipping..."
                warnings.append(warning)
                print(percentage_header+warning)
                pic_errors+=1
                continue                

        pic_name=check_length(pic_name)
        out_pic=open(s.base_folder+s.pics_folder+pic_name,"wb")
        out_pic.write(pic.content)
        out_pic.close()
        print(percentage_header+f"[DB]Done saving. Size={len(pic.content)}. Waiting for {s.wait_time} sec...")
        pic_counter+=1
        time.sleep(s.wait_time)

    print("Warning list (one more time):")
    for warning in warnings:
        print(warning)

    print(f"[DB]Done. Downloaded={pic_counter}, skipped={pic_skipped}, errors={pic_errors}")
    db.close()
    if s.diary_url_mode==s.dum.one_post:
        return pic_names_for_replace
    else:
        return []

if __name__=="__main__":
    init.create_folders()
    download_pics()