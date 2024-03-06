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

def connect():
    global db_link
    global db_cursor
    db_link=sl.connect(s.dump_folder+s.db_name)
    db_link.row_factory = sl.Row
    db_cursor=db_link.cursor()

def create_db():
    global db_link
    global db_cursor
    if db_link==None:
        connect()
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
        TIMESTAMP TEXT,
        TITLE TEXT,
        COMMENTS_N INTEGER,
        COMMENTS_NEED_UPDATE INTEGER,
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
        CONTENTS TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE PICS
    (
        POST_ID INTEGER,
        URL TEXT
    )
    ''')
    db_cursor.execute('''
    CREATE TABLE LINKS
    (
        POST_ID INTEGER,
        URL TEXT
    )
    ''')
    db_link.commit()

def add_post(post_id,url,timestamp,title,comments_n,tags,contents):
    global db_cursor
    res=db_ret.unknown
    comments_need_update=1
    db_cursor.execute('''
    SELECT * FROM POSTS WHERE POST_ID=(?)
    ''',(post_id,))
    found=db_cursor.fetchall()
    if(len(found)>0):
        comments_need_update_old=found[0]['COMMENTS_NEED_UPDATE']
        comments_n_old=found[0]['COMMENTS_N']
        if comments_n_old!=comments_n:#если число комментариев совпало, флаг остаётся таким, какой был
            comments_need_update=1#а если не совпало, выставляется в единицы. сброс происходит в другом месте
        else:
            commends_need_update=comments_need_update_old
        #пост найден, надо его обновить
        db_cursor.execute('''UPDATE POSTS SET
        (POST_ID,URL,TIMESTAMP,TITLE,COMMENTS_N,COMMENTS_NEED_UPDATE,CONTENTS)=
        (?,?,?,?,?,?,?)''',(post_id,url,timestamp,title,comments_n,comments_need_update,contents))
        res=db_ret.updated
    else:
        db_cursor.execute('''INSERT INTO POSTS 
        (POST_ID,URL,TIMESTAMP,TITLE,COMMENTS_N,COMMENTS_NEED_UPDATE,CONTENTS)
        VALUES
        (?,?,?,?,?,?,?)''',(post_id,url,timestamp,title,comments_n,comments_need_update,contents))
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

def add_pic(post_id,url):
    res=db_ret.unknown
    db_cursor.execute('''
    SELECT * FROM PICS WHERE POST_ID=(?) AND URL=(?)
    ''',(post_id,url))
    if len(db_cursor.fetchall())==0:
        db_cursor.execute('''
        INSERT INTO PICS (POST_ID,URL) VALUES (?,?)
        ''',(post_id,url))
        res=db_ret.inserted
    else:
        res=db_ret.already_exists
    db_link.commit()

def add_link(post_id,url):
    res=db_ret.unknown
    db_cursor.execute('''
    SELECT * FROM LINKS WHERE POST_ID=(?) AND URL=(?)
    ''',(post_id,url))
    if len(db_cursor.fetchall())==0:
        db_cursor.execute('''
        INSERT INTO LINKS (POST_ID,URL) VALUES (?,?)
        ''',(post_id,url))
        res=db_ret.inserted
    else:
        res=db_ret.already_exists
    db_link.commit()


def reset_db():
    if os.path.exists(s.dump_folder+s.db_name):
        os.remove(s.dump_folder+s.db_name)
    create_db()

def close_db():
    db_link.close()

if __name__=="__main__":
    reset_db()
    add_post(1,"test","test time","title",5,["Аниме","Дзякиган","Случай из жизни"],"Тестовое содержание")
    add_post(1,"test","test time2","title2",6,["Аниме","Дзякиган","Автомобили"],"Тестовое содержание3")
    add_pic(1,"https://example.com")
    add_pic(1,"https://example.com")
    add_pic(2,"https://example.com")
    add_pic(2,"https://example.com")
    add_link(1,"https://example.com")
    add_link(1,"https://example.com")
    add_link(2,"https://example.com")
    add_link(2,"https://example.com")
    close_db()
