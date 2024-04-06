import requests
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urlparse
from pathlib import Path
import logging as l
import tqdm

import settings as s
import download_pics
import init
import db

def post_replace(file_name: str,str_from: str,str_to: str) -> None:
    post_r=open(file_name,"r",encoding=s.post_encoding)
    post_contents=post_r.read()
    post_r.close()
    post_contents=post_contents.replace(str_from,str_to)

    post_w=open(file_name,"w",encoding=s.post_encoding,newline='\n')
    post_w.write(post_contents)
    post_w.close()

def strip_post_id(url: str) -> str:
    for link_mark in s.link_marks:
        id_begin_raw=url.lower().find(link_mark.lower())
        if(id_begin_raw==-1):
            continue
        id_begin=id_begin_raw+len(link_mark)
        id_end=url.find("_",id_begin)
        if id_end==-1:
            id_end=url.find(".",id_begin)#без заголовка, поэтому нижнего подчёркивания нет
        return url[id_begin:id_end]
    return "-1"

@init.log_call
def replace_urls() -> None:

    print("Stage 5 of 7: Replacing cross links...")
    print("Reading link lists...",end="")

    n=0

    #DB
    db.connect()
    if s.download_pics==True:
        pics_list_db=db.get_pics_list_dict()
    else:
        pics_list_db=[]

    links_list_db=db.get_links_list_dict()



    for pic in pics_list_db:
        pic_url=pic['URL']
        pic_name=os.path.basename(urlparse(pic_url.strip()).path).strip()
        post_name=pic['POST_FNAME']

        res=urlparse(pic_url)#проверим, что у нас нормальный урл
        if(len(res.path)>0):
            post_replace(s.base_folder+post_name+".md",'('+pic_url+')','('+s.pics_folder+download_pics.check_length(pic_name)+')')
        else:
            l.info("warning! empty pic name! ["+pic_url+"], post: "+post_name)

    links=[]
    link={}
    not_found=[]

    #прочтём список ссылок

    print("Processing links...")
    for link in tqdm.tqdm(links_list_db,ascii=True):

        links_list_len=len(links_list_db)
        n+=1

        link_is_pic=False
        for test_str in s.pic_checking:
            if link['SRC_URL'].strip().lower().endswith(test_str.lower())!=False:
                link_is_pic=True
        if link_is_pic and s.download_pics==True:
            base_name=os.path.basename(urlparse(link['SRC_URL'].strip()).path).strip()
            link_dest=s.pics_folder+download_pics.check_length(base_name)
            l.info(f"Replacing {link['SRC_URL']} to {link_dest}")
            post_replace(s.base_folder+link["SRC_POST_FNAME"]+".md",link['SRC_URL'],link_dest.replace(" ","%20"))        
        else:
            #обрабатываем перекрёстные ссылки
            if link["SRC_POST_FNAME"]=="Советы по Pixel Dungeon":
                post_name=post_name

            if link['SRC_DEST_POST_ID']!=-1 and link['DEST_POST_FNAME'] is not None:
                l.info(f"Replacing {link['SRC_URL']} to {link['DEST_POST_FNAME']}")
                res=urlparse(link['SRC_URL'])
                if res.fragment.isdigit():
                    l.info("Special handling of internal comment link! SRC_URL="+link['SRC_URL']+", DEST_POST_FNAME="+link['DEST_POST_FNAME'])
                    link['DEST_POST_FNAME']+="#^c"+res.fragment
                    l.info("Resulting dest:"+link['DEST_POST_FNAME'])
                if re.search(r'[\[\]\^\#\|]',link['DEST_POST_FNAME']):
                    warning=f"Attention! Special character in dest name! {link['DEST_POST_FNAME']}"
                    l.info(warning)
                    not_found.append(warning)
                    post_replace(s.base_folder+link["SRC_POST_FNAME"]+".md",'('+link['SRC_URL']+')','('+(link['DEST_POST_FNAME'].replace(" ","%20"))+')')
                    #post_replace(s.base_folder+link_src["name"]+".md",link_src['url'],("[["+link_dest['name'].replace(" ","%20")+"\|"+link_dest['name'].replace(" ","%20")+"]]"))
                else:
                    post_replace(s.base_folder+link["SRC_POST_FNAME"]+".md",'('+link['SRC_URL']+')','('+(link['DEST_POST_FNAME'].replace(" ","%20"))+')')

            if link['SRC_DEST_POST_ID']!=-1 and link['DEST_POST_FNAME'] is None:#если -1, то там обычный урл без номера, конечно он не будет найден
                warning="WARNING! Destination post not found: "+str(link['SRC_DEST_POST_ID'])+ "; url: "+link['SRC_URL']
                l.info(warning)
                not_found.append(warning)

    db.close()

if __name__=="__main__":
    init.create_folders()
    replace_urls()