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

def post_replace(file_name,str_from,str_to):
    post_r=open(file_name,"r",encoding=s.post_encoding)
    post_contents=post_r.read()
    post_r.close()
    post_contents=post_contents.replace(str_from,str_to)

    post_w=open(file_name,"w",encoding=s.post_encoding,newline='\n')
    post_w.write(post_contents)
    post_w.close()


if s.download_pics==True:
    pics_list_file=open(s.base_folder+s.pics_file,"r",encoding=s.pics_file_encoding)
    pics_list_text=pics_list_file.readlines()
else:
    pics_list_text=[]

links_list_file=open(s.base_folder+s.links_file,"r",encoding=s.links_file_encoding)
links_list_text=links_list_file.readlines()

def strip_post_id(url):
    for link_mark in s.link_marks:
        id_begin_raw=url.find(link_mark)
        if(id_begin_raw==-1):
            continue
        id_begin=id_begin_raw+len(link_mark)
        id_end=url.find("_",id_begin)
        if id_end==-1:
            id_end=url.find(".",id_begin)#без заголовка, поэтому нижнего подчёркивания нет
        return url[id_begin:id_end]
    return "-1"

phase=0

#первую строчку пропускаем, там не то
#вторую строчку запоминаем
#третью используем

for line in pics_list_text:
    phase+=1
    if phase%3==1:
        continue
    if phase%3==2:
        post_name=line.strip()
        continue
    #теперь у нас есть урл
    pic_url=line.strip()
    pic_name=os.path.basename(urlparse(line.strip()).path).strip()

    post_replace(s.base_folder+post_name+".md",pic_url,s.pics_folder+pic_name)

links=[]
link={}
not_found=[]

#прочтём список ссылок

phase=0

for line in links_list_text:
    phase+=1
    if phase%3==1:
        link['id']=line.strip()
    if phase%3==2:
        link['name']=line.strip()
    if phase%3==0:
        link['url']=line.strip()
        links.append(link)
        link={}

for link_src in links:

    id_dest=strip_post_id(link_src['url'])
    if id_dest==link_src['id']:
        continue
    found=False
    link_is_pic=False
    for test_str in s.pic_checking:
        if link_src['url'].strip().lower().endswith(test_str)!=False:
            link_is_pic=True
    if link_is_pic and s.download_pics==True:
        link_dest=s.pics_folder+os.path.basename(urlparse(link_src['url'].strip()).path).strip()
        print(f"Replacing {link_src['url']} to {link_dest}")
        post_replace(s.base_folder+link_src["name"]+".md",link_src['url'],link_dest.replace(" ","%20"))        
    else:
        #обрабатываем перекрёстные ссылки
        for link_dest in links:
            if link_dest['id']==id_dest:
                #нашли целевой файл
                found=True
                print(f"Replacing {link_src['url']} to {link_dest['name']}")
                if re.search(r'[\[\]\^\#\|]',link_dest['name']):
                    warning=f"Attention! Special character in dest name! {link_dest['name']}"
                    print(warning)
                    not_found.append(warning)
                    post_replace(s.base_folder+link_src["name"]+".md",link_src['url'],(link_dest['name'].replace(" ","%20")))
                    #post_replace(s.base_folder+link_src["name"]+".md",link_src['url'],("[["+link_dest['name'].replace(" ","%20")+"\|"+link_dest['name'].replace(" ","%20")+"]]"))
                else:
                    post_replace(s.base_folder+link_src["name"]+".md",link_src['url'],(link_dest['name'].replace(" ","%20")))
                break
                #т.к. уже нашли дальше неча смотреть

        #а тут обрабатываем ссылки на изображения

        if not found:
            warning="WARNING! Destination post not found: "+link_src['id']+ "; url: "+link_src['url']
            not_found.append(warning)
            print(warning)


print("Absent links (one more time):")
for message in not_found:
    print(message)
print("End (replace_urls)")