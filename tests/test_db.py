import db


def test_connect():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res==0
    db.close()
def test_adding():
    db.reset_db("test.db")
    res=db.check_connection()
    assert res ==0
    res=db.add_post(1,"test","2001-01-01","test time","title",5,[("Аниме",1),("Дзякиган",2),("Случай из жизни",3)],"Тестовое содержание")
    assert res==db.db_ret.inserted
    res=db.add_post(100,"test","2001-01-01","test time2","title2",6,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.inserted
    res=db.add_post(100,"test","2001-01-01","test time2","title2",7,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое?")
    assert res==db.db_ret.updated_comments_n_changed
    res=db.add_post(100,"test_changed","2001-01-01","test time2","title2",0,[("Аниме",1),("Дзякиган",2),("Автомобили",4)],"это что такое? изменено")
    assert res==db.db_ret.updated_comments_n_identical
    #реальное число в бд равно нулю, поэтому надо передать ноль чтобы получить такое возвращаемое значение
    
    #проверка, как там добавилось
    list=db.get_posts_list(reversed=True)
    assert list==[100,1]
    list=db.get_posts_list()
    assert list==[1,100]

    
