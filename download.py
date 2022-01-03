#download diary

import requests
from bs4 import BeautifulSoup
import time
import re

from requests.sessions import RequestsCookieJar
import settings as s

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

for offset in range(s.start, s.stop, 20):
    page_url=s.diary_url+str(offset)
    print("Downloading "+page_url+"...")
    page = requests.get(page_url,cookies=cookies)
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
            if class_name =="day-header":
                posts_dates_s.append(div.span.contents[0])
                posts_dates.append(convert_date(div.span.contents[0]))
            if class_name =="post-header":
                if len(posts_dates_s)!=len(posts_links)+1:#если для текущей записи не нашлось даты из-за двух записей в течение дня
                    posts_dates_s.append(posts_dates_s[-1])
                    posts_dates.append(posts_dates[-1])
                posts_links.append(div.a["href"])
                id_begin=div.a["href"].find(s.link_marks[0])+len(s.link_marks[0])
                posts_ids.append(div.a["href"][id_begin:id_begin+9])
                posts_times_s.append(div.span.contents[0])
                if len(div.a.contents)>0:
                    posts_titles.append(div.a.contents[0])
                else:
                   posts_titles.append("(no title)")
                print(f"Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
            if class_name =="post-inner":
                posts_contents.append(div.prettify().replace('\r', '').replace('\n', ''))
            if class_name == "post-content":
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
