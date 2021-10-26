from markdownify import markdownify as markdownify
from os import path
from os import walk
from os import system
from pathlib import Path

"""file_list=[]

file_list=os.listdir(".")

file_list2=[t for t in Path(".").iterdir()]

#print(file_list)
print(file_list2)

#import os
start_path = '.' # current directory
for path,dirs,files in walk(start_path):
    for filename in files:
        print path.join(path,filename)"""

#system("cd q:\nbold\notebook2")
#system("q:")
#system("dir /b /s > list.txt")

system("dir .\dump\ /b /s > list.txt")

file=open("list.txt", encoding="cp866")
file_list=file.readlines()

print(file_list)

file_list_out=file_list.copy()

for i in file_list:
    test=i.strip()
    print("testing: "+test)
    if not(test.endswith(".htm") or test.endswith(".html")):
        print("removing: "+i)
        file_list_out.remove(i)
    else:
        print("levaing: "+i)

print(f"source list: (len: {len(file_list)})")
print(file_list)

print(f"final list: {len(file_list_out)})")
print(file_list_out)

for i in file_list_out:
    i_trim=i.strip()
    print("Processing:"+i_trim)
    f=open(i_trim,errors="ignore")
    contents=f.read()
    f_out=open(i_trim+".md","w")
    f_out.write(markdownify(contents))
    f_out.close()
    f.close()