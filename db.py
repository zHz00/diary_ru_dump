import sqlite3 as sl
import settings as s
import os
import enum
import re
import logging as l

db_link=None
db_cursor=None

class db_ret(enum.Enum):
    unknown=0
    inserted=1
    updated=2
    already_exists=3
    created=4
    connected=5
    updated_comments_n_changed=6
    updated_comments_n_identical=7
    comments_n_negative=8
    not_changed=9

def connect(create=True):
    global db_link
    global db_cursor

    l.info("DB: "+s.dump_folder+s.db_name)

    if db_link is not None:
        l.info("DB: already connected!")
        return db_ret.already_exists

    if not os.path.isfile(s.dump_folder+s.db_name):
        l.info("DB: need creation")
        need_creation=True
    else:
        l.info("DB: already exist")
        need_creation=False

    db_link=sl.connect(s.dump_folder+s.db_name)
    db_link.row_factory = sl.Row
    db_cursor=db_link.cursor()

    if(need_creation and create):
        create_db()
        return db_ret.created
    else:
        return db_ret.connected

def create_db():
    global db_link
    global db_cursor
    if db_link is None:
        connect(False)
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS TAGS
    (
        TAG_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        TAG_DIARY_ID INTEGER,
        TAG TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS POSTS
    (
        POST_ID INTEGER PRIMARY KEY,
        URL TEXT,
        DATE TEXT,
        TIME TEXT,
        TITLE TEXT,
        COMMENTS_N INTEGER,
        CONTENTS TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS TAGS_LINKED
    (
        POST_ID INTEGER,
        TAG_ID INTEGER
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS COMMENTS
    (
        COMMENT_ID INTEGER PRIMARY KEY,
        POST_ID INTEGER,
        DATE TEXT,
        TIME TEXT,
        AUTHOR TEXT,
        DELETED INTEGER,
        NOT_SPAM INTEGER,
        CONTENTS TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS PICS
    (
        POST_ID INTEGER,
        POST_FNAME TEXT,
        URL TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS LINKS
    (
        POST_ID INTEGER,
        POST_FNAME TEXT,
        DEST_POST_ID INTEGER,
        URL TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE INDEX IF NOT EXISTS TAGS_LINKED_INDEX
    ON TAGS_LINKED(POST_ID)
    ''')
    db_cursor.execute('''
    CREATE INDEX IF NOT EXISTS TAGS_INDEX
    ON TAGS_LINKED(TAG_ID)
    ''')    
    db_cursor.execute('''
    CREATE INDEX IF NOT EXISTS COMMENTS_INDEX
    ON COMMENTS(POST_ID)
    ''')
    db_link.commit()
    
def check_connection():
    global db_cursor
    global db_link
    if db_cursor is None:
        return 1
    if db_link is None:
        return 2
    db_cursor.execute('''SELECT count(*) as tcount FROM sqlite_master WHERE type = 'table' AND name != 'android_metadata' AND name != 'sqlite_sequence'
    ''')
    tables=db_cursor.fetchone()["tcount"]
    if tables!=6:
        print(f"tables={tables}")
        return 3
    db_cursor.execute('''SELECT count(*) as icount FROM sqlite_master WHERE type = 'index'
    ''')
    indexes=db_cursor.fetchone()["icount"]
    if indexes!=3:
        print(f"indexes={indexes}")
        return 4
    return 0




def add_post(post_id,url,date,time,title,comments_n,tags,contents):
    global db_cursor
    global db_link
    res=db_ret.unknown
    db_cursor.execute('''
    SELECT * FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    found=db_cursor.fetchall()
    if(len(found)>0):
        #пост найден, надо его обновить
        comments_n_old=get_comments_downloaded(post_id)
        db_cursor.execute('''UPDATE POSTS SET
        (POST_ID,URL,DATE,TIME,TITLE,COMMENTS_N,CONTENTS)=
        (?,?,?,?,?,?,?)
        WHERE POST_ID=(?)''',(post_id,url,date,time,title,comments_n,contents,post_id))
        print(f"id:{post_id}, old:{comments_n_old}, new:{comments_n}")
        if comments_n_old==int(comments_n):
            res=db_ret.updated_comments_n_identical
        else:
            res=db_ret.updated_comments_n_changed
    else:
        db_cursor.execute('''INSERT INTO POSTS 
        (POST_ID,URL,DATE,TIME,TITLE,COMMENTS_N,CONTENTS)
        VALUES
        (?,?,?,?,?,?,?)''',(post_id,url,date,time,title,comments_n,contents))
        res=db_ret.inserted

    #теперь пробивает таблицу тегов
    db_cursor.execute('''
    DELETE FROM TAGS_LINKED WHERE POST_ID=(?)
    ''',(post_id,))#чтобы не было дублей
    for tag in tags:
        db_cursor.execute('''
        SELECT * FROM TAGS WHERE TAG=(?)
        ''',(tag[0],))
        tag_db=db_cursor.fetchall()
        if len(tag_db)>0:
            db_cursor.execute('''
            INSERT INTO TAGS_LINKED (POST_ID,TAG_ID) VALUES (?,?)
            ''',(post_id,tag_db[0]['TAG_ID']))
        else:
            db_cursor.execute('''
            INSERT INTO TAGS (TAG,TAG_DIARY_ID) VALUES (?,?)
            ''',(tag[0],tag[1]))
            db_cursor.execute('''
            SELECT * FROM TAGS WHERE TAG=(?)
            ''',(tag[0],))
            tag_db=db_cursor.fetchall()
            db_cursor.execute('''
            INSERT INTO TAGS_LINKED (POST_ID,TAG_ID) VALUES (?,?)
            ''',(post_id,tag_db[0]['TAG_ID']))
    db_link.commit()
    return res

def add_pic(post_id,post_fname,url):
    global db_cursor
    res=db_ret.unknown
    db_cursor.execute('''
    SELECT * FROM PICS WHERE POST_ID=(?) AND URL=(?)
    ''',(post_id,url))#проверяем только ИД поста, а имя файла не проверяем. рано или поздно это может привести к проблемам!
    #UPD. И уже привело. Теперь при наличии строки я обновляю имя файла, потому что оно, вообще-то, могло измениться!
    if len(db_cursor.fetchall())==0:
        db_cursor.execute('''
        INSERT INTO PICS (POST_ID,POST_FNAME,URL) VALUES (?,?,?)
        ''',(post_id,post_fname,url))
        res=db_ret.inserted
    else:
        db_cursor.execute('''
        UPDATE PICS SET POST_FNAME=(?) 
        WHERE POST_ID=(?) AND URL=(?)
        ''',(post_fname,post_id,url))
        res=db_ret.already_exists
    db_link.commit()
    return res

def add_link(post_id,post_fname,dest_post_id,url):
    global db_cursor
    db_cursor.execute('''
    SELECT * FROM LINKS WHERE POST_ID=(?)
    ''',(post_id,))#проверяем только ИД поста, а имя файла не проверяем. рано или поздно это может привести к проблемам!
    #UPD. И уже привело. Теперь при наличии строки я обновляю имя файла, потому что оно, вообще-то, могло измениться!
    #UPD2. оказалось что недостаточно текущих мер (проверки ИД и урла), т.к. при изменении имени поста изменяется и его урл!
    fetch=db_cursor.fetchall()
    find_pattern="diary.ru/"
    for link in fetch:
        dest_post_id_match=re.search("\\/p(\\d+)",link['URL'][link['URL'].find(find_pattern):])
        if dest_post_id_match is not None:
            dest_post_id_db_str=dest_post_id_match.group(0)[2:]
            if dest_post_id_db_str.isdecimal():
                dest_post_id_db_int=int(dest_post_id_db_str)
            else:
                dest_post_id_db_int=-2
        else:
            dest_post_id_db_int=-2
        if dest_post_id==dest_post_id_db_int or url==link['URL']:#уже есть ссылка, надо обновить данные
            db_cursor.execute('''
            UPDATE LINKS SET POST_FNAME=(?), URL=(?)
            WHERE POST_ID=(?) AND URL=(?)
            ''',(post_fname,url,post_id,link['URL']))
            db_link.commit()
            return db_ret.already_exists

    db_cursor.execute('''
    INSERT INTO LINKS (POST_ID,POST_FNAME,DEST_POST_ID,URL) VALUES (?,?,?,?)
    ''',(post_id,post_fname,dest_post_id,url))
    
    db_link.commit()
    return db_ret.inserted


def get_post_contents(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT CONTENTS FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    return db_cursor.fetchone()['CONTENTS']

def get_post_title(post_id:int) -> str:#конкрнетно для данной функции сделано, чтобы она корректно работала при отсутствии поста
    #такое надо сделать для всех но пока нету. у этой функции сделано, т.к. она используется для проверки существования поста
    global db_cursor
    db_cursor.execute('''SELECT TITLE FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    fetch=db_cursor.fetchone()
    if fetch==None:
        return None
    else:
        return fetch['TITLE']

def get_post_url(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT URL FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    return db_cursor.fetchone()['URL']

def get_post_date_time(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT DATE,TIME FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    fetch=db_cursor.fetchone()
    return (fetch['DATE'],fetch['TIME'])

def get_post_tags(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT TAG FROM TAGS_LINKED LEFT JOIN TAGS ON TAGS_LINKED.TAG_ID=TAGS.TAG_ID WHERE TAGS_LINKED.POST_ID=(?)
    ''',(post_id,))
    tags=[]
    for row in db_cursor.fetchall():
        tags.append(row['TAG'])
    return tags

def get_post_fname(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT DISTINCT LINKS.POST_FNAME 
    FROM POSTS LEFT JOIN LINKS 
    ON POSTS.POST_ID=LINKS.POST_ID 
    WHERE POSTS.POST_ID=(?)  AND LINKS.DEST_POST_ID=(?)
    ''',(post_id,post_id))#дублирование нужно чтобы найти именно ссылку поста самого на себя. иначе можно найти устаревшие ссылки оставшиеся после редактирования постов
    #тут долгая история, срабатывает на посте "Список моих статией" после того, как я отредактировал там список тегов
    #из за этого в базу попали новые строчки со ссылками, а старые не удалилилсь (не придумал, как алгоритмически выяснить необходимость их удаления)
    #ну и вот, если не сравнивать LINKS.DEST_POST_ID, то выскочит и старое имя поста и новое. первым в списке будет старое, из-за чего при генерациии индексов будут
    #битые ссылки
    return db_cursor.fetchone()['POST_FNAME']

def get_posts_list(reversed=False):
    global db_cursor
    if reversed:
        db_cursor.execute('''
        SELECT POST_ID,DATE,TIME 
        FROM POSTS 
        ORDER BY DATE DESC,TIME DESC
        ''')
    else:
        db_cursor.execute('''
        SELECT POST_ID,DATE,TIME 
        FROM POSTS 
        ORDER BY DATE ASC,TIME ASC
        ''')
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(int(id['POST_ID']))
    return list

def get_posts_list_at_date(date):
    global db_cursor
    db_cursor.execute('''
    SELECT POST_ID,DATE,TIME 
    FROM POSTS
    WHERE DATE=(?)
    ORDER BY DATE,TIME
    ''',(date,))
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(int(id['POST_ID']))
    return list

def get_posts_list_at_tag(tag):
    global db_cursor
    db_cursor.execute('''
    SELECT POSTS.POST_ID
    FROM POSTS LEFT JOIN TAGS_LINKED
    ON POSTS.POST_ID=TAGS_LINKED.POST_ID
    LEFT JOIN TAGS
    ON TAGS_LINKED.TAG_ID=TAGS.TAG_ID
    WHERE TAG=(?)
    ORDER BY DATE,TIME
    ''',(tag,))
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(int(id['POST_ID']))
    return list

def get_pics_list_plain(post_id=-1):
    global db_cursor
    if post_id==-1:
        db_cursor.execute('''
        SELECT URL FROM PICS
        ''')
    else:
        db_cursor.execute('''
        SELECT URL FROM PICS
        WHERE POST_ID=(?)
        ''',(post_id,))
    fetch=db_cursor.fetchall()
    list=[]
    for pic in fetch:
        list.append(pic['URL'])
    return list

def get_links_list_plain(post_id=-1):
    global db_cursor
    if post_id==-1:
        db_cursor.execute('''
        SELECT URL FROM LINKS
        ''')
    else:
        db_cursor.execute('''
        SELECT URL FROM LINKS
        WHERE POST_ID=(?)
        ''',(post_id,))
    fetch=db_cursor.fetchall()
    list=[]
    for link in fetch:
        list.append(link['URL'])
    return list

def get_pics_list_dict():
    global db_cursor
    db_cursor.execute('''
    SELECT * FROM PICS
    ''')
    fetch=db_cursor.fetchall()
    list=[]
    for pic in fetch:
        pic_dict={}
        pic_dict['POST_ID']=pic['POST_ID']
        pic_dict['POST_FNAME']=pic['POST_FNAME']
        pic_dict['URL']=pic['URL']
        #может можно было просто сделать аппенд пик и всё заработало бы, но я знаю, что роу фэктори это не совсем словарь
        #так что на всякий случай пусть будет так
        list.append(pic_dict)
    return list

def get_links_list_dict():
    global db_cursor
    db_cursor.execute('''
    SELECT DISTINCT
        SRC.POST_FNAME AS SRC_POST_FNAME,
        SRC.URL AS SRC_URL,
        DEST.POST_FNAME AS DEST_POST_FNAME,
        SRC.DEST_POST_ID AS SRC_DEST_POST_ID
    FROM LINKS SRC LEFT JOIN LINKS DEST 
    ON SRC.DEST_POST_ID=DEST.POST_ID 
    WHERE SRC.POST_ID<>SRC.DEST_POST_ID
    ''')
    fetch=db_cursor.fetchall()
    list=[]
    for link in fetch:
        link_dict={}
        link_dict['SRC_POST_FNAME']=link['SRC_POST_FNAME']
        link_dict['SRC_URL']=link['SRC_URL']
        link_dict['DEST_POST_FNAME']=link['DEST_POST_FNAME']
        link_dict['SRC_DEST_POST_ID']=int(link['SRC_DEST_POST_ID'])
        #может можно было просто сделать аппенд пик и всё заработало бы, но я знаю, что роу фэктори это не совсем словарь
        #так что на всякий случай пусть будет так
        list.append(link_dict)
    return list


def get_tags_list():
    global db_cursor
    db_cursor.execute('''
    SELECT TAG FROM TAGS
    ORDER BY TAG
    ''')
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(id['TAG'])
    return list

def get_comments_list(post_id:int,deleted:bool=True):
    global db_cursor
    if deleted:
        db_cursor.execute('''SELECT COMMENT_ID FROM COMMENTS
        WHERE POST_ID=(?)
        ''',(post_id,))
    else:
        db_cursor.execute('''SELECT COMMENT_ID FROM COMMENTS
        WHERE POST_ID=(?) AND
        DELETED=0
        ''',(post_id,))
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(id['COMMENT_ID'])
    return list    
    

def get_comments_n(post_id:int) -> int:
    global db_cursor
    db_cursor.execute('''SELECT COMMENTS_N FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    return db_cursor.fetchone()['COMMENTS_N']   

def get_comments_downloaded(post_id:int) -> int:
    global db_cursor
    db_cursor.execute('''SELECT COUNT (*) 
    AS COMMENTS_N_DOWNLOADED 
    FROM COMMENTS 
    WHERE POST_ID=(?) AND DELETED=0
    ''',(post_id,))
    return db_cursor.fetchone()['COMMENTS_N_DOWNLOADED']   

def add_comment(comment_id:int,post_id:int,date:str,time:str,author:str,contents:str):
    global db_cursor
    global db_link
    db_cursor.execute('''SELECT * FROM COMMENTS WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    if db_cursor.fetchone()==None:
        db_cursor.execute('''INSERT INTO COMMENTS (COMMENT_ID,POST_ID,DATE,TIME,AUTHOR,DELETED,NOT_SPAM,CONTENTS)
        VALUES ((?),(?),(?),(?),(?),0,0,(?))
        ''',(comment_id,post_id,date,time,author,contents))
        res=db_ret.inserted
        db_link.commit()
        return res
    else:
        db_cursor.execute('''UPDATE COMMENTS SET (AUTHOR,DELETED,CONTENTS)=((?),0,(?))
        WHERE COMMENT_ID=(?)
        ''',(author,contents,comment_id))
        res=db_ret.updated
        db_link.commit()
        return res
    
def mark_deleted_comment(comment_id):
    global db_cursor
    global db_link
    db_cursor.execute('''SELECT DELETED FROM COMMENTS WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    already_deleted=db_cursor.fetchone()["DELETED"]
    if already_deleted==1:
        return db_ret.not_changed
    db_cursor.execute('''UPDATE COMMENTS SET DELETED=1 WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    db_cursor.execute('''SELECT POST_ID FROM COMMENTS WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    post_id=db_cursor.fetchone()["POST_ID"]
    db_cursor.execute('''SELECT COMMENTS_N FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    comments_n=db_cursor.fetchone()["COMMENTS_N"]
    comments_n-=1
    if comments_n<0:
        res=db_ret.comments_n_negative
        db_link.rollback()
        return res
    else:
        db_cursor.execute('''UPDATE POSTS SET COMMENTS_N=(?) WHERE POST_ID=(?)
        ''',(comments_n,post_id))

    res=db_ret.updated
    db_link.commit()
    return res

def mark_not_spam_comment(comment_id):
    global db_cursor
    global db_link
    db_cursor.execute('''UPDATE COMMENTS SET NOT_SPAM=1 WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    res=db_ret.updated
    db_link.commit()
    return res

def update_comments_n(post_id:int,n:int):
    global db_cursor
    global db_link
    db_cursor.execute('''UPDATE POSTS SET COMMENTS_N=(?) WHERE POST_ID=(?)
    ''',(n,post_id))
    res=db_ret.updated
    db_link.commit()
    return res

def get_comment_date_time(comment_id):
    global db_cursor
    db_cursor.execute('''SELECT DATE,TIME FROM COMMENTS WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    res=db_cursor.fetchone()
    return (res['DATE'],res['TIME'])

def get_comment_author(comment_id):
    global db_cursor
    db_cursor.execute('''SELECT AUTHOR FROM COMMENTS WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    return (db_cursor.fetchone()['AUTHOR'])

def get_comment_contents(comment_id):
    global db_cursor
    db_cursor.execute('''SELECT CONTENTS FROM COMMENTS WHERE COMMENT_ID=(?)
    ''',(comment_id,))
    return (db_cursor.fetchone()['CONTENTS'])

def get_spam_comments(age:int):
    global db_cursor
    db_cursor.execute('''
        SELECT
            COMMENT_ID,
            COMMENTS.POST_ID,
            COMMENTS.DATE AS C_DATE, 
            POSTS.DATE AS P_DATE,
            (JULIANDAY(COMMENTS.DATE)-JULIANDAY(POSTS.DATE)) AS DIFF,
            POSTS.TITLE,
            COMMENTS.CONTENTS 
        FROM COMMENTS LEFT JOIN POSTS ON COMMENTS.POST_ID=POSTS.POST_ID 
        WHERE AUTHOR="Гость" AND DIFF>(?) AND NOT_SPAM=0 AND DELETED=0
        ORDER BY DIFF DESC
    ''',(age,))
    list=[]
    for fetch in db_cursor.fetchall():
        list.append(fetch)
    return list

def get_tag_name_by_diary_id(diary_tag_id:int)->str:
    global db_cursor
    db_cursor.execute('''
        SELECT TAG FROM TAGS
        WHERE TAG_DIARY_ID=(?)
    ''',(diary_tag_id,))
    fetch=db_cursor.fetchone()
    if fetch is None:
        return ""
    return fetch['TAG']

def get_posts_by_contents(substr:str):
    global db_cursor
    db_cursor.execute('''
        SELECT POST_ID
        FROM POSTS
        WHERE CONTENTS LIKE (?)
    ''',('%'+substr+'%',))
    list=[]
    for fetch in db_cursor.fetchall():
        list.append(fetch['POST_ID'])
    return list



def reset_db(db_name=""):
    if db_name!="":
        s.db_name=db_name
    if os.path.exists(s.dump_folder+s.db_name):
        os.remove(s.dump_folder+s.db_name)
    create_db()

def reset_posts():
    global db_cursor
    db_cursor.execute('''
    DELETE FROM POSTS
    ''')#delete all

"""

"""

def compare_with_other_db(second_db:str)->dict():
    global db_cursor
    global db_link

    report=dict()

    db_cursor.execute("ATTACH ? AS DB2",(second_db,))

    db_cursor.execute("SELECT * FROM main.POSTS EXCEPT SELECT * FROM DB2.POSTS ORDER BY main.POSTS.POST_ID")
    fetch=db_cursor.fetchall()
    print("posts 1-2. diff len="+str(len(fetch)))
    list12=[]
    for i in fetch:
        list12.append(i["POST_ID"])

    db_cursor.execute("SELECT * FROM DB2.POSTS EXCEPT SELECT * FROM main.POSTS ORDER BY DB2.POSTS.POST_ID")
    fetch=db_cursor.fetchall()
    print("posts 2-1. diff len="+str(len(fetch)))
    list21=[]
    for i in fetch:
        list21.append(i["POST_ID"])

    report["POSTS"]=[list12,list21]

    #==================================================================================
    db_cursor.execute("SELECT * FROM main.TAGS EXCEPT SELECT * FROM DB2.TAGS ORDER BY main.TAGS.TAG_ID")
    fetch=db_cursor.fetchall()
    print("tags 1-2. diff len="+str(len(fetch)))
    list12=[]
    for i in fetch:
        list12.append(i["TAG_ID"])

    db_cursor.execute("SELECT * FROM DB2.TAGS EXCEPT SELECT * FROM main.TAGS ORDER BY DB2.TAGS.TAG_ID")
    fetch=db_cursor.fetchall()
    print("tags 2-1. diff len="+str(len(fetch)))
    list21=[]
    for i in fetch:
        list21.append(i["TAG_ID"])

    report["TAGS"]=[list12,list21]

    #==================================================================================
    db_cursor.execute("SELECT * FROM main.TAGS_LINKED EXCEPT SELECT * FROM DB2.TAGS_LINKED ORDER BY main.TAGS_LINKED.POST_ID")
    fetch=db_cursor.fetchall()
    print("tags_linked 1-2. diff len="+str(len(fetch)))
    list12=[]
    for i in fetch:
        list12.append(i["POST_ID"])

    db_cursor.execute("SELECT * FROM DB2.TAGS_LINKED EXCEPT SELECT * FROM main.TAGS_LINKED ORDER BY DB2.TAGS_LINKED.POST_ID")
    fetch=db_cursor.fetchall()
    print("tags_linked 2-1. diff len="+str(len(fetch)))
    list21=[]
    for i in fetch:
        list21.append(i["POST_ID"])

    report["TAGS_LINKED"]=[list12,list21]

    #==================================================================================
    db_cursor.execute("SELECT * FROM main.PICS EXCEPT SELECT * FROM DB2.PICS ORDER BY main.PICS.URL")
    fetch=db_cursor.fetchall()
    print("pics 1-2. diff len="+str(len(fetch)))
    list12=[]
    for i in fetch:
        list12.append(i["URL"])

    db_cursor.execute("SELECT * FROM DB2.PICS EXCEPT SELECT * FROM main.PICS ORDER BY DB2.PICS.URL")
    fetch=db_cursor.fetchall()
    print("pics 2-1. diff len="+str(len(fetch)))
    list21=[]
    for i in fetch:
        list21.append(i["URL"])

    report["PICS"]=[list12,list21]

    #==================================================================================
    db_cursor.execute("SELECT * FROM main.LINKS EXCEPT SELECT * FROM DB2.LINKS ORDER BY main.LINKS.URL")
    fetch=db_cursor.fetchall()
    print("links 1-2. diff len="+str(len(fetch)))
    list12=[]
    for i in fetch:
        list12.append(i["URL"])

    db_cursor.execute("SELECT * FROM DB2.LINKS EXCEPT SELECT * FROM main.LINKS ORDER BY DB2.LINKS.URL")
    fetch=db_cursor.fetchall()
    print("links 2-1. diff len="+str(len(fetch)))
    list21=[]
    for i in fetch:
        list21.append(i["URL"])

    report["LINKS"]=[list12,list21]

    #==================================================================================
    db_cursor.execute("SELECT * FROM main.COMMENTS EXCEPT SELECT * FROM DB2.COMMENTS ORDER BY main.COMMENTS.COMMENT_ID")
    fetch=db_cursor.fetchall()
    print("comments 1-2. diff len="+str(len(fetch)))
    list12=[]
    for i in fetch:
        list12.append(i["COMMENT_ID"])

    db_cursor.execute("SELECT * FROM DB2.COMMENTS EXCEPT SELECT * FROM main.COMMENTS ORDER BY DB2.COMMENTS.COMMENT_ID")
    fetch=db_cursor.fetchall()
    print("comments 2-1. diff len="+str(len(fetch)))
    list21=[]
    for i in fetch:
        list21.append(i["COMMENT_ID"])

    report["COMMENTS"]=[list12,list21]



    db_cursor.execute("DETACH DB2")
    db_link.commit()

    return report





def close(delete=False):
    global db_link
    if db_link is not None:
        db_link.close()
    db_link=None
    if delete==True:
        os.remove(s.dump_folder+s.db_name)

if __name__=="__main__":
    print("use test_db.py!")