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
    updated_comments_n_changed=6
    updated_comments_n_identical=7

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
    CREATE TABLE IF NOT EXISTS TAGS
    (
        TAG_ID INTEGER PRIMARY KEY AUTOINCREMENT,
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
    CREATE INDEX IF NOT EXISTS "COMMENTS_INDEX" ON "COMMENTS" (
	"POST_ID"
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

def add_link(post_id,post_fname,dest_post_id,url):
    global db_cursor
    res=db_ret.unknown
    db_cursor.execute('''
    SELECT * FROM LINKS WHERE POST_ID=(?) AND URL=(?)
    ''',(post_id,url))#проверяем только ИД поста, а имя файла не проверяем. рано или поздно это может привести к проблемам!
    #UPD. И уже привело. Теперь при наличии строки я обновляю имя файла, потому что оно, вообще-то, могло измениться!
    if len(db_cursor.fetchall())==0:
        db_cursor.execute('''
        INSERT INTO LINKS (POST_ID,POST_FNAME,DEST_POST_ID,URL) VALUES (?,?,?,?)
        ''',(post_id,post_fname,dest_post_id,url))
        res=db_ret.inserted
    else:
        db_cursor.execute('''
        UPDATE LINKS SET POST_FNAME=(?) 
        WHERE POST_ID=(?) AND URL=(?)
        ''',(post_fname,post_id,url))
        res=db_ret.already_exists
    db_link.commit()


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
    WHERE POSTS.POST_ID=(?)
    ''',(post_id,))
    return db_cursor.fetchone()['POST_FNAME']

def get_posts_list():
    global db_cursor
    db_cursor.execute('''
    SELECT POST_ID,DATE,TIME 
    FROM POSTS 
    ORDER BY DATE,TIME
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
        db_cursor.execute('''INSERT INTO COMMENTS (COMMENT_ID,POST_ID,DATE,TIME,AUTHOR,DELETED,CONTENTS)
        VALUES ((?),(?),(?),(?),(?),0,(?))
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
    db_cursor.execute('''UPDATE COMMENTS SET DELETED=1 WHERE COMMENT_ID=(?)
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
    #connect()
    #create_db()
    reset_db("test.db")
    add_post(1,"test","test date","test time","title",5,["Аниме","Дзякиган","Случай из жизни"],"Тестовое содержание")
    add_post(100,"test","test_date","test time2","title2",6,["Аниме","Дзякиган","Автомобили"],"Тестовое содержание3")
    add_pic(1,"TEST","https://example.com")
    add_pic(1,"TEST","https://example.com")
    add_pic(2,"TEST","https://example.com")
    add_pic(2,"TEST","https://example.com")
    add_link(1,"TEST",2,"https://example.com")
    add_link(1,"TEST",2,"https://example.com")
    add_link(2,"TEST",-1,"https://example.com")
    add_link(2,"TEST",1,"https://example.com")
    add_comment(1,100,"date1","time1","me","test")
    add_comment(2,100,"date2","time2","me","test")
    add_comment(3,100,"date3","time3","me","test")
    add_comment(4,100,"date4","time4","me","test")
    add_comment(4,100,"date2","time2","me2","test2")
    mark_deleted_comment(3)
    print("get_post_contents(1):",get_post_contents(1))
    print("get_post_tags(1):",get_post_tags(1))
    print("get_posts_list():",get_posts_list())
    (d,t)=get_post_date_time(1)
    print("get_post_date_time(1):",d,"|",t)
    print("get_post_title(1):",get_post_title(1))
    print("get_post_url(1):",get_post_url(1))
    print("get_tags_list()",get_tags_list())
    print("get_pics_list_plain():",get_pics_list_plain())
    print("get_links_list_plain():",get_links_list_plain())
    print("get_pics_list_dict():",get_pics_list_dict())
    print("get_links_list_dict()",get_links_list_dict())
    print("get_post_fname(1):",get_post_fname(1))
    print("get_posts_list_at_date('test_date')):",get_posts_list_at_date("test_date")) 
    print("get_comments_n(100):",get_comments_n(100))
    print("get_comments_downloaded(100):",get_comments_downloaded(100))
    print("get_comments_list(100)",get_comments_list(100))
    print("get_comments_list(100)",get_comments_list(100,deleted=True))
    print("get_comments_list(100)",get_comments_list(100,deleted=False))    
    print("update_comments_n(100,5)",update_comments_n(100,5))
    list=get_comments_list(100)
    for id in list:
        print(id)
        print("get_comments_date_time",get_comment_date_time(id))
        print("get_comment_author",get_comment_author(id))
        print("get_comment_contents",get_comment_contents(id))


    close()
