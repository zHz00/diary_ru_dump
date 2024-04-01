import time
import datetime
import calendar
import os
import typing
import re

import settings as s
import init
import db


days_with_no_posts=0   
days_with_one_post=0
days_with_many_posts=0

weeks_in_month=8
days_in_week_markup=8
days_in_week=7
weekdays=["Пн","Вт","Ср","Чт","Пт","Сб","Вс",""]
#каждый месяц максимум 6 недель плюс строчка на дни недели, плюс строчка на месяцмножим на 4, т.к. календарь 3 на 4 блоком
months_rows=4
months_cols=3

roman_month=["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"]

def get_month(week: int,weekday_col: int) -> int:
    month_col=int(weekday_col/days_in_week_markup)
    month_row=int(week/weeks_in_month)
    return months_cols*month_row+month_col

def get_day(year: int,week: int,weekday_col: int) -> int:
    if weekday_col%days_in_week_markup==days_in_week_markup-1:#последняя колонка -- пропуск
        return 0
    month=get_month(week,weekday_col)
    (first_weekday,days_in_month)=calendar.monthrange(year,month+1)
    week_ordinary=week%weeks_in_month-2#неделя от 0 до 5
    day_ordinary=weekday_col%days_in_week_markup+week_ordinary*days_in_week
    day_this_month=day_ordinary-first_weekday+1
    if day_this_month<0:
        return 0
    if day_this_month>days_in_month:
        return 0
    return day_this_month

def generate_post_list_db(post_list: typing.List[int]) -> str:
    (post_date,post_time)=db.get_post_date_time(post_list[0])
    print(f"[DB]At {post_date} we have {len(post_list)} posts...")
    bare_filename=s.day_list_prefix+post_date+".md"
    filename=s.base_folder+s.indexes_folder+s.days_folder+bare_filename
    list_file=open(filename,"w",encoding=s.post_encoding,newline="\n")
    list_file.write("## "+post_date+"\n")
    list_file.write("| Время | Заголовок |\n| --- | --- |\n")
    for post_id in post_list:
        (post_date,post_time)=db.get_post_date_time(post_id)
        post_fname=db.get_post_fname(post_id)
        post_title=db.get_post_title(post_id)
        list_file.write(f"| {post_time} | [[{post_fname}\|{post_title}]] |\n")
    list_file.close()

    return bare_filename

def generate_year_db(year: int) -> str:
    global days_with_no_posts
    global days_with_one_post
    global days_with_many_posts
    text=""
    text+=f"## {year}\n"
    for h_col in range(months_cols*days_in_week_markup):
        text+="| "
    text+="|\n"
    for h_col in range(months_cols*days_in_week_markup):
        text+="| ---"
    text+="|\n"

    for week in range(0,weeks_in_month*months_rows):
        #каждый месяц максимум 6 недель плюс строчка на дни недели, множим на 4, т.к. календарь 3 на 4 блоком
        week_in_row=week%weeks_in_month
        if week_in_row==0:#выводим месяц
            for weekday_col in range(months_cols*days_in_week_markup):
                if(weekday_col%days_in_week_markup==0):
                    text+="| **"+roman_month[get_month(week,weekday_col)]+"** "
                else:
                    text+="| "
            text+="|\n"
        if week_in_row==1:#выводим дни недели
            for weekday_col in range(months_cols*days_in_week_markup):
                text+="| "+weekdays[weekday_col%days_in_week_markup]+" "
            text+="|\n"
        if week_in_row>1:
            for weekday_col in range(months_cols*days_in_week_markup):
                day=get_day(year,week,weekday_col)
                if day==0:
                    day_str=""
                else:
                    day_str=str(day)
                if day!=0:
                    #ищем посты с заданной датой
                    today=datetime.datetime(year,get_month(week,weekday_col)+1,day)
                    post_list=db.get_posts_list_at_date(today.strftime("%Y-%m-%d"))
                    if len(post_list)==1:#у нас единственная ссылка!
                        day_str="[["+db.get_post_fname(post_list[0])+"\|"+day_str+"]]"
                        days_with_one_post+=1
                    if len(post_list)>1:#у нас несколько постов
                        day_str="[["+generate_post_list_db(post_list)+"\|"+day_str+"]]"
                        days_with_many_posts+=1
                    if len(post_list)==0:
                        days_with_no_posts+=1
                text+="| "+day_str+" "
            text+="|\n"

    return text



def create_indexes() -> None:
    print("Stage 6 of 7: Creating indexes...")
    print("Creating full list...",end="")
    file_list=os.listdir(s.base_folder)

    db.connect()
    # I. Полный список постов

    #DB
    post_index=open(s.base_folder+s.indexes_folder+s.list_file_name,"w",encoding=s.post_encoding,newline="\n")
    post_index.write("| Дата | Заголовок |\n| --- | --- |\n")
    post_list_db=db.get_posts_list()
    for post_id in post_list_db:
        post_file_name=db.get_post_fname(post_id)
        post_title=db.get_post_title(post_id)
        (post_date,post_time)=db.get_post_date_time(post_id)
        date_timestamp=time.mktime(datetime.datetime.strptime(post_date,"%Y-%m-%d").timetuple())
        date_formatted=datetime.datetime.fromtimestamp(date_timestamp).strftime("%Y&#8209;%m&#8209;%d")
        post_index.write(f"| {date_formatted} | [[{post_file_name}\|{post_title}]] |\n")
    post_index.close()

    # II. Календарь

    #DB
    (first_date,first_time)=db.get_post_date_time(post_list_db[0])
    (last_date,last_time)=db.get_post_date_time(post_list_db[-1])
    year_start_db=datetime.datetime.fromisoformat(first_date).year
    year_end_db=datetime.datetime.fromisoformat(last_date).year 
    calendar_text=""
    for year in range(year_start_db,year_end_db+1):
        calendar_text+=generate_year_db(year)

    post_calendar=open(s.base_folder+s.indexes_folder+s.calendar_file_name,"w",encoding=s.post_encoding,newline="\n")
    post_calendar.write(calendar_text)
    post_calendar.close()


    print(f"Done. No posts days:{days_with_no_posts}, 1 post days: {days_with_one_post}, many post days:{days_with_many_posts}\nCreating tags lists...")

    # III. Теперь сделаем список тегов

    #DB

    tags_list=db.get_tags_list()
    common_tag_list_file=open(s.base_folder+s.indexes_folder+s.tags_file_name,"w",encoding=s.post_encoding,newline="\n")
    common_tag_list_file.write("| Тег | N |\n| --- | --- |\n")

    for tag in tags_list:
        print("[DB]Processing tag: "+tag)
        post_list=db.get_posts_list_at_tag(tag)
        tag_safe_name=re.sub(r'[\\/*?:"<>|]',"",tag.strip())
        common_tag_list_file.write(f"| [[{tag_safe_name}\|{tag}]] | {len(post_list)} |\n")

        tag_file_name=s.base_folder+s.tags_folder+tag_safe_name+".md"
        tag_file=open(tag_file_name,"w",encoding=s.post_encoding,newline="\n")
        tag_file.write("## Тег: "+tag+"\n")
        tag_file.write("#Теги\n\n")
        tag_file.write("| Дата | Заголовок |\n| --- | --- |\n")
        for post_id in post_list:
            (post_date,post_time)=db.get_post_date_time(post_id)
            post_fname=db.get_post_fname(post_id)
            post_title=db.get_post_title(post_id)
            date_formatted=datetime.datetime.fromisoformat(post_date).strftime("%Y&#8209;%m&#8209;%d")
            tag_file.write(f"| {date_formatted} | [[{post_fname}\|{post_title}]] |\n")
        tag_file.close()

    common_tag_list_file.close()


if __name__=="__main__":
    init.create_folders()
    create_indexes()