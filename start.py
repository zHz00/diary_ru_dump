from calendar import HTMLCalendar

from six import indexbytes
from download import download
from download_pics import download_pics
from markdown_all_diary import markdown_all_diary
from replace_urls import replace_urls
from create_indexes import create_indexes
from update_times import update_times
import settings as s


hello_message=f'diary.ru dump utility, version {s.version}.\n\
(C) zHz, 2022. Licenced under MIT license, see readme.txt for details.\n\
\n\
Please note that you can manually start every script. It will correctly with settings described in settings.py\n\
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

print(hello_message)