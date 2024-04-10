import settings as s
import db
from bs4 import BeautifulSoup
import markdownify
import click
import requests

def delete_comment(comment_id:int,post_id:int)->bool:
    return False

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

def show_comment_meta(comment_row,idx:int,max:int,not_spam:int,for_del:int)->None:
    print("===========================COMMENT FOR REVIEW==============================")

    print(f"({idx}/{max})")
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
    def next():
        nonlocal idx
        if idx<total-1:
            idx+=1
    def prev():
        nonlocal idx
        if idx>0:
            idx-=1
    def not_spam():
        nonlocal comments_not_spam,comments_for_del
        comments_not_spam[idx]=(1 if comments_not_spam[idx]==0 else 0)
        comments_for_del[idx]=0
        next()
    def for_del():
        nonlocal comments_not_spam,comments_for_del
        comments_for_del[idx]=(1 if comments_for_del[idx]==0 else 0)
        comments_not_spam[idx]=0
        next()
    def esc():
        quit(0)
    def go():
        not_spam_n=sum(comments_not_spam)
        for_del_n=sum(comments_for_del)
        print(f"{not_spam_n} comments will be marked as natural (not spam). Proceed?[y/n]")
        answer=input()
        if(answer=='y' or answer=='Y'):
            for idx,comment in enumerate(comments_list):
                if comments_not_spam[idx]==1:
                    #res=db.mark_not_spam_comment(comment['COMMENT_ID'])
                    res=0
                    if res==db.db_ret.updated:
                        print(f"Comment {comment['COMMENT_ID']} marked as not spam.")
                    else:
                        print(f"Comment {comment['COMMENT_ID']} FAILD to be marked.")

        print(f"{for_del_n} comments will be deleted from diary on the internet. Proceed?[y/n]")
        answer=input()
        if(answer=='y' or answer=='Y'):
            for idx,c_id in enumerate(comments_list):
                if comments_for_del[idx]==1:
                    #res=delete_from_diary(c_id)
                    res=0
                    if res==db.db_ret.updated:
                        print(f"Comment {comment['COMMENT_ID']} deleted.")
                    else:
                        print(f"Comment {comment['COMMENT_ID']} FAILD to be deleted.")
        quit(0)

    l_next=lambda:next()
    l_prev=lambda:prev()
    l_not_spam=lambda:not_spam()
    l_for_del=lambda:for_del()
    l_esc=lambda:esc()
    l_go=lambda:go()
    actions=dict()
    actions[']']=l_next
    actions['[']=l_prev
    actions['d']=l_for_del
    actions['x']=l_not_spam
    actions['q']=l_esc
    actions['\r']=l_go
    comments_list=db.get_spam_comments(600)#комментарии старши 600 дней
    total=len(comments_list)
    comments_not_spam=[0]*total
    comments_for_del=[0]*total

    key=' '

    
    while True:
        cls()
        if key=='d' or key=='x':
            show_state("===PREV",comments_not_spam[idx-1],comments_for_del[idx-1])
        show_comment_meta(comments_list[idx],idx+1,total,comments_not_spam[idx],comments_for_del[idx])
        show_state("CURRENT",comments_not_spam[idx],comments_for_del[idx])
        show_hint()
        key=click.getchar()
        if key in actions:
            actions[key]()
        
    

if __name__=="__main__":
    db.connect()
    detect_spam()


