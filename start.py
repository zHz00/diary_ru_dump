import datetime
import logging as l

import click

from download import download
from download import download_comments
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
import settings as s

hello_message=lambda:f'''diary.ru dump utility, version {s.version}.
(C) zHz, 2022-2024. Licenced under MIT license, see readme.txt for details.

Diary dump consists of seven stages:

Stage 1: Download posts as HTML
Stage 2: Download comments
Stage 3: Convert HTML to markdown
Stage 4: Download pics if needed
Stage 5: Replace cross-links
Stage 6: Create indexes
Stage 7: Update creation times (Windows only)

Working with pictures: {"Enabled" if s.download_pics==True else "Disabled"}
Save HTML in addition: {"Enabled" if s.download_html==True else "Disabled"}
Save comments: {"Enabled" if s.download_comments==True else "Disabled"}
Diary url: {s.diary_url}
Output folder: {s.base_folder}

Possible scenarios:

Stage:                        [  1  ][  2  ][  3  ][  4  ][  5  ][  6  ][  7  ]

A. Total                      [  +  ][  +  ][  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ]
B. Update + markup (default)  [ +/- ][ {"+/-" if s.download_comments==True else " - "} ][  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ]
C. Update (no markup)         [ +/- ][ {"+/-" if s.download_comments==True else " - "} ][  -  ][  -  ][  -  ][  -  ][  -  ]
D. Download (no markup)       [  +  ][  {"+" if s.download_comments==True else "-"}  ][  -  ][  -  ][  -  ][  -  ][  -  ]
E. Markup                     [  -  ][  -  ][  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ]
F. Download comments          [  -  ][  {"+" if s.download_comments==True else "-"}  ][  -  ][  -  ][  -  ][  -  ][  -  ]
V. Change username
W. Toggle comments enable/disable mode
X. Toggle save html enable/disable mode (debug purpose)
Y. Toggle pics enable/disable mode
Z. Quit

Please choose scenario:'''

no=lambda: 0

s1=lambda: download(update=False,auto_find=True)
s1u=lambda: download(update=True,auto_find=True)
s2=lambda: download_comments(update=False)
s2u=lambda: download_comments(update=True)

s3=lambda: markdown_all_diary(reset=True)
s4=download_pics
s5=replace_urls
s6=create_indexes
s7=update_times

change_username_lambda=s.enter_username
toggle_pics_lambda=s.toggle_pics
toggle_html_lambda=s.toggle_html
toggle_comments_lambda=s.toggle_comments

scenarios={
    'A':[s1,	s2,	    s3,	s4,	s5,	s6,	s7],
    'B':[s1u,	s2u,	s3,	s4,	s5,	s6,	s7],
    'C':[s1u,	s2u,	no,	no,	no,	no,	no],
    'D':[s1,	s2,	    no,	no,	no,	no,	no],
    'E':[no,	no,	    s3,	s4,	s5,	s6,	s7],
	'F':[no,	s2,	    no,	no,	no,	no,	no],
    'V':[change_username_lambda],
    'W':[toggle_comments_lambda],
    'X':[toggle_html_lambda],
    'Y':[toggle_pics_lambda],
    'Z':[no]
}

continue_execution={
    'A':False,
    'B':False,
    'C':False,
    'D':False,
    'E':False,
    'F':False,
    'V':True,
    'W':True,
    'X':True,
    'Y':True,
    'Z':False,
}

print("test1")

s.load_username()

logger=l.getLogger()
file_handler=l.FileHandler(filename=s.dump_folder+"py_log"+datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+".log",mode="w",encoding="utf-8")
file_handler.setFormatter(l.Formatter("%(asctime)s %(levelname)s %(message)s"))
file_handler.setLevel(l.INFO)
logger.addHandler(file_handler)
logger.setLevel(l.INFO)

while True:
    print(hello_message())
    letter=input().upper()
    if letter=="":
        letter='B'
    if letter in scenarios:
        l.info("Starting scenario: %s",letter)
        for function in scenarios[letter]:
            function()
        if continue_execution[letter]:
            continue
        break
    else:
        print("Invalid letter!")
        continue
