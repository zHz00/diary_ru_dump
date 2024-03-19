import markdownify
from os import getcwd, path
from os import walk
from os import listdir

from pathlib import Path
import re
from bs4 import BeautifulSoup

import settings as s
import init
import db
import time
import replace_urls

times_md=[]

def get_post_as_html(post_id: int):
    global times_md
    fish="<html><title></title><body></body></html>"
    out_page=BeautifulSoup(fish,"lxml")

    title_header=BeautifulSoup("<h1></h1>", 'lxml')
    title_header.find("h1").string=db.get_post_title(post_id)
    if s.diary_url_mode!=s.dum.one_post:
        out_page.find("body").append(title_header)
        out_page.find("body").append(BeautifulSoup("<br />", 'lxml'))
    (post_date,post_time)=db.get_post_date_time(post_id)
    out_page.find("body").append(post_date+", "+post_time)
    out_page.find("body").append(BeautifulSoup("<br />", 'lxml'))
    add_times(times_md)#3

    out_page.find("body").append(BeautifulSoup(db.get_post_contents(post_id),'lxml'))
    out_page.find("body").append(BeautifulSoup("<br />", 'lxml'))
    add_times(times_md)#4
    #другие метаданные тоже надо внести
    title_url=title_header.new_tag("a",href=db.get_post_url(post_id))
    
    if s.diary_url_mode!=s.dum.one_post:
        title_url.string=db.get_post_url(post_id)
        out_page.find("body").append(title_url)
        out_page.find("body").append(BeautifulSoup("<br />", 'lxml'))
        out_page.find("body").append(BeautifulSoup("<br />Теги:<br />", 'lxml'))
    else:
        title_url.string=s.diary_url_pretty+"p"+str(post_id)+".htm"
        out_page.find("body").append(title_url)
        out_page.find("body").append(BeautifulSoup("<br /><br />", 'lxml'))
    add_times(times_md)#5
    tags_db=db.get_post_tags(post_id)
    add_times(times_md)#6
    for tag in tags_db:
        if s.diary_url_mode!=s.dum.one_post:
            out_page.find("body").append(BeautifulSoup("[["+re.sub(r'[\\/*?:"<>|]',"",tag).strip()+"]] <br />", 'lxml'))
        else:
            out_page.find("body").append(BeautifulSoup("<div>#"+re.sub(r'[\\/*?:"<>|]',"",tag).replace(" ","_").replace("-","_").strip()+"</div><br />", 'lxml'))
    add_times(times_md)#7
    if s.diary_url_mode!=s.dum.one_post:
        out_page.find("body").append(BeautifulSoup("ID: p"+str(post_id)+"<br />", 'lxml'))

    contents=str(out_page).replace("\n","").replace("\r","").replace("</br>","<br/>").replace("<br>","<br/>")
    contents=contents.replace("<tbody>","").replace("</tbody>","")
    return contents

def normalize_to_prev_ver(text: str) -> str:
    #после перехода на lxml парсер по неясной причине мд-файлы выглядят немного не так, как должны
    #чтобы в ГИТе сравнение с предыдущими версиями работало нормально, надо кое-что добавить, а кое-что убрать. этим и займёмся
    text_lines=text.split("\n")
    text_lines[1]=text_lines[1]+"="
    #print("3:["+text_lines[3]+"]")
    text_lines[3]=text_lines[3]+" "
    #print("4:["+text_lines[4]+"]")
    text_lines[4]=" "+text_lines[4]+" "
    text_lines[5]=" "+text_lines[5]
    tags_line=0
    for x in range(len(text_lines)-1,-1,-1):
        if text_lines[x].find("Теги:")!=-1:
            tags_line=x
            break
    text_lines[tags_line-3]="  "+text_lines[tags_line-3]
    text_lines[tags_line-2]=" "+text_lines[tags_line-2]+" "
    text_lines[tags_line-1]=" "+text_lines[tags_line-1]
    text_lines[tags_line]=" "+text_lines[tags_line]+" "
    for x in range(tags_line,len(text_lines)-1):
        if len(text_lines[x])>0 and text_lines[x][0]=='[':#строчка с тегом
            text_lines[x]=" "+text_lines[x]
    #теперь надо убрать пустые строки в конце
    for x in range(len(text_lines)-1,tags_line,-1):
        if len(text_lines[x])==0:
            del text_lines[x]
    text_lines[-1]=" "+text_lines[-1]#ID:
    return "\n".join(text_lines)

def remove_unwanted_escape(mk_str: str) -> str:
    #надо кое-что сделать, а именно убрать все эскейпы созданные markdownify внутри блоков кода
    pre_indexes=[pre.start() for pre in re.finditer('```', mk_str)]
    pre_index_sets=[[]]
    for idx in pre_indexes:
        if len(pre_index_sets[-1])>=2:
            pre_index_sets.append([])
        pre_index_sets[-1].append(idx)
    chunk_sets=[[0]]
    for set in pre_index_sets:
        if len(set)!=2:
            return mk_str#не собрали ничего, так что сразу возвращаем как есть
        chunk_sets[-1].append(set[0])
        chunk_sets[-1].append(set[1])
        chunk_sets.append([set[1]])
    chunk_sets[-1].append([len(mk_str),len(mk_str)])
    mk_str_res=""
    for chunk in chunk_sets:
        mk_str_res+mk_str[:chunk[0]]
        mk_str_res+=mk_str[chunk[1]:chunk[2]].replace("\\","")
    return mk_str_res

def add_times(list):
    cur_time=time.time()
    if(len(list)>0):
        last_time=list[-1][0]
    else:
        last_time=cur_time
    list.append((cur_time,cur_time-last_time))



def markdown_all_diary(reset: bool,post_id:int=0) -> None:
    global times_md

    times_md=[]
    times=[]
    add_times(times)#0
    print ("Stage 2 of 6: Creating markdown files from HTML...")
    if(reset==True):
        init.reset_vault()
    add_times(times)#1

    db.connect()
    add_times(times)#2
        
    if(post_id==0):
        file_list_db=db.get_posts_list()
    else:
        file_list_db=[post_id]


    file_list_len_db=len(file_list_db)
    print(f"\n[DB]Found {file_list_len_db} posts...")

    #сначала пробежимся по всем постам и создадим файлы, соответствующие тегам

    print("\nCreating tags list...")
    renamed_count=0
    #DB
    tags_db=db.get_tags_list()
    for tag in tags_db:
        tag_name=s.base_folder_db+s.tags_folder+re.sub(r'[\\/*?:"<>|]',"",tag.strip())+".md"
        test_path=Path(tag_name)
        if not test_path.is_file():
            tag_file=open(tag_name,"w",encoding=s.post_encoding)
            tag_file.write("#Теги")
            tag_file.close()
    tag_count_db=len(tags_db)


    posts_list={}
    pics=[]
    links=[]
    ids=[]



    #ещё раз пробегаемся по всем постам, но уже по вопросам содержимого

    print("\nConverting posts...")
    #DB
    add_times(times)#6
    times_loop=[]
    n=0
   
    for post_id in file_list_db:
        add_times(times_loop)
        times_md=[]
        add_times(times_md)#0
        add_times(times_md)#1
        percentage=int(n/file_list_len_db*100)
        print(f"[{percentage}%] {n} of {file_list_len_db} done...",end="\r")
        n+=1
        #сохраним содержимое

        out_name_file_base=re.sub(r'[\\/*?:"<>|]',"",db.get_post_title(post_id)).strip()
        if len(out_name_file_base)==0:
            out_name_file_base="[NOT PRINTABLE]"
        out_name_file=out_name_file_base
        out_name=s.base_folder_db+out_name_file+".md"
        out_name_as_tag=s.base_folder_db+s.tags_folder+out_name_file+".md"
        test_path=Path(out_name)
        test_path_as_tag=Path(out_name_as_tag)
        append_num=0
        while test_path.is_file() or test_path_as_tag.is_file():
            print(f"[{percentage}%]File "+out_name+" exists! Renaming...")
            out_name_file=out_name_file_base+"["+str(append_num)+"]"
            out_name=s.base_folder_db+out_name_file+".md"
            out_name_as_tag=s.base_folder_db+s.tags_folder+out_name_file+".md"
            test_path=Path(out_name)
            test_path_as_tag=Path(out_name_as_tag)
            append_num+=1
            renamed_count+=1
        #имя файла готово, теперь надо его сохранить в словарь

        posts_list[post_id]=out_name_file
        add_times(times_md)#2
        contents=get_post_as_html(post_id)
        #contents=contents.replace("&gt;","\\&gt;")
        #contents=contents.replace("&lt;","\\&lt;")
        #добываем ссылки и картинки
        add_times(times_md)#8
        bs=BeautifulSoup(contents,"html.parser")
        for pic in bs.find_all("img"):
            if pic.parent.name=="pre" or pic.parent.parent.name=="pre":
                continue
            db.add_pic(post_id,out_name_file,pic['src'])
        add_times(times_md)#9
        for link in bs.find_all("a"):
            if not link.has_attr("href"):
                continue
            link_is_cross_link=False
            link_is_pic=False
            if re.search(r'[\[\]\^\#\|]',link.contents[0]):
                print(f"Warning! \"a\" tag has forbidden characters: {link.contents}")
            for test_str in s.cross_link_checking:
                if link['href'].lower().find(test_str.lower())!=-1:
                    link_is_cross_link=True
            for test_str in s.pic_checking:
                if link['href'].strip().lower().endswith(test_str.lower())!=False and link.find("img")==None:
                    link_is_pic=True
            #воркэраунд для ситуации, когда имя файла упоминается как аргумент к запросу в гугл 
            # (такой случай один, но нормализовать его в самом дневнике я не могу, поэтому делаю тут)
            for test_str in s.forbidden_pic_urls:
                if link['href'].strip().lower().find(test_str.lower())!=-1:
                    link_is_pic=False
            if link_is_cross_link==False and link_is_pic==False:
                continue
            db.add_link(post_id,out_name_file,replace_urls.strip_post_id(link['href']),link['href'])
        add_times(times_md)#10
        #линуксовые концы строк т.к. обсидиан всё равно их заменит
        f_out=open(out_name,"w",encoding=s.post_encoding,errors="ignore",newline='\n')
        if s.diary_url_mode==s.dum.one_post:
            out_contents=markdownify.markdownify(contents,strong_em_symbol=markdownify.UNDERSCORE,escape_asterisks=True).strip()
        else:
            out_contents=markdownify.markdownify(contents).strip()
            out_contents=normalize_to_prev_ver(out_contents)
        #макрдаун этого не умеет, поэтому вручную сделаем зачёркивание!
        #out_contents=out_contents.replace("~~","~")
        add_times(times_md)#11
        out_len=len(out_contents)
        f_out.write(out_contents)
        f_out.close()
        add_times(times_md)#12
        pass
    


    print(f"\nend (markdown). All={len(file_list_db)}, renamed={renamed_count}, tags={tag_count_db}")
    if s.diary_url_mode==s.dum.one_post:
        return out_name,out_len
    else:
        return 0

if __name__=="__main__":
    init.create_folders()
    markdown_all_diary(reset=True)
