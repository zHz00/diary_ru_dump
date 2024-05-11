import markdownify
import time
import tqdm
import logging as l
from pathlib import Path
import re
from bs4 import BeautifulSoup

import settings as s
import init
import db
import replace_urls
from create_indexes import convert_tag_to_safe

times_md=[]

def remove_backslashes_in_code(contents:str,post_id:int)->str:
    code_markers=[]
    pair=[]
    for i,m in enumerate(re.finditer("```",contents)):
        if i%2==0:
            pair=[m.start(0)]
        else:
            pair.append(m.start(0))
            code_markers.append(pair)
    if len(pair)==1:
        l.info("Warning! odd code markers count, post id %d",post_id)
    #print(code_markers)
    if len(code_markers)==0:
        return contents
    contents_new=contents[0:code_markers[0][0]]
    for i in range(len(code_markers)):
        if i!=0:
            contents_new+=contents[code_markers[i-1][1]:code_markers[i][0]]
        contents_new+=contents[code_markers[i][0]:code_markers[i][1]].replace("\_","_").replace("\*","*")
    contents_new+=contents[code_markers[-1][1]:]
    #print(contents_new)
    return contents_new
    

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
            out_page.find("body").append(BeautifulSoup("<div>[["+re.sub(r'[\\/*?:"<>|]',"",tag).strip()+"]]</div><br />", 'lxml'))
        else:
            out_page.find("body").append(BeautifulSoup("<div>#"+re.sub(r'[\\/*?:"<>|]',"",tag).replace(" ","_").replace("-","_").strip()+"</div><br />", 'lxml'))
    add_times(times_md)#7
    if s.diary_url_mode!=s.dum.one_post:
        out_page.find("body").append(BeautifulSoup("ID: p"+str(post_id)+"<br />", 'lxml'))

    #будем добавлять комментарии

    if s.download_comments==True and s.diary_url_mode!=s.dum.one_post:
        comments_header=BeautifulSoup("<h2></h2>", 'lxml')
        comments_n=db.get_comments_downloaded(post_id)
        if comments_n!=0:
            comments_header.find("h2").string=f"Комментарии: {db.get_comments_downloaded(post_id)}"
        else:
            comments_header.find("h2").string="(Комментариев нет)"
        out_page.find("body").append(comments_header)
        out_page.find("body").append(BeautifulSoup("<br />", 'lxml'))
        comments_list=db.get_comments_list(post_id,deleted=False)
        c_len=len(comments_list)
        for idx,c_id in enumerate(comments_list):
            c_date,c_time=db.get_comment_date_time(c_id)
            c_author=db.get_comment_author(c_id)
            c_contents=db.get_comment_contents(c_id).replace("</span>  </div>","</span>  </div><br>").replace("</code>","</code><br>").replace('<div align="center">   <a href=','<div align="center"><br><a href=')
            out_page.find("body").append(BeautifulSoup("<hr /><table><tr><th>        #        </th><th>             Дата             </th><th>                    Автор                    </th><th>          ID          </th></tr><tr><td>("+str(idx+1)+"/"+str(c_len)+")</td><td>"+c_date+", "+c_time+"</td><td>"+c_author+"</td><td>c"+str(c_id)+"</td></tr></table><br />"+c_contents.strip()+" ^c"+str(c_id), 'lxml'))


    contents=str(out_page).replace("\n","").replace("\r","").replace("</br>","<br/>").replace("<br>","<br/>")
    contents=contents.replace("<tbody>","").replace("</tbody>","")
    return contents

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


@init.log_call
def markdown_all_diary(reset: bool,post_id:int=0) -> None:
    global times_md

    times_md=[]
    times=[]
    add_times(times)#0
    print ("Stage 3 of 7: Creating markdown files from HTML...")
    if(reset==True):
        if s.diary_url_mode==s.dum.one_post:
            init.reset_vault(s.dump_folder+s.temp_md_folder)
        else:
            init.reset_vault(s.base_folder)
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
    #на самом деле это сейчас уже не нужно, т.к. изначально эти файлы служили для поиска тегов при разметке
    #но сейчас я использую БД для хранения списка тегов, так что зачем мне этот набор? надо подумать

    print("\nCreating tags list...")
    renamed_count=0
    #DB
    tags_db=db.get_tags_list()
    for tag in tqdm.tqdm(tags_db,ascii=True):
        tag_name=s.base_folder+s.tags_folder+convert_tag_to_safe(tag)+".md"
        test_path=Path(tag_name)
        if not test_path.is_file():
            tag_file=open(tag_name,"w",encoding=s.post_encoding)
            tag_file.write("#Теги")
            tag_file.close()
    tag_count_db=len(tags_db)


    posts_list={}

    #ещё раз пробегаемся по всем постам, но уже по вопросам содержимого

    print("\nConverting posts...")
    #DB
    add_times(times)#6
    times_loop=[]
    n=0

    if s.diary_url_mode==s.dum.one_post:
        folder=s.dump_folder+s.temp_md_folder
    else:
        folder=s.base_folder
   
    for post_id in tqdm.tqdm(file_list_db,ascii=True):
        #if post_id!=221557637:
        #    continue
        add_times(times_loop)
        times_md=[]
        add_times(times_md)#0
        add_times(times_md)#1
        n+=1
        #сохраним содержимое

        out_name_file_base=re.sub(r'[\\/*?:"<>|]',"",db.get_post_title(post_id)).strip()
        while len(out_name_file_base)>0 and out_name_file_base[0]==".":#второе условие не будет вычисляться, если первое ложно
            out_name_file_base=out_name_file_base[1:]#убираем все стартовые точки, т.к. обсидиан неадекватно с ними работает
        if len(out_name_file_base)==0:
            out_name_file_base="[NOT PRINTABLE]"
        out_name_file=out_name_file_base
        out_name=folder+out_name_file+".md"
        out_name_as_tag=folder+s.tags_folder+out_name_file+".md"
        test_path=Path(out_name)
        test_path_as_tag=Path(out_name_as_tag)
        append_num=0
        renamed=False
        while test_path.is_file() or test_path_as_tag.is_file():
            renamed=True
            out_name_file=out_name_file_base+"["+str(append_num)+"]"
            out_name=folder+out_name_file+".md"
            out_name_as_tag=folder+s.tags_folder+out_name_file+".md"
            test_path=Path(out_name)
            test_path_as_tag=Path(out_name_as_tag)
            append_num+=1
            renamed_count+=1
        if renamed:
            l.info(f"File {out_name_file_base}.md exists! Renamed to: {out_name_file}")
            renamed=False
        #имя файла готово, теперь надо его сохранить в словарь

        posts_list[post_id]=out_name_file
        add_times(times_md)#2
        contents=get_post_as_html(post_id)
        #contents=contents.replace("&gt;","\\&gt;")
        #contents=contents.replace("&lt;","\\&lt;")
        #добываем ссылки и картинки
        add_times(times_md)#8
        bs=BeautifulSoup(contents,"lxml")
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
                l.info(f"Warning! \"a\" tag has forbidden characters: {link.contents}")
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
            db.add_link(post_id,out_name_file,int(replace_urls.strip_post_id(link['href'])),link['href'])
        add_times(times_md)#10
        #линуксовые концы строк т.к. обсидиан всё равно их заменит
        f_out=open(out_name,"w",encoding=s.post_encoding,errors="ignore",newline='\n')
        contents=contents.replace("&lt;br&gt;","\n")
        if s.diary_url_mode==s.dum.one_post:
            out_contents=markdownify.markdownify(contents,strong_em_symbol=markdownify.UNDERSCORE,escape_asterisks=True,keep_inline_images_in=["tr","td","th","a"]).strip()
        else:
            out_contents=markdownify.markdownify(contents,keep_inline_images_in=["tr","td","th","a"]).strip()
        out_contents=remove_backslashes_in_code(out_contents,post_id)
            #out_contents=normalize_to_prev_ver(out_contents)
            #поскольку я собираюсь докачивать комментарии, все файлы всё равно будут изменены и репозиторий с хранилищем обсидиана будет залит заново
            #так что более нет необходимости хранить совместимость
        #макрдаун этого не умеет, поэтому вручную сделаем зачёркивание!
        #out_contents=out_contents.replace("~~","~")
        add_times(times_md)#11
        out_len=len(out_contents)
        f_out.write(out_contents)
        f_out.close()
        add_times(times_md)#12


    print(f"\nend (markdown). All={len(file_list_db)}, renamed={renamed_count}, tags={tag_count_db}")
    if s.diary_url_mode==s.dum.one_post:
        return out_name,out_len
    else:
        return 0

if __name__=="__main__":
    init.create_folders()
    markdown_all_diary(reset=True)
