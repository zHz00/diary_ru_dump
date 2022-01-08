import time
import datetime
import calendar
import os
import settings as s
from win32_setctime import setctime
import init

init.create_folders()

file_list=os.listdir(s.base_folder)


# I. Полный список постов

counter=0
post_list=[]

for post_file_name in file_list:
    if post_file_name.endswith(".md")==False:
        continue
    post_file_name=s.base_folder+post_file_name.strip()
    post_file=open(post_file_name,"r",encoding=s.post_list_encoding)
    post_contents=post_file.readlines()
    if len(post_contents)<5:
        continue #это не настоящий пост а какая-то ерунда
    post_date=post_contents[4].strip()
    post_file.close()
    post_time=time.mktime(datetime.datetime.strptime(post_date,"%Y-%m-%d, %H:%M").timetuple())
    post_list.append((post_time,os.path.splitext(os.path.basename(post_file_name.strip()))[0]))
    counter+=1

post_list.sort(key=lambda pdt:pdt[0])

post_index=open(s.base_folder+s.indexes_folder+s.list_file_name,"w",encoding=s.post_encoding,newline="\n")
post_index.write("| Дата | Заголовок |\n| --- | --- |\n")
for post in post_list:
    time_s=datetime.datetime.fromtimestamp(post[0]).strftime("%Y&#8209;%m&#8209;%d")
    post_index.write(f"| {time_s} | [[{post[1]}\|{post[1]}]] |\n")
post_index.close()

print(f"End create_indexes: list. Counter={counter}")

# II. Календарь

weeks_in_month=8
days_in_week_markup=8
days_in_week=7
weekdays=["Пн","Вт","Ср","Чт","Пт","Сб","Вс",""]
#каждый месяц максимум 6 недель плюс строчка на дни недели, плюс строчка на месяцмножим на 4, т.к. календарь 3 на 4 блоком
months_rows=4
months_cols=3

roman_month=["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"]

def get_month(week,weekday_col):
    month_col=int(weekday_col/days_in_week_markup)
    month_row=int(week/weeks_in_month)
    return months_cols*month_row+month_col

def get_day(year,week,weekday_col):
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

def generate_post_list(post_links):
    post_date=datetime.datetime.fromtimestamp(post_links[0][0]).date()
    print(f"At {post_date.strftime('%Y-%m-%d')} we have {len(post_links)} posts...")
    bare_filename=s.day_list_prefix+post_date.strftime("%Y-%m-%d")+".md"
    filename=s.base_folder+s.indexes_folder+s.days_folder+bare_filename
    list_file=open(filename,"w",encoding=s.post_encoding,newline="\n")
    list_file.write("## "+post_date.strftime("%Y-%m-%d")+"\n")
    list_file.write("| Время | Заголовок |\n| --- | --- |\n")
    for post in post_links:
        time_s=datetime.datetime.fromtimestamp(post[0]).strftime("%H:%M")
        list_file.write(f"| {time_s} | [[{post[1]}\|{post[1]}]] |\n")
    list_file.close()

    return bare_filename

days_with_no_posts=0   
days_with_one_post=0
days_with_many_posts=0

def generate_year(year):
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
                    post_links=[]
                    for post in post_list:
                        if datetime.datetime.fromtimestamp(post[0]).date()==today.date():
                            post_links.append(post)
                    if len(post_links)==1:#у нас единственная ссылка!
                        day_str="[["+post_links[0][1]+"\|"+day_str+"]]"
                        days_with_one_post+=1
                    if len(post_links)>1:#у нас несколько постов
                        day_str="[["+generate_post_list(post_links)+"\|"+day_str+"]]"
                        days_with_many_posts+=1
                    if len(post_links)==0:
                        days_with_no_posts+=1
                text+="| "+day_str+" "
            text+="|\n"

    return text


        

year_start=datetime.datetime.fromtimestamp(post_list[0][0]).year
year_end=datetime.datetime.fromtimestamp(post_list[-1][0]).year

calendar_text=""
for year in range(year_start,year_end+1):
    calendar_text+=generate_year(year)

post_calendar=open(s.base_folder+s.indexes_folder+s.calendar_file_name,"w",encoding=s.post_encoding,newline="\n")
post_calendar.write(calendar_text)
post_calendar.close()


print(f"End create_indexes: calendar. No posts days:{days_with_no_posts}, 1 post days: {days_with_one_post}, many post days:{days_with_many_posts}")

# III. Теперь сделаем список тегов

# это пока не сделано

print(f"End create_indexes: tags.")