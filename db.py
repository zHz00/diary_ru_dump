import sqlite3 as sl
import settings as s
import os
import enum

db_link=None
db_cursor=None

class db_ret(enum.Enum):
    unknown=0
    inserted=1
    updated=2
    already_exists=3
    created=4
    connected=5

def connect(create=True):
    global db_link
    global db_cursor

    if db_link is not None:
        return db_ret.already_exists

    if not os.path.isfile(s.dump_folder+s.db_name):
        need_creation=True
    else:
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
    CREATE TABLE TAGS
    (
        TAG_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        TAG TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE POSTS
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
    CREATE TABLE TAGS_LINKED
    (
        POST_ID INTEGER,
        TAG_ID INTEGER
    )
    ''')    
    db_cursor.execute('''
    CREATE TABLE COMMENTS
    (
        COMMENT_ID INTEGER PRIMARY KEY,
        POST_ID INTEGER,
        TIMESTAMP TEXT,
        AUTHOR TEXT,
        DELETED INTEGER,
        CONTENTS TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE PICS
    (
        POST_ID INTEGER,
        POST_FNAME TEXT,
        URL TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE LINKS
    (
        POST_ID INTEGER,
        POST_FNAME TEXT,
        URL TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE INDEX TAGS_LINKED_INDEX
    ON TAGS_LINKED(POST_ID)
    ''')
    db_link.commit()

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
        db_cursor.execute('''UPDATE POSTS SET
        (POST_ID,URL,DATE,TIME,TITLE,COMMENTS_N,CONTENTS)=
        (?,?,?,?,?,?,?)
        WHERE POST_ID=(?)''',(post_id,url,date,time,title,comments_n,contents,post_id))
        res=db_ret.updated
    else:
        db_cursor.execute('''INSERT INTO POSTS 
        (POST_ID,URL,DATE,TIME,TITLE,COMMENTS_N,CONTENTS)
        VALUES
        (?,?,?,?,?,?,?)''',(post_id,url,date,time,title,comments_n,contents))
        res=db_ret.inserted

    #теперь пробивает таблицу тегов
    db_cursor.execute('''
    DELETE FROM TAGS_LINKED WHERE POST_ID=(?)
    ''',(post_id,))
    for tag in tags:
        db_cursor.execute('''
        SELECT * FROM TAGS WHERE TAG=(?)
        ''',(tag,))
        tag_db=db_cursor.fetchall()
        if len(tag_db)>0:
            db_cursor.execute('''
            INSERT INTO TAGS_LINKED (POST_ID,TAG_ID) VALUES (?,?)
            ''',(post_id,tag_db[0]['TAG_ID']))
        else:
            db_cursor.execute('''
            INSERT INTO TAGS (TAG) VALUES (?)
            ''',(tag,))
            db_cursor.execute('''
            SELECT * FROM TAGS WHERE TAG=(?)
            ''',(tag,))
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
    if len(db_cursor.fetchall())==0:
        db_cursor.execute('''
        INSERT INTO PICS (POST_ID,POST_FNAME,URL) VALUES (?,?,?)
        ''',(post_id,post_fname,url))
        res=db_ret.inserted
    else:
        res=db_ret.already_exists
    db_link.commit()

def add_link(post_id,post_fname,url):
    global db_cursor
    res=db_ret.unknown
    db_cursor.execute('''
    SELECT * FROM LINKS WHERE POST_ID=(?) AND URL=(?)
    ''',(post_id,url))#проверяем только ИД поста, а имя файла не проверяем. рано или поздно это может привести к проблемам!
    if len(db_cursor.fetchall())==0:
        db_cursor.execute('''
        INSERT INTO LINKS (POST_ID,POST_FNAME,URL) VALUES (?,?,?)
        ''',(post_id,post_fname,url))
        res=db_ret.inserted
    else:
        res=db_ret.already_exists
    db_link.commit()


def get_post_contents(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT CONTENTS FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    return db_cursor.fetchone()['CONTENTS']

def get_post_title(post_id:int) -> str:
    global db_cursor
    db_cursor.execute('''SELECT TITLE FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    return db_cursor.fetchone()['TITLE']

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

def get_posts_list():
    global db_cursor
    db_cursor.execute('''
    SELECT POST_ID FROM POSTS
    ''')
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(int(id['POST_ID']))
    return list

def get_tags_list():
    global db_cursor
    db_cursor.execute('''
    SELECT TAG FROM TAGS
    ''')
    fetch=db_cursor.fetchall()
    list=[]
    for id in fetch:
        list.append(id['TAG'])
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

def close():
    global db_link
    db_link.close()
    db_link=None

if __name__=="__main__":
    reset_db("test.db")
    add_post(1,"test","test date","test time","title",5,["Аниме","Дзякиган","Случай из жизни"],"Тестовое содержание")
    add_post(100,"test","test_date","test time2","title2",6,["Аниме","Дзякиган","Автомобили"],"Тестовое содержание3")
    add_pic(1,"TEST","https://example.com")
    add_pic(1,"TEST","https://example.com")
    add_pic(2,"TEST","https://example.com")
    add_pic(2,"TEST","https://example.com")
    add_link(1,"TEST","https://example.com")
    add_link(1,"TEST","https://example.com")
    add_link(2,"TEST","https://example.com")
    add_link(2,"TEST","https://example.com")
    print(get_post_contents(1))
    print(get_post_tags(1))
    print(get_posts_list())
    (d,t)=get_post_date_time(1)
    print(d,"|",t)
    print(get_post_title(1))
    print(get_post_url(1))
    print(get_tags_list())
    close()
