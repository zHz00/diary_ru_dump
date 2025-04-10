import init
import enum
version=10

uname="zHz00"
session=""

#Замените в следующей настройке мой ник на необходимый
diary_url='https://diary.ru/~zHz00?oam&rfrom='
diary_url_comments='https://diary.ru/~zHz00?sort=last_comment&rfrom='
diary_url_pretty='https://zhz00.diary.ru/'

#diary_url='https://zhz00.diary.ru/?tag=33243&n=t&page='

class dum(enum.Enum):
    full=0
    by_tag=1
    from_file=2
    one_post=3
    newest_comments=4

# 0 -- режим постов -- 20, 40, 60 и т.п.
# 1 -- режим страниц, если скачиваем по тегу, 1, 2, 3 и т.п.
# 2 -- режим файла
# 3 -- режим одного поста
diary_url_mode=dum.full

tg_max_len=6000
tg_max_pics=3
tg_post_len=3500
tg_pic_len=128
tg_max_retries=3
tg_ph_token=""
tg_channel_token=""
tg_channel_name=""

#Нужны ли картинки? (для веселья)
download_pics=True

#Нужны ли исходные html-файлы? (для отладки)
download_html=False
#нужны ли комментарии? (для полноты картины)
download_comments=True

def toggle_pics():
    global download_pics
    download_pics=not download_pics
    change_username()

def toggle_html():
    global download_html
    download_html=not download_html

def toggle_comments():
    global download_comments
    download_comments=not download_comments


#Тут надо придумать шаблон для поиска номеров постов. Если не знаете, что делать, замените "00" на необходимый ник.
link_marks=["00/p","00.diary.ru/p"]

#Аналогично, заменяем мой ник на необходимый.
cross_link_checking=["zHz00.diary.ru/","/~zHz00/","zhz00.diary.ru/","/~zhz00/"]
#Не трогать.
pic_checking=[".jpg",".jpeg",".png",".gif"]

#Для открытых дневников задайте все три ключа как пустые строки. Для закрытых возьмите значения кукисов из своего браузера.
saved_cookies={'_session':''}

#if len(saved_cookies['_session'])<2:
#    links_style=0
#else:
 #   links_style=1
links_style=1


#Диапазон страниц. Минимальный, как правило, 20, при этом первый пост может не попасть в список. Максимальный можно вычислить, зайдя на дневник и посмотрев адреса первой страницы
#Например, при адресе первой страницы https://zhz00.diary.ru/?rfrom=3840 надо выставлять номер 3860, т.е. на 20 больше
start=20
stop=3860

#На ваш выбор.
wait_time=60 #sec

#Тут надо задать название блокнота для Obsidian
base_folder="../zhz00_diary_obsidian/"
#base_folder="../zhz_diary_obsidian_nopics/"
pics_folder="pics/"
pics_duplicate_folder="duplicate/"
pics_censor_folder="censor/"
dump_folder="../zhz00_dump/"
indexes_folder="indexes/"
days_folder="days/"
tags_folder="tags/"
obsidian_settings_folder=".obsidian/"
obsidian_bookmarks_file="bookmarks.json"
obsidian_default_settings_folder="default_obsidian_config/"
test_folder="tests/data/"
temp_md_folder="temp_md/"

#Если скрипты распакованы в папку c:\diary\scripts\, то структура будет такой:
#c:\diary\zhz_diary_obsidian <- тут будут сами посты в формате .md
#c:\diary\zhz_diary_obsidian\pics <- тут будут картинки
#c:\diary\zhz_diary_obsidian\indexes <- тут будет список постов, канедарь и список тегов
#c:\diary\zhz_diary_obsidian\indexes\days <- тут будут вспомогательные файлы для календаря;
# если в какой-либо день создано несколько постов, то для этого дня генерируется отдельный список,
# который будет размещён в этой папке
#c:\diary\zhz_diary_obsidian\tags <- тут будут лежать файлы со списками постов по каждому тегу
#C:\diary\zhz_diary_obsidian\.obsidian <- тут будут лежать настройки обсидиана
#c:\diary\scripts <- сюда сложить питоновские файлы
#c:\diary\zhz00_dump <- тут будут метаданные постов и "сырые" посты в формате html

list_file_name="Список"
list_direct_postfix=" (хронологически).md"
list_reversed_postfix=" (сначала новые).md"
calendar_file_name="Календарь.md"
tags_file_name="Теги"
tags_ab_postfix=" (по алфавиту).md"
tags_n_postfix=" (по количеству).md"
day_list_prefix="AT"

post_list_encoding="utf-8"
post_encoding="utf-8"
settings_file_encoding="utf-8"

forbidden_pic_urls=["google.ru/search?q=","google.com/search?q=","chan.sankakustatic.com","img.rudepedexe1.com","img.totafofesos1.com"]
user_agent = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0 SeaMonkey/2.53.16'}#'Mozilla/5.0'}

settings_file_name="username.txt"
tokens_file_name="tokens.txt"
placeholder_image_name="placeholder.png"
censor_image_name="censor.png"

db_name="posts.db"

def enter_username() -> None:
    uname_local=input("Please enter username:")
    cf_clearance_local=input("Please paste Cloudflare clearance from cookies (name: 'cf_clearance'):")
    session_local=input("Please paste session ID from cookies (name:'_identity_'):")
    settings_file=open(settings_file_name,"w",encoding=settings_file_encoding)
    settings_file.write(uname_local)
    settings_file.write(session_local)
    settings_file.write(cf_clearance_local)
    settings_file.close()
    load_username()

def load_username(postfix:int="") -> None:
    global uname
    global session
    global cf_clearance
    settings_file=open(settings_file_name,"r",encoding=settings_file_encoding)
    uname=settings_file.readline().strip()
    cf_clearance=settings_file.readline().strip()
    session=settings_file.readline().strip()
    settings_file.close()
    change_username(postfix)
    
def load_tokens():
    global tg_ph_token
    global tg_channel_token
    global tg_channel_name
    tokens_file=open(dump_folder+tokens_file_name,"r",encoding=settings_file_encoding)
    tg_ph_token=tokens_file.readline().strip()
    tg_channel_token=tokens_file.readline().strip()
    tg_channel_name=tokens_file.readline().strip()
    print("Len of telegraph token: "+str(len(tg_ph_token)))
    print("Len of bot token: "+str(len(tg_channel_token)))
    print("Loaded channel name: "+tg_channel_name)


def change_username(postfix:str="") -> None:
    global diary_url
    global diary_url_comments
    global link_marks
    global cross_link_checking
    global base_folder
    global dump_folder
    global links_style
    diary_url='https://diary.ru/~'+uname+'?oam&rfrom='
    diary_url_comments='https://diary.ru/~'+uname+'?sort=last_comment&rfrom='
    link_marks=[uname+"/p",uname+".diary.ru/p"]
    cross_link_checking=[uname+".diary.ru/","/~"+uname+"/"]
    saved_cookies['_identity_']=session
    saved_cookies['cf_clearance']=cf_clearance

    if diary_url_mode==dum.one_post:
        base_folder="../"+uname+postfix+"_diary_obsidian/"
        dump_folder="../"+uname+postfix+"_dump/"
    else:
        dump_folder="../"+uname+postfix+"_dump/"
        if download_pics:
            base_folder="../"+uname+postfix+"_diary_obsidian/"
        else:
            base_folder="../"+uname+postfix+"_diary_obsidian_nopics/"


#    if len(saved_cookies['_session'])<2:
#        links_style=0
#    else:
#        links_style=1
    links_style=1

    init.create_folders()
