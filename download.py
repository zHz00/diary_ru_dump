#download diary

import requests
from bs4 import BeautifulSoup
import time
import re

from requests.sessions import RequestsCookieJar
import settings as s

import init

init.create_folders()

def convert_date(date):
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

cookies=RequestsCookieJar()
for c_name,c_value in s.saved_cookies.items():
    cookie=requests.cookies.create_cookie(domain="diary.ru",name=c_name,value=c_value)
    cookies.set_cookie(cookie)

if s.diary_url_mode==0:
    step=20
if s.diary_url_mode==1:
    step=1
    
for offset in range(s.start, s.stop, step):
    page_url=s.diary_url+str(offset)
    print("Downloading "+page_url+"...")
    page = requests.get(page_url,cookies=cookies)

    # тестирование, работают куки или нет. отключено
    #testpage=open("testpage.htm","w")
    #testpage.write(page.text)
    #testpage.close()

    page = BeautifulSoup(page.text, 'html.parser')
    posts_titles=[]
    posts_links=[]
    posts_dates_s=[]
    posts_times_s=[]
    posts_contents=[]
    posts_tags=[]

    posts_ids=[]
    posts_dates=[]
    posts_times=[]

    #разбор данных на метаданные

    posts_divs=page.find_all("div")
    for div in posts_divs:
        if div.has_attr("class") and len(div["class"])>0:
            class_name=div["class"][0]
            if class_name == "day-header":
                posts_dates_s.append(div.span.contents[0])
                posts_dates.append(convert_date(div.span.contents[0]))
            if class_name == "singlePost" and div.div["class"][0] == "countSecondDate":
                posts_dates_s.append(div.div.span.contents[0])
                posts_dates.append(convert_date(div.div.span.contents[0]))
            if class_name == "post-header" or class_name == "postTitle":
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
            if class_name == "postLinksBackg":#старый дизайн
                posts_links.append(div.span.a["href"])
                id_begin=div.span.a["href"].lower().find(s.link_marks[s.links_style])+len(s.link_marks[s.links_style])
                id_end=div.span.a["href"].rfind("_")
                if id_end==-1:
                    id_end=div.span.a["href"].rfind(".")#без заголовка, поэтому нижнего подчёркивания нет
                posts_ids.append(div.span.a["href"][id_begin:id_end])
                print(f"Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
            if class_name == "post-links":#новый дизайн
                posts_links.append(div.div.a["href"])
                id_begin=div.div.a["href"].find(s.link_marks[s.links_style])+len(s.link_marks[s.links_style])
                id_end=div.div.a["href"].find("_",id_begin)
                if id_end==-1:
                    id_end=div.a["href"].find(".",id_begin)#без заголовка, поэтому нижнего подчёркивания нет
                posts_ids.append(div.div.a["href"][id_begin:id_end])
                print(f"Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
            if class_name == "post-inner" or class_name == "postInner":
                posts_contents.append(div.prettify().replace('\r', '').replace('\n', ''))
            if class_name == "post-content" or class_name == "postContent":
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
                


        #мы великолепны. теперь у нас в каждом массиве будет по 20 элементов, т.к. на странице 20 постов
        #и при этом что бы ни случилось, все поля будут заполнены, поэтому мы можем быть уверены
        #что не случится смещения на 1 в каком-либо массиве. а если даже случится, то при сборке в следующей
        #части мы обязательно получим ошибку (кроме случая, когда массив posts_ids окажется меньше, чем надо)

        #в этом случае какой-то пост будет утерян, а ещё мы получим неизвестные смещения по остальным метаданным

    #а теперь надо всё собрать обратно

    fish="<html><title></title><body></body></html>"
    out_page=BeautifulSoup(fish,"html.parser")
    #это не соответствует в3ц, ну и ладно
    print("writing posts: "+str(len(posts_ids)))

    for x in range(len(posts_ids)):
        #метаданные собираем в отдельный файл

        out_meta=open(s.dump_folder+"p"+posts_ids[x]+".txt","w",encoding=s.post_encoding)
        out_meta.write(f"{posts_ids[x]}\n")
        out_meta.write(f"{posts_links[x]}\n")
        out_meta.write(f"{posts_dates[x]}\n")
        out_meta.write(f"{posts_times_s[x]}\n")
        out_meta.write(f"{posts_titles[x]}\n")
        for tag in posts_tags[x]:
            out_meta.write(f"{tag}\n")
        out_meta.write("\n")
        out_meta.close()

        out_page=BeautifulSoup(fish,"html.parser")

        title_header=BeautifulSoup("<h1></h1>", 'html.parser')
        title_header.find("h1").string=posts_titles[x]
        out_page.find("body").append(title_header)
        out_page.find("body").append(BeautifulSoup("<br />", 'html.parser'))

        out_page.find("body").append(posts_dates[x]+", "+posts_times_s[x])
        out_page.find("body").append(BeautifulSoup("<br />", 'html.parser'))

        out_page.find("body").append(BeautifulSoup(posts_contents[x],'html.parser'))
        out_page.find("body").append(BeautifulSoup("<br />", 'html.parser'))

        #другие метаданные тоже надо внести

        title_url=title_header.new_tag("a",href=posts_links[x])
        title_url.string=posts_links[x]
        out_page.find("body").append(title_url)
        out_page.find("body").append(BeautifulSoup("<br />", 'html.parser'))

        out_page.find("body").append(BeautifulSoup("<br />Теги:<br />", 'html.parser'))

        for tag in posts_tags[x]:
            out_page.find("body").append(BeautifulSoup("[["+re.sub(r'[\\/*?:"<>|]',"",tag).strip()+"]] <br />", 'html.parser'))

        out_page.find("body").append(BeautifulSoup("ID: p"+posts_ids[x]+"<br />", 'html.parser'))

        out_post=open(s.dump_folder+"p"+posts_ids[x]+".htm","w",encoding=s.post_encoding)
        out_post.write(out_page.prettify())
        out_post.close()

    print(f"Done saving. Waiting for {s.wait_time} sec...")
    time.sleep(s.wait_time)




print(f"end (dump). Downloadaed {len(posts_ids)} posts.")
