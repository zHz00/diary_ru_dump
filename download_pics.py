import time
import os
from urllib.parse import urlparse
from pathlib import Path
import logging as l
import enum
from PIL import Image
import requests

import settings as s
import init
import db

def write_placeholder(file:str) -> None:
    if not hasattr(write_placeholder,"placeholder_image"):
        placeholder_image_stream=open(s.placeholder_image_name,"rb")
        write_placeholder.placeholder_image=placeholder_image_stream.read()
        placeholder_image_stream.close()
    out_pic=open(file,"rb")
    contents=out_pic.read()
    backup_pic=open(s.dump_folder+s.temp_md_folder+s.pics_folder+os.path.basename(file),"wb")
    backup_pic.write(contents)
    backup_pic.close()
    out_pic.close()
    out_pic=open(file,"wb")
    out_pic.write(write_placeholder.placeholder_image)
    out_pic.close()

class cir(enum.Enum):
    ok=0
    not_exist=1
    zero=2
    placeholder=3
    corrupted=4



def check_image(file:str) -> cir:
    if not hasattr(check_image,"placeholder_image"):
        placeholder_image_stream=open(s.placeholder_image_name,"rb")
        check_image.placeholder_image=placeholder_image_stream.read()
        placeholder_image_stream.close()
    #сначала проверим, не является ли картинка плейсхолдером
    if not Path(file).is_file():#файл не существует
        return cir.not_exist
    test_img_stream=open(file,"rb")
    test_img=test_img_stream.read()
    test_img_stream.close()
    if len(test_img)==0:#файл пустой
        return cir.zero
    if test_img==check_image.placeholder_image:#совпадает с заглушкой
        return cir.placeholder
    try:
        img = Image.open(file) # open the image file
        img.verify() # verify that it is, in fact an image
        img.close()
    except (IOError, SyntaxError) as _:
        return cir.corrupted
    return cir.ok


def check_length(name:str)->str:
    name=name.replace("%","-")#с процентами в именах беда
    if len(name)<200:
        return name
    #расширение попробуем сохранить
    l.info("Warning! Too long name! ["+name+"]")
    return name[:195]+name[-5:]

@init.log_call
def download_pics(post_id=-1) -> None:
    print("Stage 4 of 7: Downloading images...")
    if s.download_pics==False:
        print("Skip.")
        return

    #DB
    db.connect()

    placeholders=0

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
        pic_name=os.path.basename(urlparse(line.strip()).path).strip()
        pic_names_for_replace.append([line,pic_name])
        if pic_name=='':
            #почему имя оказалось пустым?
            warning="WARNING! URL is empty! line=["+line+"]"
            warnings.append(warning)
            l.info(warning)
            pic_errors+=1
            continue
        if pic_name in pic_names:
            #очень серьёзный сигнал -- повторение имени картинки. картинки берутся со случайными нечитаемыми названиями, поэтому не должны повторяться
            warning="WARNING! DUPLICATE PIC NAME! ["+pic_name+"]"
            warnings.append(warning)
            l.info(warning)
            pic_errors+=1
            pic_name="!!!"+pic_name
            #если у нас не две одинаковые картинки, а три или больше -- это всё равно. нам с двумя надо разобраться. я даже сюда поставлю брейкпоинт
            #тем не менее, если я использую одну и ту же картинку в постах несколько раз, а такое бывало, то это не страшно.
            #в этом случае картинка фактически одна и та же, т.е. не только имя файла, но и урл. но пусть остаются три воскл. знака как сигнал
        else:
            pic_names.add(pic_name)


        pic_full_name=s.base_folder+s.pics_folder+check_length(pic_name)
        if(Path(pic_full_name).is_file()):
            l.info(pic_url+" already downloaded.")
            pic_skipped+=1
            res=check_image(pic_full_name)
            if res==cir.placeholder:
                l.info("Placeholded image! "+pic_full_name)
                placeholders+=1
            else:
                if res!=cir.ok:
                    l.info("Invalid image! "+pic_full_name+"Replacing to placeholder")
                    write_placeholder(pic_full_name)
                    placeholders+=1
            continue
        l.info("[DB]Downloading "+pic_url+"...")
        print("[DB]Downloading "+pic_url+"...", end="")

        if s.diary_url_mode!=s.dum.from_file:
            try:
                pic=requests.get(pic_url,headers=s.user_agent)
            except:
                write_placeholder(s.base_folder+s.pics_folder+check_length(pic_name))
                placeholders+=1
                warning="[DB]Error during downloading ["+pic_url+"]! Skipping..."
                warnings.append(warning)
                l.info(warning)
                print("Error!")
                pic_errors+=1
                continue
        else:
            try:
                src_pic=open(s.test_folder+check_length(pic_name),"rb")
                pic.content=src_pic.read()
            except:
                write_placeholder(s.base_folder+s.pics_folder+check_length(pic_name))
                placeholders+=1
                warning="[DB]Error opening ["+pic_url+"]! Skipping..."
                warnings.append(warning)
                l.info(warning)
                print("Error!")
                pic_errors+=1
                continue                

        pic_name=check_length(pic_name)
        out_pic=open(s.base_folder+s.pics_folder+pic_name,"wb")
        out_pic.write(pic.content)
        out_pic.close()
        if check_image(s.base_folder+s.pics_folder+pic_name)==False:
            l.info("Invalid image! "+s.base_folder+s.pics_folder+pic_name+"Replacing to placeholder")
            write_placeholder(s.base_folder+s.pics_folder+pic_name)
            placeholders+=1
        l.info(f"[DB]Done saving. Size={len(pic.content)}. Waiting for {s.wait_time} sec...")
        print(f"Done. Size={len(pic.content)}. Waiting {s.wait_time}s")
        pic_counter+=1
        time.sleep(s.wait_time)

    #print("Warning list (one more time):")
    #for warning in warnings:
        #print(warning)

    print(f"[DB]Done. Downloaded={pic_counter}, skipped={pic_skipped}, errors={pic_errors}, placeholders={placeholders}")
    db.close()
    if s.diary_url_mode==s.dum.one_post:
        return pic_names_for_replace
    else:
        return []

if __name__=="__main__":
    init.create_folders()
    download_pics()