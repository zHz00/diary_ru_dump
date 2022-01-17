from calendar import HTMLCalendar

from six import indexbytes
from download import download
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
import settings as s
import init


hello_message=lambda:f'diary.ru dump utility, version {s.version}.\n\
(C) zHz, 2022. Licenced under MIT license, see readme.txt for details.\n\
\n\
Please note that you can manually start every script. It will work correctly with settings described in settings.py\n\
\n\
Stage 1: Download posts as HTML\n\
Stage 2: Download pics if needed\n\
Stage 3: Convert HTML to markdown\n\
Stage 4: Replace cross-links\n\
Stage 5: Create indexes\n\
Stage 6: Update creation times\n\
\n\
Working with pictures: {"Enabled" if s.download_pics==True else "Disabled"}\n\
Diary url: {s.diary_url}\n\
Output folder: {s.base_folder}\n\
\n\
Possible scenarios:\n\
\n\
Stage:                     [   1   ][   2   ][   3   ][   4   ][   5   ][   6   ]\n\
\n\
A. Total (default)         [   +   ][   {"+" if s.download_pics==True else "-"}   ][   +   ][   +   ][   +   ][   +   ]\n\
B. Update + markup         [  +/-  ][   {"+" if s.download_pics==True else "-"}   ][   +   ][   +   ][   +   ][   +   ]\n\
C. Update (no markup)      [  +/-  ][   {"+" if s.download_pics==True else "-"}   ][   -   ][   -   ][   -   ][   -   ]\n\
D. Download (no markup)    [   +   ][   {"+" if s.download_pics==True else "-"}   ][   -   ][   -   ][   -   ][   -   ]\n\
E. Markup                  [   -   ][   -   ][   +   ][   +   ][   +   ][   +   ]\n\
Y. Change username\n\
Z. Toggle pics enable/disable mode \n\
\n\
Please choose scenario:'

no=lambda: 0

s1=lambda: download(update=False,auto_find=True)
s1u=lambda: download(update=True,auto_find=True)

s2=lambda: download_pics()
s3=lambda: markdown_all_diary(reset=True)
s4=lambda: replace_urls()
s5=lambda: create_indexes()
s6=lambda: update_times()

change_username_lambda=lambda: s.enter_username()
toggle_pics_lambda=lambda: s.toggle_pics()

scenarios={
    'A':[s1,	s2,	s3,	s4,	s5,	s6],
    'B':[s1u,	s2,	s3,	s4,	s5,	s6],
    'C':[s1u,	s2,	no,	no,	no,	no],
    'D':[s1,	s2,	no,	no,	no,	no],
    'E':[no,	no,	s3,	s4,	s5,	s6],
    'Y':[change_username_lambda],
    'Z':[toggle_pics_lambda]
}

continue_execution={
    'A':False,
    'B':False,
    'C':False,
    'D':False,
    'E':False,
    'Y':True,
    'Z':True,
}

s.load_username()

while True:
    print(hello_message())
    letter=input()
    if letter in scenarios:
        for function in scenarios[letter]:
            function()
        if continue_execution[letter]:
            continue
        break
    else:
        print("Invalid letter!")
        continue
