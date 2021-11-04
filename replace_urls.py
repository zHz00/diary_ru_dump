import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urlparse
from pathlib import Path
import settings as s

def post_replace(file_name,str_from,str_to):
    post_r=open(file_name,"r",encoding=s.post_encoding)
    post_contents=post_r.read()
    post_r.close()
    post_contents=post_contents.replace(str_from,str_to)

    post_w=open(file_name,"w",encoding=s.post_encoding)
    post_w.write(post_contents)
    post_w.close()


pics_list_file=open(s.base_folder+s.pics_file,"r",encoding=s.pics_file_encoding)
pics_list_text=pics_list_file.readlines()

links_list_file=open(s.base_folder+s.links_file,"r",encoding=s.links_file_encoding)
links_list_text=links_list_file.readlines()

def strip_post_id(url):
    for link_mark in s.link_marks:
        id_begin_raw=url.find(link_mark)
        if(id_begin_raw==-1):
            continue
        id_begin=id_begin_raw+len(link_mark)
        return url[id_begin:id_begin+s.post_id_len]
    return "-1"

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

    post_replace(s.base_folder+post_name+".md",pic_url,s.pics_folder+pic_name)

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

    id_dest=strip_post_id(link_src['url'])
    if id_dest==link_src['id']:
        continue
    found=False
    for link_dest in links:
        if link_dest['id']==id_dest:
            #нашли целевой файл
            found=True
            print(f"Replacing {link_src['url']} to {link_dest['name']}")
            post_replace(s.base_folder+link_src["name"]+".md",link_src['url'],(link_dest['name'].replace(" ","%20")))
            break
            #т.к. уже нашли дальше неча смотреть
    if not found:
        print("WARNING! Destination post not found: "+link_src['id']+ "; url: "+link_src['url'])



print("End (replace_urls)")