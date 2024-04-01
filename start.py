from download import download
from download import download_comments
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
import settings as s
import init


hello_message=lambda:f'''diary.ru dump utility, version {s.version}.
(C) zHz, 2022-2024. Licenced under MIT license, see readme.txt for details.

Diary dump consists of six stages:

Stage 1: Download posts as HTML
Stage 2: Download comments
Stage 3: Convert HTML to markdown
Stage 4: Download pics if needed
Stage 5: Replace cross-links
Stage 6: Create indexes
Stage 7: Update creation times (Windows only)

Working with pictures: {"Enabled" if s.download_pics==True else "Disabled"}
Save HTML in addition: {"Enabled" if s.download_html==True else "Disabled"}
Diary url: {s.diary_url}
Output folder: {s.base_folder}

Possible scenarios:

Stage:                     [  1  ][  2  ][  3  ][  4  ][  5  ][  6  ][  7  ]

A. Total (default)         [  +  ][  -  ][  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ]
B. Update + markup         [ +/- ][  -  ][  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ]
C. Update (no markup)      [ +/- ][  -  ][  -  ][  -  ][  -  ][  -  ][  -  ]
D. Download (no markup)    [  +  ][  -  ][  -  ][  -  ][  -  ][  -  ][  -  ]
E. Markup                  [  -  ][  -  ][  +  ][  {"+" if s.download_pics==True else "-"}  ][  +  ][  +  ][  +  ]
F. Download comments       [  -  ][  +  ][  -  ][  -  ][  -  ][  -  ][  -  ]
W. Change username
X. Toggle save html enable/disable mode (debug purpose)
Y. Toggle pics enable/disable mode
Z. Quit

Please choose scenario:'''

no=lambda: 0

s1=lambda: download(update=False,auto_find=True)
s1u=lambda: download(update=True,auto_find=True)
s2=lambda: download_comments()

s3=lambda: markdown_all_diary(reset=True)
s4=lambda: download_pics()
s5=lambda: replace_urls()
s6=lambda: create_indexes()
s7=lambda: update_times()

change_username_lambda=lambda: s.enter_username()
toggle_pics_lambda=lambda: s.toggle_pics()
toggle_html_lambda=lambda: s.toggle_html()

scenarios={
    'A':[s1,	no,	s3,	s4,	s5,	s6,	s7],
    'B':[s1u,	no,	s3,	s4,	s5,	s6,	s7],
    'C':[s1u,	no,	no,	no,	no,	no,	no],
    'D':[s1,	no,	no,	no,	no,	no,	no],
    'E':[no,	no,	s3,	s4,	s5,	s6,	s7],
	'F':[no,	s2,	no,	no,	no,	no,	no],
    'W':[change_username_lambda],
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
    'W':True,
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
