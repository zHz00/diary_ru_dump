from markdownify import markdownify as markdownify
from os import getcwd, path
from os import walk
from os import listdir

from pathlib import Path
import re
from bs4 import BeautifulSoup
import settings as s
import init

def markdown_all_diary():
    print ("Stage 3 of 6: Creating markdown files from HTML...")
    file_list=listdir(s.dump_folder)

    file_list_out=file_list.copy()

    found=0
    for file in file_list:
        test=file.strip()
        if not(test.endswith(".htm")):
            file_list_out.remove(file)
        else:
            found+=1
        print(f"Found {found} posts...",end='\r')

    #сначала пробежимся по всем постам и создадим файлы, соответствующие тегам

    print("\nCreating tags list...")

    renamed_count=0
    tag_count=0

    for post in file_list_out:
        post_trim=s.dump_folder+post.strip()
        post_meta=s.dump_folder+post[:-4]+".txt"
        print(f"Found {tag_count} tags. Processing:"+post_trim,end="\r")
        f_meta=open(post_meta,"r",encoding=s.post_encoding)
        meta=f_meta.readlines()

        #сохраним теги

        tags=meta[5:]
        for tag in tags:
            if len(tag.strip())==0:#у нас последняя строчка пустая. ну и на случай если другие пустые будут
                continue
            tag_name=s.base_folder+s.tags_folder+re.sub(r'[\\/*?:"<>|]',"",tag.strip())+".md"
            test_path=Path(tag_name)
            if not test_path.is_file():
                tag_file=open(tag_name,"w",encoding=s.post_encoding)
                tag_file.write("#Теги")
                tag_file.close()
                tag_count+=1

    posts_list={}
    pics=[]
    links=[]
    ids=[]



    #ещё раз пробегаемся по всем постам, но уже по вопросам содержимого

    print("\nConverting posts...")

    file_list_len=len(file_list_out)
    n=0
    for post in file_list_out:
        percentage=int(n/file_list_len*100)
        print(f"[{percentage}%] {n} of {file_list_len} done...",end="\r")
        n+=1
        post_trim=post.strip()
        post_meta=post[:-4]+".txt"
        f_meta=open(s.dump_folder+post_meta,encoding=s.post_encoding)
        meta=f_meta.readlines()

        #сохраним содержимое

        out_name_file_base=re.sub(r'[\\/*?:"<>|]',"",meta[4]).strip()
        if len(out_name_file_base)==0:
            out_name_file_base="[NOT PRINTABLE]"
        out_name_file=out_name_file_base
        out_name=s.base_folder+out_name_file+".md"
        out_name_as_tag=s.base_folder+s.tags_folder+out_name_file+".md"
        test_path=Path(out_name)
        test_path_as_tag=Path(out_name_as_tag)
        append_num=0
        while test_path.is_file() or test_path_as_tag.is_file():
            print("File "+out_name+" exists! Renaming...")
            out_name_file=out_name_file_base+"["+str(append_num)+"]"
            out_name=s.base_folder+out_name_file+".md"
            out_name_as_tag=s.base_folder+s.tags_folder+out_name_file+".md"
            test_path=Path(out_name)
            test_path_as_tag=Path(out_name_as_tag)
            append_num+=1
            renamed_count+=1

        #имя файла готово, теперь надо его сохранить в словарь

        posts_list[meta[0].strip()]=out_name_file


        f=open(s.dump_folder+post_trim,encoding=s.post_encoding,errors="ignore")
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
            link_is_pic=False
            if re.search(r'[\[\]\^\#\|]',link.contents[0]):
                print(f"Warning! \"a\" tag has forbidden characters: {link.contents}")
            for test_str in s.cross_link_checking:
                if link['href'].find(test_str)!=-1:
                    link_is_cross_link=True
            for test_str in s.pic_checking:
                if link['href'].strip().lower().endswith(test_str)!=False and link.find("img")==None:
                    link_is_pic=True
            #воркэраунд для ситуации, когда имя файла упоминается как аргумент к запросу в гугл 
            # (такой случай один, но нормализовать его в самом дневнике я не могу, поэтому делаю тут)
            for test_str in s.forbidden_pic_urls:
                if link['href'].strip().lower().find(test_str)!=-1:
                    link_is_pic=False
            if link_is_cross_link==False and link_is_pic==False:
                continue
            link1={}
            link1['id']=meta[0].strip()
            link1['name']=out_name_file
            link1['url']=link['href']
            links.append(link1)

        


        #линуксовые концы строк т.к. обсидиан всё равно их заменит
        f_out=open(out_name,"w",encoding=s.post_encoding,errors="ignore",newline='\n')
        f_out.write(markdownify(contents).strip())
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

    print(f"\nend (markdown). All={len(file_list_out)}, renamed={renamed_count}, tags={tag_count}")

if __name__=="__main__":
    init.create_folders()
    init.reset_vault()
    markdown_all_diary()
