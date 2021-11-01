import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urlparse
from pathlib import Path

def post_replace(file_name,str_from,str_to):
    post_r=open(file_name,"r",encoding="utf-8")
    post_contents=post_r.read()
    post_r.close()
    post_contents=post_contents.replace(str_from,str_to)

    post_w=open(file_name,"w",encoding="utf-8")
    post_w.write(post_contents)
    post_w.close()

base_folder="diary_zhz_obsidian\\"
pics_folder="pics/"

pics_list_file=open(base_folder+"pics.txt","r",encoding="utf-8")
pics_list_text=pics_list_file.readlines()

links_list_file=open(base_folder+"links.txt","r",encoding="utf-8")
links_list_text=links_list_file.readlines()

def strip_post_id(url):
    id_begin_raw1=url.find("00/p")
    id_begin_raw2=url.find("00.diary.ru/p")
    if(id_begin_raw1==-1 and id_begin_raw2==-1):
        return "-1"
    if(id_begin_raw1==-1):
        id_begin=id_begin_raw2+13
    else:
        id_begin=id_begin_raw1+4
    return url[id_begin:id_begin+9]


phase=0

for i in pics_list_text:
    phase+=1
    if phase%3==1:
        continue
    if phase%3==2:
        post_name=i.strip()
        continue
    #теперь у нас есть урл
    pic_url=i.strip()
    pic_name=os.path.basename(urlparse(i).path).strip()

    post_replace(base_folder+post_name+".md",pic_url,pics_folder+pic_name)

links=[]
link={}

#прочтём список ссылок

for i in links_list_text:
    phase+=1
    if phase%3==1:
        link['id']=i.strip()
    if phase%3==2:
        link['name']=i.strip()
    if phase%3==0:
        link['url']=i.strip()
        links.append(link)
        link={}

for link_src in links:
    if link_src['name']=="Желания в NetHack (часть 12)":
        dummy=0
    id_dest=strip_post_id(link_src['url'])
    if id_dest==link_src['id']:
        continue
    found=False
    for link_dest in links:
        if link_dest['id']==id_dest:
            #нашли целевой файл
            found=True
            print(f"Replacing {link_src['url']} to {link_dest['name']}")
            post_replace(base_folder+link_src["name"]+".md",link_src['url'],(link_dest['name'].replace(" ","%20")))
            break
            #т.к. уже нашли дальше неча смотреть
    if not found:
        print("WARNING! Destination post not found: "+link_src['id']+ "; url: "+link_src['url'])



print("end (replace_urls)")