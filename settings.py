diary_url='https://diary.ru/~zHz00?oam&rfrom='
link_marks=["00/p","00.diary.ru/p"]
post_id_len=9

cross_link_checking=["zHz00.diary.ru/","/~zHz00/","zhz00.diary.ru/","/~zhz00/"]
pic_checking=[".jpg",".jpeg",".png",".gif"]

saved_cookies={'_csrf':'-',
'_session':'-',
'_identity':'-'}



start=120
stop=160

wait_time=60 #sec

base_folder="../diary_zhz_obsidian/"
pics_folder="../pics/"
dump_folder="../dump\\"

pics_file="pics.txt"
links_file="links.txt"

pics_file_encoding="utf-8"
links_file_encoding="utf-8"
post_list_encoding="utf-8"
post_encoding="utf-8"

forbidden_pic_urls=["google.ru/search?q=","google.com/search?q=","chan.sankakustatic.com","img.rudepedexe1.com","img.totafofesos1.com"]
user_agent = {'User-agent': 'Mozilla/5.0'}