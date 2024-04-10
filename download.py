#download diary

from cgi import test
import requests
import certifi
from bs4 import BeautifulSoup
import time
import re
from requests.sessions import RequestsCookieJar
from pathlib import Path
import tqdm
import typing
import logging as l

import init
import settings as s
import db


def convert_to_old_style(url: str) -> str:
    #новые ссылки типа имя.дайари.ру/ должны быть превращены в дайари.ру/~имя, чтобы совпадало со старыми дампами
    #приблизительно летом 22 года разработчики наконец сделали так, что для незалогиненных ссылки отображаются в новом формате. это создало проблемы
    #при сравнении дампов со старыми версиями гита
    #на входе: https://zhz00.diary.ru/pXXXX.htm
    #на выходе: https://diary.ru/~zHz00/pXXXX.htm
    cut_begin=8
    cut_end=url.find(".diary.ru/")
    uname=url[cut_begin:cut_end]
    out_str=url[:cut_begin]+url[cut_end+1:]
    out_str=out_str[:17]+"~"+uname+"/"+out_str[17:]
    return out_str
    

def remove_newlines_ex(bs4obj):
    for pre in bs4obj.find_all("pre"):
        if hasattr(pre,"string") and pre.string is not None:
            l.info("'pre' has inner string : ")
            l.info("S:"+pre.string)
            pre.string=pre.string.replace("\n","SUPERSECRETNEWLINE")
            l.info("end of replace")
        else:
            l.info(pre)
    return bs4obj.prettify().replace("\r","").replace("\n","").replace("SUPERSECRETNEWLINE","<br />")
    
PRE_START="<pre>"
PRE_END="</pre>"
"""def change_pre(html_txt):#функция ищет все теги pre и заменяет внутри них все угловые скобки на спец. последовательности
    pre_ranges_start=[]
    pre_ranges_end=[]
    idx=0
    print("Changing inside pres...")
    while(idx!=-1):
        idx=html_txt.find(PRE_START,idx+1)
        if(idx!=-1):
            print("Idx="+str(idx))
            pre_ranges_start.append(idx+len(PRE_START))
    idx=0
    while(idx!=-1):
        idx=html_txt.find(PRE_END,idx+1)
        if(idx!=-1):
            print("Idx="+str(idx))
            pre_ranges_end.append(idx)
    if(len(pre_ranges_start)!=len(pre_ranges_end)):
        print("Non-paired pre found. Skipping...")
        return html_txt
    for x in range(len(pre_ranges_start)):
        beg=pre_ranges_start[x]
        end=pre_ranges_end[x]
        print("PRE range:"+html_txt[beg:end])
        html_txt=html_txt[:beg]+html_txt[beg:end].replace("<","&lt;").replace(">","&gt;")+html_txt[end:]
        print("Result:"+html_txt[beg:end])
    print("Changing done.")
    return html_txt"""
    
def change_pre(html_txt, start=0):
    beg_outer=html_txt.find(PRE_START,start)
    l.info("beg_outer:"+str(beg_outer))
    if(beg_outer==-1):
        l.info("Done parsing...")
        return html_txt
    end_outer=html_txt.find(PRE_END,start)
    l.info("end_outer:"+str(end_outer))
    if(end_outer==-1):
        l.info("Error parsing 1...")
        return html_txt        
    beg=html_txt.find(">",beg_outer+len(PRE_START))+1#пропускаем тег textarea
    l.info("beg:"+str(beg))
    if(beg==-1):
        l.info("Error parsing 2...")
        return html_txt
    end=html_txt.rfind("<",beg,end_outer)#закрытие тоже пропускаем
    prl.infoint("end:"+str(end))
    if(end==-1):
        l.info("Error parsing 3...")
        return html_txt
    l.info("RANGE:"+str(beg)+","+str(end))
    l.info("STR:"+html_txt[beg:end])
    return change_pre(html_txt[:beg]+html_txt[beg:end].replace("<","&lt;").replace(">","&gt;")+html_txt[end:],end_outer+len(PRE_END))

def convert_date(date: str) -> str:
    month_convertor = {
        'января' : '01',
        'февраля' : '02',
        'марта' : '03',
        'апреля' : '04',
        'мая' : '05',
        'июня' : '06',
        'июля' : '07',
        'августа' : '08',
        'сентября' : '09',
        'октября' : '10',
        'ноября' : '11',
        'декабря' : '12',
    }
    date = date.split()
    return date[3] + '-' + month_convertor[date[2]] + '-' + date[1]

def convert_date_ru_to_iso(date:str)->str:
    return date[6:]+'-'+date[3:5]+'-'+date[0:2]

def get_cookies() -> None:
    cookies=RequestsCookieJar()
    for c_name,c_value in s.saved_cookies.items():
        cookie=requests.cookies.create_cookie(domain="diary.ru",name=c_name,value=c_value)
        cookies.set_cookie(cookie) 
    return cookies

@init.log_call
def find_last_page() -> int:
    if hasattr(find_last_page,"last_num_cached"):
        l.info(f"Last page already found: {find_last_page.last_num_cached}")
        print(f"Last page already found: {find_last_page.last_num_cached}")
        return find_last_page.last_num_cached

    l.info("Finding last page...")
    print("Finding last page...")
    page_url=s.diary_url
    print("Downloading "+page_url+"...")
    page = requests.get(page_url,cookies=get_cookies())
    page = BeautifulSoup(page.text, 'lxml')
    post_divs=page.find_all("div")
    for div in post_divs:
        if div.has_attr("class") and len(div["class"])>0 and div["class"][0]=="pagination":
            hrefs=div.find_all("a")
            for href in hrefs:
                last_num_idx=href["href"].rfind("=")
                if href.has_attr("href") and last_num_idx!=-1 and len(href["href"])>last_num_idx+1:
                    last_num=int(href["href"][last_num_idx+1:])
                    break
    l.info(f"Last page: {last_num}")
    print(f"Last page: {last_num}")
    find_last_page.last_num_cached=last_num
    return last_num
    
@init.log_call
def find_last_post() -> int:
    l.info("Finding last post...")
    print("Finding last post...")
    page_url=s.diary_url
    l.info("Downloading "+page_url+"...")
    print("Downloading "+page_url+"...")
    page = requests.get(page_url,cookies=get_cookies())
    page = BeautifulSoup(page.text, 'lxml')
    post_divs=page.find_all("div")
    for div in post_divs:
        if div.has_attr("class") and len(div["class"])>1 and div["class"][0]=="item" and div["class"][1]=="first":
            post_id=int((div["id"])[4:])
            l.info("Last post:"+str(post_id))
            print("Last post:"+str(post_id))
            return post_id
    l.info("no last post found")
    print("no last post found")
    return 0


def test_epigraph(epigraph: typing.Dict[str,bool],test_name: str) -> bool:
    if test_name in epigraph.keys():
        return True
    else:
        epigraph[test_name]=True
        return False

@init.log_call
def download(update: bool,auto_find: bool,post_id:int=0) -> None:
    db.connect()
    if s.diary_url_mode==s.dum.full and update==False:
        db.reset_posts()
    if(post_id==0 and s.diary_url_mode==s.dum.one_post):
        post_id=find_last_post()
        if post_id==0:
            return 0
    if(auto_find):
        last_page=find_last_page()
    else:
        last_page=s.start if s.start>s.stop else s.stop
    if(update):
        s.start=last_page+20
        s.stop=20
    else:
        s.start=20
        s.stop=last_page+20

    if s.diary_url_mode!=s.dum.newest_comments:
        print("Stage 1 of 7: Downloading posts...")
    else:
        print("Updating comments counters...")

    step=20

    if s.diary_url_mode==s.dum.full and s.start<=s.stop:
        step=20
    if s.diary_url_mode==s.dum.full and s.start>s.stop:
        step=-20

    if s.diary_url_mode==s.dum.newest_comments and s.start<=s.stop:
        step=20
    if s.diary_url_mode==s.dum.newest_comments and s.start>s.stop:
        step=-20

    if s.diary_url_mode==s.dum.by_tag and s.start<=s.stop:
        step=1
    if s.diary_url_mode==s.dum.by_tag and s.start>s.stop:
        step=-1

    if s.diary_url_mode==s.dum.one_post:
        s.start=0
        s.stop=1
        step=1

    saved_pages=0
    comments_n_changed=True
        
    for offset in range(s.start, s.stop, step):
        if s.diary_url_mode!=s.dum.one_post:
            if s.diary_url_mode==s.dum.newest_comments:
                page_url=s.diary_url_comments+str(offset)
            else:
                page_url=s.diary_url+str(offset)
        else:
            qmark_index=s.diary_url.find("?")
            page_url=s.diary_url[:qmark_index]+"/p"+str(post_id)+".htm"+s.diary_url[qmark_index:]
            l.info("Page url="+page_url)
            print("Page url="+page_url)
        if s.diary_url_mode==s.dum.from_file:
            page_url+=".html"
        l.info("Downloading "+page_url+"...")
        print("Downloading "+page_url+"...")
        if s.diary_url_mode!=s.dum.from_file:
            page = requests.get(page_url,cookies=get_cookies())

            if s.download_html==True:
                htmlfile_name=s.dump_folder+f"sheet{offset}.html"
                htmlfile=open(htmlfile_name,"w",encoding=s.post_encoding)
                htmlfile.write(page.text)
                htmlfile.close()

            page = BeautifulSoup(change_pre(page.text), 'lxml')
        else:
            page_file=open(page_url,"r",encoding=s.post_encoding)
            page=page_file.read()
            page_file.close()
            page=BeautifulSoup(page,'lxml')
            
        posts_titles=[]
        posts_links=[]
        posts_dates_s=[]
        posts_times_s=[]
        posts_contents=[]
        posts_comments_n=[]
        posts_tags=[]

        posts_ids=[]
        posts_dates=[]
        posts_times=[]

        #разбор данных на метаданные

        epigraph={}
        #нам надо пропустить все дивы эпиграфа
        posts_divs=page.find_all("div")
        for div in posts_divs:
            if div.has_attr("class") and len(div["class"])>0:
                class_name=div["class"][0]
                if len(div["class"])>1:
                    class_name_2nd=div["class"][1]
                else:
                    class_name_2nd=""
                #отладочный вывод, когда дайри-программист в очередной раз перепиливает разметку
                #id_name=div["id"] if div.has_attr("id") else "[none]"
                #print("Class:"+class_name+", id="+id_name)
                if class_name == "day-header":
                    posts_dates_s.append(div.span.contents[0])
                    posts_dates.append(convert_date(div.span.contents[0]))
                if class_name == "singlePost" and div.find("div")!=None and div.div.has_attr("class") and div.div["class"][0] == "countSecondDate":
                    posts_dates_s.append(div.div.span.contents[0])
                    posts_dates.append(convert_date(div.div.span.contents[0]))
                test_name="postTitle"
                if class_name == "post-header" or class_name == test_name:
                    #if test_epigraph(epigraph,test_name)==False:
                    #    continue
                    if len(posts_dates_s)!=len(posts_links)+1:#если для текущей записи не нашлось даты из-за двух записей в течение дня
                        posts_dates_s.append(posts_dates_s[-1])
                        posts_dates.append(posts_dates[-1])
                    #if div.has_attr("a"):
                    #    posts_links.append(div.a["href"])
                    #    id_begin=div.a["href"].find(s.link_marks[s.links_style])+len(s.link_marks[s.links_style])
                    #    posts_ids.append(div.a["href"][id_begin:div.a["href"].rfind(".")-1])
                    #else:
                        #закрытая запись. текста у нас нет, поэтому сохраняем только ИД записи
                        #обращаю внимания, что если запись доступна, но нет заголовка, то ссылка всё равно генерируется, поэтому ИД у нас есть
                    #    posts_links.append(div.parent)
                    posts_times_s.append(div.span.contents[0])
                    if div.find("a")!=None:
                        if len(div.a.contents)>0:
                            posts_titles.append(div.a.contents[0])
                        else:
                            posts_titles.append("(no title)")
                    else:
                        posts_titles.append("(closed)")
                test_name="postLinksBackg"
                if class_name == test_name and class_name_2nd!="prevnext":#старый дизайн
                    #prevnext это блок "предыдущая запись-следующая запись", он нас не интересует
                    #if test_epigraph(epigraph,test_name)==False:
                    #    continue
                    posts_links.append(convert_to_old_style(div.div.a["href"]))
                    id_begin=div.span.a["href"].lower().find(s.link_marks[s.links_style].lower())+len(s.link_marks[s.links_style])
                    id_end=div.span.a["href"].rfind("_")
                    if id_end==-1:
                        id_end=div.span.a["href"].rfind(".")#без заголовка, поэтому нижнего подчёркивания нет
                    posts_ids.append(div.span.a["href"][id_begin:id_end])
                    percentage=int(len(posts_ids)/(s.stop-s.start)*step*100)
                    l.info(f"[{percentage}%]Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
                    print(f"[{percentage}%]Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
                if class_name == "post-links":#новый дизайн
                    posts_links.append(convert_to_old_style(div.div.a["href"]))
                    id_begin=div.div.a["href"].lower().find(s.link_marks[s.links_style].lower())+len(s.link_marks[s.links_style])
                    id_end=div.div.a["href"].find("_",id_begin)
                    if id_end==-1:
                        id_end=div.a["href"].find(".",id_begin)#без заголовка, поэтому нижнего подчёркивания нет
                    posts_ids.append(div.div.a["href"][id_begin:id_end])
                    percentage=int(len(posts_ids)/abs(s.stop-s.start)*100)
                    l.info(f"[{percentage}%]Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
                    print(f"[{percentage}%]Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
                test_name="postInner"
                if class_name==test_name:
                    #if test_epigraph(epigraph,test_name)==False:
                    #   continue
                    posts_contents.append(remove_newlines_ex(div))#div.prettify().replace('\r', '').replace('\n', ''))
                if class_name == "post-inner":
                    posts_contents.append(remove_newlines_ex(div))
                test_name="postContent"
                if class_name == test_name:
                    #if test_epigraph(epigraph,test_name)==False:
                    #    continue
                    tags=[]
                    post_tags=[]
                    posts_ps=div.find_all("p")
                    for p in posts_ps:# тег <p>
                        if p.has_attr("class"):
                            if p["class"][0]=="tags":
                                tags=p.find_all("a")
                                for tag in tags:
                                    post_tags.append(tag.contents[0])
                    if len(post_tags)==0:#бывают посты без тегов. чтобы их отловить, мы ищем блок с тегами ТОЛЬКО внутри текущего дива. если его нет, ставим специальный тег, что тегов нет
                        post_tags.append("None")
                    posts_tags.append(post_tags)
                comments_n=0
                if class_name=="right" or class_name=="postLinksBackg":#как ни странно, это счётчик комментариев! для нового и старого дизайна соответственно
                    spans=div.find_all("span")
                    for span in spans:
                        if span.has_attr("class"):
                            if span["class"][0]=="comments_count_link":
                                comments_n=spans[0].a.contents[0]
                    posts_comments_n.append(comments_n)

                    


            #мы великолепны. теперь у нас в каждом массиве будет по 20 элементов, т.к. на странице 20 постов
            #и при этом что бы ни случилось, все поля будут заполнены, поэтому мы можем быть уверены
            #что не случится смещения на 1 в каком-либо массиве. а если даже случится, то при сборке в следующей
            #части мы обязательно получим ошибку (кроме случая, когда массив posts_ids окажется меньше, чем надо)

            #в этом случае какой-то пост будет утерян, а ещё мы получим неизвестные смещения по остальным метаданным

        #а теперь надо всё собрать обратно

        
        if s.diary_url_mode==s.dum.one_post:
            posts_ids=[posts_ids[0]]
        #там может ещё что-то обнаружиться в комментариях, но комментарии надо отдельно парсить, этого пока нет
        l.info("writing posts: "+str(len(posts_ids)))

        for x in range(len(posts_ids)):
            res=db.add_post(int(posts_ids[x]),posts_links[x],posts_dates[x],posts_times_s[x],posts_titles[x],posts_comments_n[x],posts_tags[x],posts_contents[x])
            if res==db.db_ret.updated_comments_n_identical:
                comments_n_changed=False
            if \
                update==True and \
                saved_pages>2 and \
                (res==db.db_ret.updated_comments_n_changed or res==db.db_ret.updated_comments_n_identical) and \
                s.diary_url_mode==s.dum.full:

                l.info(f"Update complete, found old posts. Saved pages={saved_pages}")
                print("Update complete, found old posts.")
                return
            if update==True and comments_n_changed==False and s.diary_url_mode==s.dum.newest_comments:
                l.info("Update comments complete, found posts with equal comments counter.")
                print("Update comments complete, found posts with equal comments counter.")
                return            

        saved_pages+=1
        l.info(f"Done saving. Waiting for {s.wait_time} sec...")
        print(f"Done saving. Waiting for {s.wait_time} sec...")
        time.sleep(s.wait_time)


    db.close()

    l.info(f"Done. Downloadaed {len(posts_ids)} posts.")
    print(f"Done. Downloadaed {len(posts_ids)} posts.")
    if s.diary_url_mode==s.dum.one_post:#скачал один пост -- сообщи ид выше
        return post_id

def download_comments_from_post(post_id:int,n:int,percentage:int,left:int):
    comments_on_page=30
    comments_existing_ids=db.get_comments_list(post_id)
    urls=[]
    pages=n//comments_on_page+1
    comments_n_actual=0
    for page in range(pages):
        url=f"https://{s.uname}.diary.ru/p{post_id}.htm?from={comments_on_page*page}"
        urls.append(url)

        print(f"[{percentage}%, {left} posts left] Comments: {n}. Downloading "+url+"...")
        l.info(f"[{percentage}%, {left} posts left] Comments: {n}. Downloading "+url+"...")
        page = requests.get(url,cookies=get_cookies())
        page = BeautifulSoup(change_pre(page.text), 'lxml')
            
        #c_ означает comment_. это сокращение
        c_contents=[]
        c_id=[]
        c_date=[]
        c_time=[]
        c_author=[]

        first_on_page=True

        #разбор данных на метаданные

        epigraph={}
        c_class_name_id="discussion"
        #нам надо пропустить все дивы эпиграфа
        posts_divs=page.find_all("div")
        for div in posts_divs:
            if div.has_attr("class") and len(div["class"])>0:
                class_name=div["class"][0]
                if len(div["class"])>1:
                    class_name_2nd=div["class"][1]
                else:
                    class_name_2nd=""
                #отладочный вывод, когда дайри-программист в очередной раз перепиливает разметку
                #id_name=div["id"] if div.has_attr("id") else "[none]"
                #print("Class:"+class_name+", id="+id_name)

                if class_name == c_class_name_id or class_name_2nd==c_class_name_id:
                    if div.has_attr("data-id"):
                        c_id.append(div["data-id"])
                    else:
                        l.info("Warning! No ID! POST_ID: "+str(post_id))
                if class_name == "authorName" and div.has_attr("style")==False:#авторство есть и у поста, с которого начинается ветка, но там есть дополнительный тег
                    contents=div.a.strong.contents
                    if(len(contents)==0):
                        c_author.append("UNKNOWN")#такое реально есть в https://zhz00.diary.ru/p175991102.htm . Комментарий удалён администрацией и почему-то оставлена записочка об этом!
                    else:
                        c_author.append(div.a.strong.contents[0])
                if class_name == "post-header":
                    dt=div.span.contents[0]
                    if len(dt)>10:#у стартового поста только время, а это всего 5 символов, так что если больше 10, то это комментарий
                        c_date.append(convert_date_ru_to_iso(dt[:10]))
                        c_time.append(dt[13:])
                if class_name== "post-inner" and not (div.parent.has_attr("class") and div.parent["class"][0]=="post-inner"):#if(div.parent.find("p")!=None):#если тегов у коммента нет, то это не работает
                    if first_on_page==True:
                        first_on_page=False
                    else:
                        c_contents.append(remove_newlines_ex(div))
        len1=len(c_id)
        len2=len(c_author)
        len3=len(c_date)
        len4=len(c_time)
        len5=len(c_contents)
        cl1=len1==len2
        cl2=len2==len3
        cl3=len3==len4
        cl4=len4==len5
        c_common=cl1 and cl2 and cl3 and cl4
        if c_common==False:
            l.info(f"Warning! Different length of fields while downloading comments. post_id={post_id},id:{len1},author:{len2},date:{len3},time:{len4},contents:{len5}")
        else:
            #можно добавлять
            for x in range(len(c_id)):
                #добавить конвертацию даты
                db.add_comment(int(c_id[x]),post_id,c_date[x],c_time[x],c_author[x],c_contents[x])
                comments_n_actual+=1
                if int(c_id[x]) in comments_existing_ids:
                    comments_existing_ids.remove(int(c_id[x]))#если скачанный коммент уже есть в базе, удалим из списка. зачем? см. далее
        print(f"Waiting for {s.wait_time} seconds...")
        time.sleep(s.wait_time)

    for comment_id in comments_existing_ids:
        #те комменты которые остались -- это те что есть в базе, но мы их не нашли. почему? потому что их удалили. надо их пометить в базе
        l.info(f"Deleting comment #{comment_id}...")
        print(f"Deleting comment #{comment_id}...")
        db.mark_deleted_comment(comment_id)
        comments_n_actual-=1
    db.update_comments_n(post_id,comments_n_actual)

@init.log_call
def download_comments(update:bool):
    print("Stage 2 of 7: Downloading (updating) comments")
    if s.download_comments==False:
        print("Skip.")
        return
    db.connect()
    if update==True:
        s.diary_url_mode=s.dum.newest_comments
        download(update=True,auto_find=True)
    
    print("Generating post list...")
    posts=db.get_posts_list()
    posts_to_download=[]
    posts_comments_n=[]
    for post_id in tqdm.tqdm(posts,ascii=True):
        n=db.get_comments_n(post_id)
        if n!=db.get_comments_downloaded(post_id):
            posts_to_download.append(post_id)
            posts_comments_n.append(n)
    print(f"{len(posts_to_download)} posts to update...")
    posts_n=len(posts_to_download)
    for x in range(posts_n):
        percentage=(x+1)*100//posts_n
        left=posts_n-x-1
        download_comments_from_post(posts_to_download[x],posts_comments_n[x],percentage,left)

if __name__=="__main__":
    #convert_to_old_style("https://zhz00.diary.ru/p221381736_podschyot-prosmotrov-v-telegrame.htm")
    init.create_folders()
    download(update=False,auto_find=False)