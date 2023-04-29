import markdownify
from os import getcwd, path
from os import walk
from os import listdir

from pathlib import Path
import re
from bs4 import BeautifulSoup

import settings as s
import init

def normalize_to_prev_ver(text: str) -> str:
    #после перехода на lxml парсер по неясной причине мд-файлы выглядят немного не так, как должны
    #чтобы в ГИТе сравнение с предыдущими версиями работало нормально, надо кое-что добавить, а кое-что убрать. этим и займёмся
    text_lines=text.split("\n")
    text_lines[1]=text_lines[1]+"="
    #print("3:["+text_lines[3]+"]")
    text_lines[3]=text_lines[3]+" "
    #print("4:["+text_lines[4]+"]")
    text_lines[4]=" "+text_lines[4]+" "
    text_lines[5]=" "+text_lines[5]
    tags_line=0
    for x in range(len(text_lines)-1,-1,-1):
        if text_lines[x].find("Теги:")!=-1:
            tags_line=x
            break
    text_lines[tags_line-3]="  "+text_lines[tags_line-3]
    text_lines[tags_line-2]=" "+text_lines[tags_line-2]+" "
    text_lines[tags_line-1]=" "+text_lines[tags_line-1]
    text_lines[tags_line]=" "+text_lines[tags_line]+" "
    for x in range(tags_line,len(text_lines)-1):
        if len(text_lines[x])>0 and text_lines[x][0]=='[':#строчка с тегом
            text_lines[x]=" "+text_lines[x]
    #теперь надо убрать пустые строки в конце
    for x in range(len(text_lines)-1,tags_line,-1):
        if len(text_lines[x])==0:
            del text_lines[x]
    text_lines[-1]=" "+text_lines[-1]#ID:
    return "\n".join(text_lines)

def remove_unwanted_escape(mk_str: str) -> str:
    #надо кое-что сделать, а именно убрать все эскейпы созданные markdownify внутри блоков кода
    pre_indexes=[pre.start() for pre in re.finditer('```', mk_str)]
    pre_index_sets=[[]]
    for idx in pre_indexes:
        if len(pre_index_sets[-1])>=2:
            pre_index_sets.append([])
        pre_index_sets[-1].append(idx)
    chunk_sets=[[0]]
    for set in pre_index_sets:
        if len(set)!=2:
            return mk_str#не собрали ничего, так что сразу возвращаем как есть
        chunk_sets[-1].append(set[0])
        chunk_sets[-1].append(set[1])
        chunk_sets.append([set[1]])
    chunk_sets[-1].append([len(mk_str),len(mk_str)])
    mk_str_res=""
    for chunk in chunk_sets:
        mk_str_res+mk_str[:chunk[0]]
        mk_str_res+=mk_str[chunk[1]:chunk[2]].replace("\\","")
    return mk_str_res

def markdown_all_diary(reset: bool,post_id:int=0) -> None:
    print ("Stage 2 of 6: Creating markdown files from HTML...")
    if(reset==True):
        init.reset_vault()
        
    if(post_id==0):
        file_list=listdir(s.dump_folder)
    else:
        file_list=["p"+str(post_id)+".htm"]

    file_list_out=file_list.copy()

    found=0
    for file in file_list:
        test=file.strip()
        if not(test.endswith(".htm")):
            file_list_out.remove(file)
        else:
            found+=1
        print(f"Found {found} posts...",end='\r')

    #сначала пробежимся по всем постам и создадим файлы, соответствующие тегам

    print("\nCreating tags list...")

    renamed_count=0
    tag_count=0

    for post in file_list_out:
        post_trim=s.dump_folder+post.strip()
        post_meta=s.dump_folder+post[:-4]+".txt"
        print(f"Found {tag_count} tags. Processing:"+post_trim,end="\r")
        f_meta=open(post_meta,"r",encoding=s.post_encoding)
        meta=f_meta.readlines()

        #сохраним теги

        tags=meta[5:]
        for tag in tags:
            if len(tag.strip())==0:#у нас последняя строчка пустая. ну и на случай если другие пустые будут
                continue
            tag_name=s.base_folder+s.tags_folder+re.sub(r'[\\/*?:"<>|]',"",tag.strip())+".md"
            test_path=Path(tag_name)
            if not test_path.is_file():
                tag_file=open(tag_name,"w",encoding=s.post_encoding)
                tag_file.write("#Теги")
                tag_file.close()
                tag_count+=1

    posts_list={}
    pics=[]
    links=[]
    ids=[]



    #ещё раз пробегаемся по всем постам, но уже по вопросам содержимого

    print("\nConverting posts...")

    file_list_len=len(file_list_out)
    n=0
    for post in file_list_out:
        percentage=int(n/file_list_len*100)
        print(f"[{percentage}%] {n} of {file_list_len} done...",end="\r")
        n+=1
        post_trim=post.strip()
        post_meta=post[:-4]+".txt"
        f_meta=open(s.dump_folder+post_meta,encoding=s.post_encoding)
        meta=f_meta.readlines()

        #сохраним содержимое

        out_name_file_base=re.sub(r'[\\/*?:"<>|]',"",meta[4]).strip()
        if len(out_name_file_base)==0:
            out_name_file_base="[NOT PRINTABLE]"
        out_name_file=out_name_file_base
        out_name=s.base_folder+out_name_file+".md"
        out_name_as_tag=s.base_folder+s.tags_folder+out_name_file+".md"
        test_path=Path(out_name)
        test_path_as_tag=Path(out_name_as_tag)
        append_num=0
        while test_path.is_file() or test_path_as_tag.is_file():
            print(f"[{percentage}%]File "+out_name+" exists! Renaming...")
            out_name_file=out_name_file_base+"["+str(append_num)+"]"
            out_name=s.base_folder+out_name_file+".md"
            out_name_as_tag=s.base_folder+s.tags_folder+out_name_file+".md"
            test_path=Path(out_name)
            test_path_as_tag=Path(out_name_as_tag)
            append_num+=1
            renamed_count+=1

        #имя файла готово, теперь надо его сохранить в словарь

        posts_list[meta[0].strip()]=out_name_file


        f=open(s.dump_folder+post_trim,encoding=s.post_encoding,errors="ignore")
        contents=f.read().replace("\n","").replace("\r","").replace("</br>","<br/>").replace("<br>","<br/>")
        contents=contents.replace("<tbody>","").replace("</tbody>","")
        #contents=contents.replace("&gt;","\\&gt;")
        #contents=contents.replace("&lt;","\\&lt;")
        
        #добываем ссылки и картинки
        bs=BeautifulSoup(contents,"html.parser")
        for pic in bs.find_all("img"):
            if pic.parent.name=="pre" or pic.parent.parent.name=="pre":
                continue
            pic1={}
            pic1['id']=meta[0].strip()
            pic1['name']=out_name_file
            pic1['url']=pic['src']
            pics.append(pic1)

        for link in bs.find_all("a"):
            if not link.has_attr("href"):
                continue
            link_is_cross_link=False
            link_is_pic=False
            if re.search(r'[\[\]\^\#\|]',link.contents[0]):
                print(f"Warning! \"a\" tag has forbidden characters: {link.contents}")
            for test_str in s.cross_link_checking:
                if link['href'].lower().find(test_str.lower())!=-1:
                    link_is_cross_link=True
            for test_str in s.pic_checking:
                if link['href'].strip().lower().endswith(test_str.lower())!=False and link.find("img")==None:
                    link_is_pic=True
            #воркэраунд для ситуации, когда имя файла упоминается как аргумент к запросу в гугл 
            # (такой случай один, но нормализовать его в самом дневнике я не могу, поэтому делаю тут)
            for test_str in s.forbidden_pic_urls:
                if link['href'].strip().lower().find(test_str.lower())!=-1:
                    link_is_pic=False
            if link_is_cross_link==False and link_is_pic==False:
                continue
            link1={}
            link1['id']=meta[0].strip()
            link1['name']=out_name_file
            link1['url']=link['href']
            links.append(link1)

        


        #линуксовые концы строк т.к. обсидиан всё равно их заменит
        f_out=open(out_name,"w",encoding=s.post_encoding,errors="ignore",newline='\n')
        if s.diary_url_mode==3:
            out_contents=markdownify.markdownify(contents,strong_em_symbol=markdownify.UNDERSCORE,escape_asterisks=True).strip()
        else:
            out_contents=markdownify.markdownify(contents).strip()
            out_contents=normalize_to_prev_ver(out_contents)
        #макрдаун этого не умеет, поэтому вручную сделаем зачёркивание!
        #out_contents=out_contents.replace("~~","~")
        out_len=len(out_contents)
        f_out.write(out_contents)
        f_out.close()
        f.close()

    #создадим список ссылок и список картинок

    links_file=open(s.base_folder+s.links_file,"w",encoding=s.links_file_encoding)
    for link in links:
        links_file.write(link["id"]+"\n")
        links_file.write(link["name"]+"\n")
        links_file.write(link["url"]+"\n")
    links_file.close()

    pics_file=open(s.base_folder+s.pics_file,"w",encoding=s.pics_file_encoding)
    for pic in pics:
        pics_file.write(pic["id"]+"\n")
        pics_file.write(pic["name"]+"\n")
        pics_file.write(pic["url"]+"\n")
    pics_file.close()

    print(f"\nend (markdown). All={len(file_list_out)}, renamed={renamed_count}, tags={tag_count}")
    if s.diary_url_mode==3:
        return out_name,out_len
    else:
        return 0

if __name__=="__main__":
    init.create_folders()
    markdown_all_diary(reset=True)
