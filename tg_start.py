import requests
from download import download
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
import settings as s
import init
import tg_ph
import tg_channel
import time

def post_to_tgph(post_id,img_list):
    html=open(s.dump_folder+"p"+str(post_id)+".htm","r",encoding="utf-8")
    html_text=html.read()
    uploaded_list=[]
    for img in img_list:
        #pass
        if img[0].strip() in html_text:
            uploaded=tg_ph.upload_image(s.base_folder+s.pics_folder+img[1])
            uploaded_list.append([img[0],"https://telegra.ph"+uploaded])
            #print("uploaded:"+uploaded)
            time.sleep(s.wait_time)
        else:
            print(img[0]+" not found in html, skipping")
    for img in uploaded_list:
        print("Replacing "+img[0]+" to "+img[1])
        html_text=html_text.replace(img[0].strip(),img[1])
    node_text=tg_ph.html_to_node(html_text)
    node_out=open(s.dump_folder+"p"+str(post_id)+"node.txt","w",encoding="utf-8")
    node_out.write(node_text)
    node_out.close()
    meta=open(s.dump_folder+"p"+str(post_id)+".txt","r",encoding="utf-8")
    meta_text=meta.readlines()
    meta.close()
    print("Header:"+meta_text[4])
    node_out=open(s.dump_folder+"p"+str(post_id)+"node.txt","r",encoding="utf-8")
    node_text=node_out.read()
    tg_ph.init(s.tg_ph_token)
    return tg_ph.create_page(meta_text[4],node_text)
    #return None

    
SEPARATOR=0
CAPTION=1

def divide_post(post_id,md_post_name):
    meta=open(s.dump_folder+"p"+str(post_id)+".txt","r",encoding="utf-8")
    meta_text=meta.readlines()
    meta.close()
    
    md=open(md_post_name,"r",encoding="utf-8")
    md_text=md.readlines()
    md.close()
    
    md_text.insert(0,"\n\n")
    md_text.insert(0,"*"+meta_text[4].strip()+"*")
    
    cur_len=0#накапливаем длину абзацев для поста
    posts=[]
    
    test_out=open("posts.txt","w",encoding="utf-8")
    
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
        if len(line.strip())>0:
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
    text=""
    token=s.tg_channel_token
    chat_id=s.tg_channel_name
    
    tg_channel.init(token,chat_id)
    retries=0
    
    for x in range(len(divided_post)):
        if divided_post[x] is SEPARATOR:
            if(len(text.strip())>0):
                text=text.replace("__","*")
                while retries<s.tg_max_retries:
                    res=tg_channel.send_text(text,False)
                    res_dict=res.json()
                    if(res_dict["ok"]!=True):
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
                if x<len(divided_post)+1 and divided_post[x+1] is CAPTION:
                    caption=divided_post[x+2]
                else:
                    caption=""
                img_file=""
                for img in img_list:
                    print("searching "+img[0].strip()+" in "+divided_post[x])
                    if img[0].strip() in divided_post[x]:
                        print("image found!")
                        img_file=img[1]
                while retries<s.tg_max_retries:
                    res=tg_channel.send_image(caption,s.base_folder+s.pics_folder+img_file)
                    res_dict=res.json()
                    if(res_dict["ok"]!=True):
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
    meta=open(s.dump_folder+"p"+str(post_id)+".txt","r",encoding="utf-8")
    meta_text=meta.readlines()
    meta.close()
    out_text="*"
    out_text+=meta_text[4].strip()#header
    out_text+="*\n\n"
    out_text+=meta_text[2].strip()+", "+meta_text[3].strip()+"\n"
    out_text+="[(читать на telegra.ph)]("+tgph_url+")\n\n"
    out_text+=s.diary_url_pretty+"p"+str(meta_text[0].strip())+".htm\n\n"
    for x in range(5,len(meta_text)-1):
        out_text+="#"+meta_text[x].replace(" ","\\_")#пробелов быть не должно
    
    tgch_short_file=open("short.txt","w",encoding="utf-8")
    tgch_short_file.write(out_text)
    tgch_short_file.close()
    
    print(out_text)
    
    token=s.tg_channel_token
    chat_id=s.tg_channel_name
    
    tg_channel.init(token,chat_id)
    res=tg_channel.send_text(out_text)
    print(res)
    

def main():
    s.diary_url_mode=3#отдельный пост
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
    #init.create_folders()
    md_post_name,md_post_len=markdown_all_diary(True,post_id)
    print(md_post_name)
    print(md_post_len)
    img_list=download_pics()
    print("IMAGES:")
    print(img_list)

    if md_post_len>s.tg_max_len or len(img_list)>s.tg_max_pics:
        print("Posting to telegraph...")
        time.sleep(s.wait_time)
        url=post_to_tgph(post_id,img_list)
        post_short_to_tgch(post_id,url)
    else:
        print("Posting to channel...")
        time.sleep(s.wait_time)
        post_to_tgch(post_id,img_list,md_post_name)

if __name__=="__main__":
    main()