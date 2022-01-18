from download import download
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
import settings as s
import init


hello_message=lambda:f'''diary.ru dump utility, version {s.version}.
(C) zHz, 2022. Licenced under MIT license, see readme.txt for details.

Diary dump consists of six stages:

Stage 1: Download posts as HTML
Stage 2: Convert HTML to markdown
Stage 3: Download pics if needed
Stage 4: Replace cross-links
Stage 5: Create indexes
Stage 6: Update creation times (Windows only)

Working with pictures: {"Enabled" if s.download_pics==True else "Disabled"}
Diary url: {s.diary_url}
Output folder: {s.base_folder}

Possible scenarios:

Stage:                     [  1  ][  2  ][  3  ][  4  ][  5  ][  6  ]

A. Total (default)         [  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ][  +  ]
B. Update + markup         [ +/- ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ][  +  ]
C. Update (no markup)      [ +/- ][  -  ][  -  ][  -  ][  -  ][  -  ]
D. Download (no markup)    [  +  ][  -  ][  -  ][  -  ][  -  ][  -  ]
E. Markup                  [  -  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ][  +  ]
X. Change username
Y. Toggle pics enable/disable mode
Z. Quit

Please choose scenario:'''

no=lambda: 0

s1=lambda: download(update=False,auto_find=True)
s1u=lambda: download(update=True,auto_find=True)

s2=lambda: markdown_all_diary(reset=True)
s3=lambda: download_pics()
s4=lambda: replace_urls()
s5=lambda: create_indexes()
s6=lambda: update_times()

change_username_lambda=lambda: s.enter_username()
toggle_pics_lambda=lambda: s.toggle_pics()

scenarios={
    'A':[s1,	s2,	s3,	s4,	s5,	s6],
    'B':[s1u,	s2,	s3,	s4,	s5,	s6],
    'C':[s1u,	no,	no,	no,	no,	no],
    'D':[s1,	no,	no,	no,	no,	no],
    'E':[no,	s2,	s3,	s4,	s5,	s6],
    'X':[change_username_lambda],
    'Y':[toggle_pics_lambda],
    'Z':[no]
}

continue_execution={
    'A':False,
    'B':False,
    'C':False,
    'D':False,
    'E':False,
    'X':True,
    'Y':True,
    'Z':False,
}

s.load_username()

while True:
    print(hello_message())
    letter=input().upper()
    if letter in scenarios:
        for function in scenarios[letter]:
            function()
        if continue_execution[letter]:
            continue
        break
    else:
        print("Invalid letter!")
        continue
