import time

from download import download
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from markdown_all_diary import get_post_as_html
import settings as s
import tg_ph
import tg_channel
import db

def post_to_tgph(post_id,img_list):

    #OLD
    #html=open(s.dump_folder+"p"+str(post_id)+".htm","r",encoding="utf-8")
    #html_text=html.read()

    #DB
    html_text=get_post_as_html(post_id)

    uploaded_list=[]
    for img in img_list:
        #pass
        if img[0].strip() in html_text:
            #uploaded=tg_ph.upload_image(s.base_folder+s.pics_folder+img[1])
            #uploaded_list.append([img[0],"https://telegra.ph"+uploaded])
            #к сожалению, телегра.ф отключил загрузку картинок, поэтому придётся убирать
            uploaded_list.append([img[0],img[0]])#просто повторяем урл, теперь будет хотлинкинг на имедж-хостинг
            #print("uploaded:"+uploaded)
            #time.sleep(s.wait_time)
        else:
            print(img[0]+" not found in html, skipping")
    for img in uploaded_list:
        print("Replacing "+img[0]+" to "+img[1])
        html_text=html_text.replace(img[0].strip(),img[1])
    node_text=tg_ph.html_to_node(html_text)
    node_text=node_text.replace(',"children":[]','')#сократим размер
    node_out=open(s.dump_folder+"p"+str(post_id)+"node.txt","w",encoding="utf-8")
    node_out.write(node_text)
    node_out.close()
    header=db.get_post_title(post_id)
    print("Header:"+header)
    node_out=open(s.dump_folder+"p"+str(post_id)+"node.txt","r",encoding="utf-8")
    node_text=node_out.read()
    tg_ph.init(s.tg_ph_token)
    print("telegra.ph connection initiated")
    return tg_ph.create_page(header,node_text)
    #return None

SEPARATOR=0
CAPTION=1

def divide_post(post_id,md_post_name):
    #DB
    header=db.get_post_title(post_id)

    md=open(md_post_name,"r",encoding="utf-8")
    md_text=md.readlines()
    md.close()

    md_text.insert(0,"\n\n")
    md_text.insert(0,"*"+header.strip()+"*")

    cur_len=0#накапливаем длину абзацев для поста
    posts=[]

    test_out=open(s.dump_folder+"posts.txt","w",encoding="utf-8")

    unbreakable=False
    prev_line=""

    for line in md_text:
        if line.strip().startswith("*"):
            print("found unbreakable")
            unbreakable=True
            unbreakable_start=len(posts)
        cur_len+=len(line)
        if(cur_len>s.tg_post_len or \
        line.strip().startswith("[![]") or\
        line.strip().startswith("![]")):
            if unbreakable:#подзаголовки неотделяемы
                print("inserting separator before")
                posts.insert(unbreakable_start-1,SEPARATOR)
                cur_len=len(line)
            else:
                posts.append(SEPARATOR)
                cur_len=0
            unbreakable=False
        if prev_line.strip().startswith("[![]") or\
        prev_line.strip().startswith("![]"):
            #надо ли делать подпись к картинке?
            if len(line.strip())>0:
                if(len(line.strip())<s.tg_pic_len):
                    posts.append(CAPTION)#метка, что надо подпись поставить
                else:
                    posts.append(SEPARATOR)
        if "linkmore" not in line:#линкмор пропускаем
            posts.append(line)
        if len(line.strip())>0 and unbreakable_start+1!=len(posts):#если флаг выставлен только что, сбрасывать не надо
            unbreakable=False
        #if len(line.strip())>0:
        prev_line=line

    posts.append(SEPARATOR)
    for p in posts:
        if p is SEPARATOR:
            test_out.write("\nSEPARATOR\n")
        elif p is CAPTION:
            test_out.write("\nCAPTION\n")
        else:
            test_out.write("Post:"+p)

    test_out.close()
    print("posts divided")
    return posts


def post_to_tgch(post_id,img_list,md_post_name):
    divided_post=divide_post(post_id,md_post_name)
    print(divided_post)
    text=""
    token=s.tg_channel_token
    chat_id=s.tg_channel_name

    tg_channel.init(token,chat_id)
    retries=0

    for x in range(len(divided_post)):
        if divided_post[x] is SEPARATOR:
            if len(text.strip())>0:
                text=text.replace("__","*")
                while retries<s.tg_max_retries:
                    res=tg_channel.send_text(text,False)
                    res_dict=res.json()
                    if res_dict["ok"]!=True:
                        print("error sending: ["+text+"]")
                        print(res_dict)
                        retries+=1
                        print("wait for 60 sec, retries={retries}")
                        time.sleep(60)
                    else:
                        print("Post sent")
                        retries=0
                        break
                time.sleep(5)
            text=""
        else:
            if divided_post[x] is CAPTION or (x>0 and divided_post[x-1] is CAPTION):
                continue
            if divided_post[x].strip().startswith("[![]") or divided_post[x].strip().startswith("![]"):
                #постим картинку
                caption=""
                if x<len(divided_post)-1 and divided_post[x+1] is CAPTION:
                    caption=divided_post[x+2]
                #if x<len(divided_post)-2 and divided_post[x+2] is CAPTION:
                #    caption=divided_post[x+3]
                #в каком-то смысле это костыль: делать отдельный случай, если подпись сразу после картинки, и если есть пустая строка.
                #с другой стороны, если после картинки больше одной пустой строки, то, возможно, это вовсе не подпись
                img_file=""
                for img in img_list:
                    print("searching "+img[0].strip()+" in "+divided_post[x])
                    if img[0].strip() in divided_post[x]:
                        print("image found!")
                        img_file=img[1]
                while retries<s.tg_max_retries:
                    res=tg_channel.send_image(caption,s.base_folder+s.pics_folder+img_file)
                    res_dict=res.json()
                    if res_dict["ok"]!=True:
                        print("error sending: ["+text+"]")
                        retries+=1
                        print("wait for 60 sec")
                        time.sleep(60)
                    else:
                        print("Image uploaded")
                        retries=0
                        break
                time.sleep(5)
                continue
            if len(divided_post[x].strip())>0:
                text+=divided_post[x].lstrip(" \n")#табуляции оставим
            else:
                text+=divided_post[x]
    
def post_short_to_tgch(post_id,tgph_url):

    header=db.get_post_title(post_id)
    (date_db,time_db)=db.get_post_date_time(post_id)
    out_text="*"
    out_text+=header.strip()#header
    out_text+="*\n\n"
    out_text+=date_db.strip()+", "+time_db.strip()+"\n"
    out_text+="[(читать на telegra.ph)]("+tgph_url+")\n\n"
    out_text+=s.diary_url_pretty+"p"+str(post_id)+".htm\n\n"

    tags=db.get_post_tags(post_id)
    for tag in tags:
        out_text+="#"+tag.replace(" ","\\_")#пробелов быть не должно

    
    tgch_short_file=open(s.dump_folder+"short.txt","w",encoding="utf-8")
    tgch_short_file.write(out_text)
    tgch_short_file.close()
    
    print(out_text)
    
    token=s.tg_channel_token
    chat_id=s.tg_channel_name
    
    tg_channel.init(token,chat_id)
    res=tg_channel.send_text(out_text)
    print(res)
    

def main():
    s.diary_url_mode=s.dum.one_post#отдельный пост
    s.load_username()
    s.load_tokens()
    s.wait_time=20
    post_id=0
    #post_id=221255709#статья про руку
    #post_id=221274643#исходный код
    #post_id=221254557#тестирование тега мор
    #post_id=221267424#короткий пост с картинкой дороги
    #post_id=221244585#нетхак и проблемы с инвокацией
    #post_id=221211114#aoi sora no camus
    #post_id=221200537#тег мор
    #post_id=221277284

    #src_post=open(s.dump_folder+post,"r",encoding="utf-8")
    #src_post_contents=src_post.read()
    post_id=download(False,False,post_id)#автоматически найти последний пост
    if post_id==0:
        return
    #init.create_folders()
    md_post_name,md_post_len=markdown_all_diary(True,post_id)
    print(md_post_name)
    print(md_post_len)
    img_list=download_pics(post_id)
    print("IMAGES:")
    print(img_list)

    db.connect()

    if md_post_len>s.tg_max_len or len(img_list)>s.tg_max_pics:
        print(f"Posting to telegraph... (Pause:{s.wait_time})")
        time.sleep(s.wait_time)
        print("Pause ended")
        url=post_to_tgph(post_id,img_list)
        post_short_to_tgch(post_id,url)
    else:
        print(f"Posting to channel... (Pause:{s.wait_time})")
        time.sleep(s.wait_time)
        post_to_tgch(post_id,img_list,md_post_name)

if __name__=="__main__":
    main()
