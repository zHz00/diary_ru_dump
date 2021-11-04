from markdownify import markdownify as markdownify
from os import getcwd, path
from os import walk
from os import listdir

from pathlib import Path
import re
from bs4 import BeautifulSoup
import settings as s

file_list=listdir(s.dump_folder)

file_list_out=file_list.copy()

for i in file_list:
    test=i.strip()
    print("testing: "+test)
    if not(test.endswith(".htm")):
        print("removing: "+i)
        file_list_out.remove(i)
    else:
        print("levaing: "+i)

print(f"source list: (len: {len(file_list)})")
print(file_list)

print(f"final list: {len(file_list_out)})")
print(file_list_out)

for i in file_list_out:
    i_trim=s.dump_folder+i.strip()
    i_meta=s.dump_folder+i[:-4]+".txt"
    print("Processing:"+i_trim)
    f_meta=open(i_meta,"r",encoding=s.post_encoding)
    meta=f_meta.readlines()

    #сохраним теги

    tags_raw=meta[5].split()
    tags=[]
    for tag in tags_raw:
        #специальная обработка для тега "Из закромов Родины"
        if (tag[0].islower() and len(tags)>0) or(tag=="Родины"):
            tags[-1]=tags[-1]+" "+tag
        else:
            tags.append(tag)
    for tag in tags:
        tag_name=s.base_folder+re.sub(r'[\\/*?:"<>|]',"",tag.strip())+".md"
        test_path=Path(tag_name)
        if not test_path.is_file():
            tag_file=open(tag_name,"w",encoding=s.post_encoding)
            tag_file.write("#Теги")
            tag_file.close()

posts_list={}
pics=[]
links=[]
ids=[]

for i in file_list_out:
    i_trim=i.strip()
    i_meta=i[:-4]+".txt"
    #print("Processing:"+i_trim)
    f_meta=open(s.dump_folder+i_meta,encoding=s.post_encoding)
    meta=f_meta.readlines()

    #сохраним содержимое

    out_name_file_base=re.sub(r'[\\/*?:"<>|]',"",meta[4]).strip()
    out_name_file=out_name_file_base
    out_name_folder=s.base_folder
    out_name=out_name_folder+out_name_file+".md"
    test_path=Path(out_name)
    append_num=0
    while test_path.is_file():
        print("File "+out_name+" exists! Renaming...")
        out_name_file=out_name_file_base+"["+str(append_num)+"]"
        out_name=out_name_folder+out_name_file+".md"
        test_path=Path(out_name)
        append_num+=1

    #имя файла готово, теперь надо его сохранить в словарь

    posts_list[meta[0].strip()]=out_name_file


    f=open(s.dump_folder+i_trim,encoding=s.post_encoding,errors="ignore")
    contents=f.read().replace("\n","").replace("\r","")
    
    #добываем ссылки и картинки
    bs=BeautifulSoup(contents,"html.parser")
    for pic in bs.find_all("img"):
        pic1={}
        pic1['id']=meta[0].strip()
        pic1['name']=out_name_file
        pic1['url']=pic['src']
        pics.append(pic1)

    for link in bs.find_all("a"):
        if not link.has_attr("href"):
            continue
        link_is_cross_link=False
        for test_str in s.cross_link_checking:
            if link['href'].find(test_str)!=-1:
                link_is_cross_link=True
        if link_is_cross_link==False:
            continue
        link1={}
        link1['id']=meta[0].strip()
        link1['name']=out_name_file
        link1['url']=link['href']
        links.append(link1)

    


    f_out=open(out_name,"w",encoding=s.post_encoding,errors="ignore")
    #специальная обработка для тегов со слешем
    f_out.write(markdownify(contents).strip().replace("[[Манга/Комиксы]]","[[МангаКомиксы]]").replace("[[Кино/Мультфильмы]]","[[КиноМультфильмы]]"))
    f_out.close()
    f.close()

#создадим список ссылок и список картинок

links_file=open(s.base_folder+s.links_file,"w",encoding=s.links_file_encoding)
for link in links:
    links_file.write(link["id"]+"\n")
    links_file.write(link["name"]+"\n")
    links_file.write(link["url"]+"\n")
links_file.close()

pics_file=open(s.base_folder+s.pics_file,"w",encoding=s.pics_file_encoding)
for pic in pics:
    pics_file.write(pic["id"]+"\n")
    pics_file.write(pic["name"]+"\n")
    pics_file.write(pic["url"]+"\n")
pics_file.close()

print("end (markdown)")