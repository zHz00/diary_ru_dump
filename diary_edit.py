import time

import requests
from bs4 import BeautifulSoup
import markdownify
import click

import settings as s
import db
import download

def check_session()->bool:
    url=f"https://{s.uname}.diary.ru/"
    session=requests.Session()
    session.cookies=download.get_cookies()
    res=session.get(url)
    if res.text.find("https://diary.ru/user/registration")!=-1:
        print("Probably, not logged in! (check)")
        return False
    print("Session OK")
    time.sleep(2.0)
    return True


def delete_comment(comment_id:int,post_id:int)->int:
    url=f"https://{s.uname}.diary.ru/p{post_id}.htm"
    session=requests.Session()
    session.cookies=download.get_cookies()
    res=session.get(url)
    if res.text.find("https://diary.ru/user/registration")!=-1:
        print("Probably, not logged in!")
        return 404
    page=BeautifulSoup(res.text,'lxml')
    for m in page.find_all("meta"):
        if m.has_attr("name") and m["name"]=="csrf-token":
            token=m["content"]
            #print("Token: "+token)
            break
    html=open("test.html","w",encoding="utf-8")
    html.write(res.text)
    html.close()
    headers={"X-CSRF-Token":token,"X-Requested-With":"XMLHttpRequest"}
    url=f"https://{s.uname}.diary.ru/?deletecomment&id={comment_id}"

    
    time.sleep(5.0)
    res=session.get(url,headers=headers)
    #print(f"Result: {res.status_code}")
    return res.status_code

    #X-CSRF-Token
    #X-Requested-With: XMLHttpRequest

def show_hint():
    print("==[ and ]: scroll===d:mark for deletion===x:not spam===q:quit====ENTER:go==",end="")

def show_state(text:str,not_spam:int,for_del:int):
    print(text,end="")
    print(":=================================================",end="")
    if not_spam:
        print("[NOT SPAM]",end="")
    else:
        print("==========",end="")

    if for_del:
        print("[DELETE]")
    else:
        print("========")

def cls():
    print('\n' * 80)

def show_comment_meta(comment_row,idx:int,comments_n:int)->None:
    print("===========================COMMENT FOR REVIEW==============================")

    print(f"({idx}/{comments_n})")
    print(f"Post title: {comment_row['TITLE']}")
    print(f"Post date: {comment_row['P_DATE']}")
    print(f"Post ID: {comment_row['POST_ID']}")
    print("===========================================================================")
    print(f"Comment date: {comment_row['C_DATE']}")
    print(f"Comment age: {int(comment_row['DIFF'])} days")
    print(f"Comment ID: {comment_row['COMMENT_ID']}")
    print("===========================================================================")
    comment=BeautifulSoup(comment_row["CONTENTS"],"lxml")
    contents=str(comment).replace("\n","").replace("\r","")
    print(markdownify.markdownify(contents))
    

   

def detect_spam()->None:
    idx=0
    def next_c():
        nonlocal idx
        if idx<total-1:
            idx+=1
    def prev_c():
        nonlocal idx
        if idx>0:
            idx-=1
    def not_spam():
        nonlocal comments_not_spam,comments_for_del
        comments_not_spam[idx]=(1 if comments_not_spam[idx]==0 else 0)
        comments_for_del[idx]=0
        next_c()
    def for_del():
        nonlocal comments_not_spam,comments_for_del
        comments_for_del[idx]=(1 if comments_for_del[idx]==0 else 0)
        comments_not_spam[idx]=0
        next_c()
    def esc():
        quit(0)
    def go():
        not_spam_n=sum(comments_not_spam)
        for_del_n=sum(comments_for_del)
        print(f"\n{not_spam_n} comments will be marked as natural (not spam). Proceed?[y/n](Enter=y)")
        answer=input()
        if(answer=='y' or answer=='Y' or answer==''):
            processed=0
            for idx,comment in enumerate(comments_list):
                if comments_not_spam[idx]==1:
                    c_id=comment['COMMENT_ID']
                    post_id=comment['POST_ID']
                    res=db.mark_not_spam_comment(c_id)
                    #res=0
                    if res==db.db_ret.updated:
                        print(f"({processed+1}/{not_spam_n})Comment {c_id} from post {post_id} marked as not spam.")
                    else:
                        print(f"({processed+1}/{not_spam_n})Comment {c_id} from post {post_id} FAILD to be marked as not spam.")
                    processed+=1

        print(f"\n{for_del_n} comments will be deleted from diary on the internet. Proceed?[y/n](Enter=y)")
        answer=input()
        if(answer=='y' or answer=='Y' or answer==''):
            processed=0
            for idx,comment in enumerate(comments_list):
                if comments_for_del[idx]==1:
                    c_id=comment['COMMENT_ID']
                    post_id=comment['POST_ID']
                    res=delete_comment(c_id,post_id)
                    res_db=db.db_ret.unknown
                    if res==200:
                        res_db=db.mark_deleted_comment(c_id)
                    else:
                        print(f"Result: {res}")
                    if res==500:#комментарий не найден, всё равно удалить из базы
                        print(f"({processed+1}/{for_del_n})Comment {c_id} from post {post_id} NOT found on diary. Deleting from DB...",end="")
                        time.sleep(5.0)
                        res_db=db.mark_deleted_comment(c_id)
                    if res==404:#ошибка доступа или сброс сессии
                        print("Session reset? Aborting...")
                        quit(2)
                    #если ни 200, ни 500, то комментарий был, но удалить его не вышло. в этом случае удалять из БД не надо

                    #res=0
                    if res_db==db.db_ret.updated:
                        print(f"({processed+1}/{for_del_n})Comment {c_id} from post {post_id} marked as deleted.",end="")
                    else:
                        print(f"({processed+1}/{for_del_n})Comment {c_id} from post {post_id} FAILD to be marked as deleted.",end="")
                    processed+=1
                    print("Wait for 5 sec...")
                    time.sleep(5.0)
        print("Done.")
        quit(0)

    actions=dict()
    actions[']']=next_c
    actions['[']=prev_c
    actions['d']=for_del
    actions['x']=not_spam
    actions['q']=esc
    actions['\r']=go
    comments_list=db.get_spam_comments(365)#комментарии старши 600 дней
    total=len(comments_list)
    if total==0:
        print("No spam found! Quitting...")
        quit(0)
    comments_not_spam=[0]*total
    comments_for_del=[0]*total

    key=' '

    
    while True:
        cls()
        if key=='d' or key=='x':
            show_state("===PREV",comments_not_spam[idx-1],comments_for_del[idx-1])
        show_comment_meta(comments_list[idx],idx+1,total)
        show_state("CURRENT",comments_not_spam[idx],comments_for_del[idx])
        show_hint()
        key=click.getchar()
        if key in actions:
            actions[key]()
        
    

if __name__=="__main__":
    db.connect()
    s.load_username()
    if check_session()==False:
        quit(1)
    s.wait_time=10
    download.download(update=True,auto_find=True)
    download.download_comments(update=True)
    detect_spam()
    #delete_comment(758183957,221973878)


