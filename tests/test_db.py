import db


def test_connect():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res==0
    db.close()
def test_adding_posts():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted
    res=db.add_post(100,"test","2001-01-01","test time2","title2",6,[("Случай из жизни",3)],"это что такое?")
    assert res==db.db_ret.inserted
    res=db.add_post(100,"test","2001-01-01","test time2","title2",7,[("Случай из жизни",3)],"это что такое?")
    assert res==db.db_ret.updated_comments_n_changed
    res=db.add_post(100,"test_changed","2002-02-02","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое? изменено")
    assert res==db.db_ret.updated_comments_n_identical
    #реальное число в бд равно нулю, поэтому надо передать ноль чтобы получить такое возвращаемое значение
    
    #проверка, как там добавилось
    list=db.get_posts_list(reversed=True)
    assert list==[100,1]
    list=db.get_posts_list()
    assert list==[1,100]

    text=db.get_post_contents(1)
    assert text=="Тестовое содержание"
    date,time=db.get_post_date_time(1)
    assert date=="2001-01-01"
    assert time=="test time"
    #text=db.get_post_fname(1)#fname надо проверять при добавлении ссылок
    #assert text=="title"
    text=db.get_post_title(1)
    assert text=="title"
    text=db.get_post_url(1)
    assert text=="test"
    list=db.get_post_tags(1)
    assert list==["Аниме","Дзякиган","Случай из жизни"]

    text=db.get_post_contents(100)
    assert text=="это что такое? изменено"
    date,time=db.get_post_date_time(100)
    assert date=="2002-02-02"
    assert time=="test time2"
    #text=db.get_post_fname(1)#fname надо проверять при добавлении ссылок
    #assert text=="title"
    text=db.get_post_title(100)
    assert text=="title2"
    text=db.get_post_url(100)
    assert text=="test_changed"
    list=db.get_post_tags(100)
    assert list==["Аниме","Дзякиган","Автомобили"]

    db.close()

def test_adding_links():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted

    res=db.add_link(1,"TEST",2,"https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_link(1,"TEST",1,"https://example2.com")
    assert res==db.db_ret.inserted
    res=db.add_link(1,"TEST",2,"https://example.com")
    assert res==db.db_ret.already_exists
    res=db.add_link(2,"TEST",-1,"https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_link(2,"TEST",1,"https://example.com")
    assert res==db.db_ret.already_exists
    res=db.add_link(222002696,"TEST",222002696,"https://zhz00.diary.ru/p222002696_jeto-ne-slyozy-jeto-prosto-dozhd.htm")
    assert res==db.db_ret.inserted
    res=db.add_link(222002696,"TEST2",222002696,"https://zhz00.diary.ru/p222002696_dsfghertdyg.htm")
    assert res==db.db_ret.already_exists
    res=db.add_link(218943387,"Список моих статей (обновлено 20221028)",218943387,"https://diary.ru/~zHz00/p218943387_spisok-moih-statej-obnovleno-2022-10-28.htm")
    assert res==db.db_ret.inserted
    res=db.add_link(218943387,"Список моих статей (обновлено 20240509)",218943387,"https://diary.ru/~zHz00/p218943387_spisok-moih-statej-obnovleno-2024-05-09.htm")
    assert res==db.db_ret.already_exists

    list=db.get_links_list_dict()#ссылки сами на себя тут пропускаются
    assert len(list)==2

    assert list[0]=={'SRC_POST_FNAME': 'TEST', 'SRC_URL': 'https://example.com', 'DEST_POST_FNAME': 'TEST', 'SRC_DEST_POST_ID': 2}
    assert list[1]=={'SRC_POST_FNAME': 'TEST', 'SRC_URL': 'https://example.com', 'DEST_POST_FNAME': None, 'SRC_DEST_POST_ID': -1}

    text=db.get_post_fname(1)
    assert text=="TEST"

    list=db.get_links_list_plain()
    assert len(list)==5
    assert list==["https://example.com","https://example2.com","https://example.com","https://zhz00.diary.ru/p222002696_dsfghertdyg.htm","https://diary.ru/~zHz00/p218943387_spisok-moih-statej-obnovleno-2024-05-09.htm"]

    db.close()

def test_adding_pics():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted

    res=db.add_pic(1,"TEST","https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_pic(1,"TEST","https://example.com")
    assert res==db.db_ret.already_exists
    res=db.add_pic(2,"TEST","https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_pic(2,"TEST","https://example.com")
    assert res==db.db_ret.already_exists

    list=db.get_pics_list_dict()
    assert len(list)==2
    assert list[0]=={'POST_ID': 1, 'POST_FNAME': 'TEST', 'URL': 'https://example.com'}
    assert list[1]=={'POST_ID': 2, 'POST_FNAME': 'TEST', 'URL': 'https://example.com'}

    list=db.get_pics_list_plain()
    assert len(list)==2
    assert list==["https://example.com","https://example.com"]

    db.close()

def test_search():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted
    res=db.add_post(100,"test_changed","2002-02-02","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое? изменено")
    assert res==db.db_ret.inserted
    
    text=db.get_tag_name_by_diary_id(2)
    assert text=="Дзякиган"
    text=db.get_tag_name_by_diary_id(100)
    assert text==""

    list=db.get_tags_list()
    assert len(list)==4
    assert list==["Автомобили","Аниме","Дзякиган","Случай из жизни"]

    list=db.get_posts_list_at_tag("Аниме")
    assert len(list)==2
    assert list==[1,100]

    list=db.get_posts_list_at_tag("Автомобили")
    assert len(list)==1
    assert list==[100]

    list=db.get_posts_list_at_tag("Мура")
    assert len(list)==0

    list=db.get_posts_list_at_date("test_date")
    assert len(list)==0

    list=db.get_posts_list_at_date("2002-02-02")
    assert len(list)==1
    assert list==[100]

    list=db.get_posts_by_contents("Тестовое")
    assert len(list)==1
    assert list==[1]

    list=db.get_posts_by_contents("test3")
    assert len(list)==0

    db.close()

def test_adding_comments():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted

    res=db.add_comment(1,100,"2001-01-01","time1","Гость","test")
    assert res==db.db_ret.inserted
    res=db.add_comment(2,100,"2002-01-01","time2","Гость","test")
    assert res==db.db_ret.inserted
    res=db.add_comment(3,100,"2003-01-01","time3","Гость","test")
    assert res==db.db_ret.inserted
    res=db.add_comment(4,100,"2003-01-01","time4","Гость","test")
    assert res==db.db_ret.inserted
    res=db.add_comment(4,100,"2001-01-01","time2","Гость2","test2")#обновляется автор и содержимое. дата и время не обновляются!
    assert res==db.db_ret.updated

    #===============================================================
    d,t=db.get_comment_date_time(1)
    assert d=="2001-01-01"
    assert t=="time1"
    a=db.get_comment_author(1)
    assert a=="Гость"
    c=db.get_comment_contents(1)
    assert c=="test"
    d=t=a=c=None
    assert d==None
    assert t==None
    assert a==None
    assert c==None

    d,t=db.get_comment_date_time(2)
    assert d=="2002-01-01"
    assert t=="time2"
    a=db.get_comment_author(2)
    assert a=="Гость"
    c=db.get_comment_contents(2)
    assert c=="test"
    d=t=a=c=None
    assert d==None
    assert t==None
    assert a==None
    assert c==None

    d,t=db.get_comment_date_time(3)
    assert d=="2003-01-01"
    assert t=="time3"
    a=db.get_comment_author(3)
    assert a=="Гость"
    c=db.get_comment_contents(3)
    assert c=="test"
    d=t=a=c=None
    assert d==None
    assert t==None
    assert a==None
    assert c==None

    d,t=db.get_comment_date_time(4)#обновляется автор и содержимое. дата и время не обновляются!
    assert d=="2003-01-01"
    assert t=="time4"
    a=db.get_comment_author(4)
    assert a=="Гость2"
    c=db.get_comment_contents(4)
    assert c=="test2"
    d=t=a=c=None
    assert d==None
    assert t==None
    assert a==None
    assert c==None
    #===============================================================

    i=db.get_comments_n(100)
    assert i==0
    
    i=db.get_comments_downloaded(100)
    assert i==4

    res=db.mark_deleted_comment(3)
    assert res==db.db_ret.comments_n_negative

    res=db.get_comments_downloaded(100)
    assert i==4

    res=db.update_comments_n(100,4)
    assert res==db.db_ret.updated

    res=db.mark_deleted_comment(3)
    assert res==db.db_ret.updated
    i=db.get_comments_downloaded(100)
    assert i==3
    i=db.get_comments_n(100)
    assert i==3

    res=db.mark_deleted_comment(3)#повторный вызов должен работать корректно
    assert res==db.db_ret.not_changed
    i=db.get_comments_downloaded(100)
    assert i==3

    res=db.mark_not_spam_comment(4)
    assert res==db.db_ret.updated
    #данный коммент должен отсутствовать в списке спама

    list=db.get_spam_comments(300)
    assert len(list)==1

    c=list[0]
    assert c["COMMENT_ID"]==2
    assert c["POST_ID"]==100
    assert c["C_DATE"]=="2002-01-01"
    assert c["P_DATE"]=="2001-01-01"
    assert c["DIFF"]==365.0
    assert c["TITLE"]=="title2"
    assert c["CONTENTS"]=="test"
    
    list=db.get_comments_list(100)
    assert len(list)==4
    assert list==[1,2,3,4]

    list=db.get_comments_list(100,deleted=True)
    assert len(list)==4
    assert list==[1,2,3,4]

    list=db.get_comments_list(100,deleted=False)
    assert len(list)==3
    assert list==[1,2,4]

    db.close()