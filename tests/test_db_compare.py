from init import get_function_name
import db
import settings as s

tp="tests/data/"

def test_cmp_posts():
    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted
    db.close()

    db.reset_db(s.dump_folder+get_function_name()+"1.db")
    res=db.check_connection()
    assert res == 0

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["POSTS"][0]==[]
    assert report["POSTS"][1]==[100]

    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted
    
    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["POSTS"][0]==[]
    assert report["POSTS"][1]==[]

    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"изменено")
    assert res==db.db_ret.updated_comments_n_identical
    
    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["POSTS"][0]==[100]
    assert report["POSTS"][1]==[100]

    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.updated_comments_n_identical

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["POSTS"][0]==[]
    assert report["POSTS"][1]==[]

    res=db.add_post(101,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["POSTS"][0]==[101]
    assert report["POSTS"][1]==[]

    db.close(delete=True)

    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    db.close(delete=True)

def test_cmp_tags():
    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted
    db.close()

    db.reset_db(s.dump_folder+get_function_name()+"1.db")
    res=db.check_connection()
    assert res == 0

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["TAGS"][0]==[]
    assert report["TAGS"][1]==[1,2,3]

    assert report["TAGS_LINKED"][0]==[]
    assert report["TAGS_LINKED"][1]==[100,100,100]


    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted
    
    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["TAGS"][0]==[]
    assert report["TAGS"][1]==[]

    assert report["TAGS_LINKED"][0]==[]
    assert report["TAGS_LINKED"][1]==[]


    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Случай из жизни",5)],"изменено")
    assert res==db.db_ret.updated_comments_n_identical
    
    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["TAGS"][0]==[4]
    assert report["TAGS"][1]==[]

    assert report["TAGS_LINKED"][0]==[100]#2-я бд содержит дополнительный тег "автомобили" у поста 100, которого нет у 2-й бд после обновления поста
    assert report["TAGS_LINKED"][1]==[100]#а 1-я бд содержит у того же поста тег случай из жизни, которого нет во 2-й бд. поэтому сообщается о двойном несоответствии.


    db.close(delete=True)

    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    db.close(delete=True)

def test_cmp_links():
    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted

    res=db.add_link(1,"TEST",2,"https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_link(1,"TEST",1,"https://example2.com")
    assert res==db.db_ret.inserted

    db.close()

    db.reset_db(s.dump_folder+get_function_name()+"1.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["LINKS"][0]==[]
    assert report["LINKS"][1]==["https://example.com","https://example2.com"]

    res=db.add_link(1,"TEST",2,"https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_link(1,"TEST",1,"https://example2.com")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["LINKS"][0]==[]
    assert report["LINKS"][1]==[]

    res=db.add_link(1,"TEST",1,"https://example3.com")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["LINKS"][0]==["https://example3.com"]
    assert report["LINKS"][1]==[]


    db.close(delete=True)

    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    db.close(delete=True)

def test_cmp_pics():
    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted

    res=db.add_pic(1,"TEST","https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_pic(1,"TEST","https://example2.com")
    assert res==db.db_ret.inserted

    db.close()

    db.reset_db(s.dump_folder+get_function_name()+"1.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["PICS"][0]==[]
    assert report["PICS"][1]==["https://example.com","https://example2.com"]

    res=db.add_pic(1,"TEST","https://example.com")
    assert res==db.db_ret.inserted
    res=db.add_pic(1,"TEST","https://example2.com")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["PICS"][0]==[]
    assert report["PICS"][1]==[]

    res=db.add_pic(1,"TEST","https://example3.com")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["PICS"][0]==["https://example3.com"]
    assert report["PICS"][1]==[]


    db.close(delete=True)

    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    db.close(delete=True)

def test_cmp_comments():
    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(100,"test","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted

    res=db.add_comment(1,100,"2001-01-01","time1","Гость","test")
    assert res==db.db_ret.inserted
    res=db.add_comment(2,100,"2002-01-01","time2","Гость","test")
    assert res==db.db_ret.inserted

    db.close()

    db.reset_db(s.dump_folder+get_function_name()+"1.db")
    res=db.check_connection()
    assert res == 0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["COMMENTS"][0]==[]
    assert report["COMMENTS"][1]==[1,2]

    res=db.add_comment(1,100,"2001-01-01","time1","Гость","test")
    assert res==db.db_ret.inserted
    res=db.add_comment(2,100,"2002-01-01","time2","Гость","test")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["COMMENTS"][0]==[]
    assert report["COMMENTS"][1]==[]

    res=db.add_comment(3,100,"2001-01-01","time1","Гость","test")
    assert res==db.db_ret.inserted

    report=db.compare_with_other_db(s.dump_folder+get_function_name()+"2.db")

    assert report["COMMENTS"][0]==[3]
    assert report["COMMENTS"][1]==[]


    db.close(delete=True)

    db.reset_db(s.dump_folder+get_function_name()+"2.db")
    res=db.check_connection()
    assert res == 0
    db.close(delete=True)