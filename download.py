#download diary

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re

df = pd.DataFrame([],columns=['postId', 'date', 'comments', 'full_version', 'tags', 'symbol_count', 'words_count', 'images'])

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

for offset in range(3760, 3800, 20):
    #page = requests.get('http://zhz00.diary.ru/?oam&from=' + str(offset))"""
    page_url='https://diary.ru/~zHz00?oam&rfrom='+str(offset)
    print("Downloading "+page_url+"...")
    page = requests.get(page_url)
    #page=open("test2.htm",encoding="utf-8").read()
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
    for i in posts_divs:
        if i.has_attr("class") and len(i["class"])>0:
            class_name=i["class"][0]
            if class_name =="day-header":
                posts_dates_s.append(i.span.contents[0])
                posts_dates.append(convert_date(i.span.contents[0]))
            if class_name =="post-header":
                if len(posts_dates_s)!=len(posts_links)+1:#если для текущей записи не нашлось даты из-за двух записей в течение дня
                    posts_dates_s.append(posts_dates_s[-1])
                    posts_dates.append(posts_dates[-1])
                posts_links.append(i.a["href"])
                id_begin=i.a["href"].find("00/p")+4
                posts_ids.append(i.a["href"][id_begin:id_begin+9])
                posts_times_s.append(i.span.contents[0])
                if len(i.a.contents)>0:
                    posts_titles.append(i.a.contents[0])
                else:
                   posts_titles.append("(no title)")
                print(f"Got post. ID: {posts_ids[-1]}, title: {posts_titles[-1]}")
            if class_name =="post-inner":
                posts_contents.append(i.prettify().replace('\r', '').replace('\n', ''))
            if class_name == "post-content":
                tags=[]
                post_tags=[]
                posts_ps=i.find_all("p")
                for j in posts_ps:
                    if j.has_attr("class"):
                        if j["class"][0]=="tags":
                            tags=j.find_all("a")
                            for k in tags:
                                post_tags.append(k.contents[0])
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

        out_meta=open("dump\\p"+posts_ids[x]+".txt","w",encoding="utf-8")
        out_meta.write(f"{posts_ids[x]}\n")
        out_meta.write(f"{posts_links[x]}\n")
        out_meta.write(f"{posts_dates[x]}\n")
        out_meta.write(f"{posts_times_s[x]}\n")
        out_meta.write(f"{posts_titles[x]}\n")
        for i in posts_tags[x]:
            out_meta.write(f"{i} ")
        out_meta.write("\n")
        out_meta.close()

        out_page=BeautifulSoup(fish,"html.parser")

        #out_page.find("title").string=posts_titles[x]
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

        for i in posts_tags[x]:
            out_page.find("body").append(BeautifulSoup("[["+i+"]] <br />", 'html.parser'))

        out_page.find("body").append(BeautifulSoup("ID: p"+posts_ids[x]+"]] <br />", 'html.parser'))

        out_post=open("dump\\p"+posts_ids[x]+".htm","w",encoding="utf-8")
        out_post.write(out_page.prettify())
        out_post.close()

    print("Done saving. Waiting for 1 minute...")
    time.sleep(60)




print("end (dump)")
