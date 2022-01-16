version=3

#Замените в следующей настройке мой ник на необходимый
diary_url='https://diary.ru/~zHz00?oam&rfrom='
#diary_url='https://zhz00.diary.ru/?tag=33243&n=t&page='

# 0 -- режим постов -- 20, 40, 60 и т.п.
# 1 -- режим страниц, если скачиваем по тегу, 1, 2, 3 и т.п.
diary_url_mode=0

#Нужны ли картинки?
download_pics=True


#Тут надо придумать шаблон для поиска номеров постов. Если не знаете, что делать, замените "00" на необходимый ник.
link_marks=["00/p","00.diary.ru/p"]

#Аналогично, заменяем мой ник на необходимый.
cross_link_checking=["zHz00.diary.ru/","/~zHz00/","zhz00.diary.ru/","/~zhz00/"]
#Не трогать.
pic_checking=[".jpg",".jpeg",".png",".gif"]

#Для открытых дневников задайте все три ключа как пустые строки. Для закрытых возьмите значения кукисов из своего браузера.
saved_cookies={'_csrf':'',
'_session':'',
'_identity_':''}

if len(saved_cookies['_csrf'])<2:
    links_style=0
else:
    links_style=1


#Диапазон страниц. Минимальный, как правило, 20, при этом первый пост может не попасть в список. Максимальный можно вычислить, зайдя на дневник и посмотрев адреса первой страницы
#Например, при адресе первой страницы https://zhz00.diary.ru/?rfrom=3840 надо выставлять номер 3860, т.е. на 20 больше
start=20
stop=3860

#На ваш выбор.
wait_time=60 #sec

#Тут надо задать название блокнота для Obsidian
base_folder="../zhz_diary_obsidian/"
#base_folder="../zhz_diary_obsidian_nopics/"
pics_folder="pics/"
dump_folder="../dump\\"
indexes_folder="indexes/"
days_folder="days/"
tags_folder="tags/"
obsidian_settings_folder=".obsidian/"
obsidian_default_settings_folder="default_obsidian_config/"

#Если скрипты распакованы в папку c:\diary\scripts\, то структура будет такой:
#c:\diary\zhz_diary_obsidian <- тут будут сами посты в формате .md
#c:\diary\zhz_diary_obsidian\pics <- тут будут картинки
#c:\diary\zhz_diary_obsidian\indexes <- тут будет список постов, канедарь и список тегов
#c:\diary\zhz_diary_obsidian\indexes\days <- тут будут вспомогательные файлы для календаря; если в какой-либо день создано несколько постов, то для этого дня генерируется отдельный список, который будет размещён в этой папке
#c:\diary\zhz_diary_obsidian\tags <- тут будут лежать файлы с тегами, и со списками постов по каждому тегу
#C:\diary\zhz_diary_obsidian\.obsidian <- тут будут лежать настройки обсидиана
#c:\diary\scripts <- сюда сложить питоновские файлы
#c:\diary\dump <- тут будут метаданные постов и "сырые" посты в формате html

pics_file="pics.txt"
links_file="links.txt"

list_file_name="Список.md"
calendar_file_name="Календарь.md"
tags_file_name="Теги.md"
day_list_prefix="AT"

pics_file_encoding="utf-8"
links_file_encoding="utf-8"
post_list_encoding="utf-8"
post_encoding="utf-8"

forbidden_pic_urls=["google.ru/search?q=","google.com/search?q=","chan.sankakustatic.com","img.rudepedexe1.com","img.totafofesos1.com"]
user_agent = {'User-agent': 'Mozilla/5.0'}