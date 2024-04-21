import requests
import json
from bs4 import BeautifulSoup
import time
import settings as s
__token=""
req_prefix="https://api.telegra.ph/"
upload_prefix="https://telegra.ph/"

allowed_tags=[  "a",        "aside",    "b",            "blockquote",   "br",
                "code",     "em",       "figcaption",   "figure",       "h3", 
                "h4",       "hr",       "i",            "iframe",       "img", 
                "li",       "ol",       "p",            "pre",          "s", 
                "strong",   "u",        "ul",           "video"]

def init(token):
    global __token
    __token=token
    
def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))
    
def upload_image(file,retries=5):
    #open(file,"rb").close()
    #return "[TEST1]"+file+"[TEST2]"
    print("Uploading: "+file+";remaining tries:"+str(retries))
    try:
        image_file=open(file, "rb")
        res=requests.post(upload_prefix+"upload",files={"file":image_file})
        image_file.close()
        res_dict=json.loads(res.content.decode("cp437"))
        
        if "src" in res_dict[0]:
            print("URL:"+res_dict[0]["src"])
            return res_dict[0]["src"]
        else:
            print("ERROR:"+str(res_dict))
            return None
    except requests.ConnectionError as e:
        image_file.close()
        print(e)
        print("Exception occured. Waiting...")
        time.sleep(20)
        if(retries>0):
            return upload_image(file,retries-1)
        else:
            print("What a pity, no connection. Aborting")
            return None
    except json.JSONDecodeError as e:
        image_file.close()
        print(e)
        print("Exception occured. Waiting...")
        time.sleep(20)
        if(retries>0):
            return upload_image(file,retries-1)
        else:
            print("What a pity, no connection. Aborting")
            return None

    
def create_page(title,content,retries=5):
    print("Creating page... retries:"+str(retries))
    data={"access_token":__token.encode("utf-8"),"title":title.encode("utf-8"),"author_name":s.tg_channel_name,"author_url":"https://t.me/"+s.tg_channel_name[1:],"content":content.encode("utf-8")}
    try:
        res=requests.post(req_prefix+"createPage",data=data)
    except:
        print("error during posting. waiting...")
        time.sleep(s.wait_time)
        if(retries>0):
            return create_page(title,content,retries-1)
        else:
            return None
    print("Done. Results:")
    print(res.headers)
    print(res.content)
    try:
        res_dict=json.loads(res.content.decode("cp437"))
    except:
        print("Answer is not JSON. Retrying after pause...")
        time.sleep(s.wait_time)
        if(retries>0):
            return create_page(title,content,retries-1)
        else:
            return None
    if "ok" in res_dict:
        if res_dict["ok"]==False:
            print("ERROR:"+res_dict["error"])
            return None
        else:
            print("URL:"+res_dict["result"]["url"])
            return res_dict["result"]["url"]
    return None
    
    
def show_children(file1,bs4obj,level):
    ret=""
    prev_tag=""
    if hasattr(bs4obj,"children"):
        first=True
        for tag in bs4obj.children:
            if not first:
                ret+=","
            else:
                first=False
            if(hasattr(tag,"name")):
                if(tag.name is None):
                    prev_tag=""
                    #file.write(("-"*level)+"Tag: None\n")
                    file1.write(("-"*level)+"|"+tag.string.replace("\\","\\\\").replace('\"','\\"')+"\n")
                    if len(tag.string.strip())==0:
                        if len(ret)>0:
                            if ret[-1]==",":
                                ret=ret[:-1]
                        else:
                            first=True
                        continue#пропускаем пустые теги
                    else:
                        ret+='{"tag":"div","children":["'+tag.string.replace("\\","\\\\").replace('\"','\\"').strip("\n ")+' "]}'
                else:
                    if tag.name=="br" and prev_tag=="br":
                        print("double br!")
                        if len(ret)>0:
                            if ret[-1]==",":
                                ret=ret[:-1]
                        else:
                            first=True
                        continue#пропускаем двойные бр-ки
                    prev_tag=tag.name
                    if tag.name=="a" and tag.has_attr("class") and tag["class"][0]=="LinkMore":
                        if len(ret)>0:
                            if ret[-1]==",":
                                ret=ret[:-1]
                        else:
                            first=True
                        continue#пропускаем раскрытие мор
                    if tag.name not in allowed_tags:
                        tag_out="div"
                    else:
                        tag_out=tag.name
                    file1.write(("-"*level)+"|Tag:"+tag.name+"["+tag_out+"]\n")
                    ret+='{"tag":"'+tag_out+'",'
                    if tag_out=="a":
                        if tag.has_attr("href"):
                            ret+='"attrs":{"href":"'+tag["href"]+'","target":"_blank"},'
                    if tag_out=="img":
                        ret+='"attrs":{"src":"'+tag["src"]+'"},'
                    ret+='"children":['+show_children(file1,tag,level+1)+']}'
            else:
                file1.write(("-"*level)+"None\n")
    return ret

def html_to_node(html):
    page = BeautifulSoup(html, 'lxml')
    file_pr=open(s.dump_folder+"out_pr.txt","w",encoding="utf-8")
    file_pr.write(page.prettify())
    file_pr.close()
    file1=open(s.dump_folder+"out.txt","w",encoding="utf-8")
    file2=open(s.dump_folder+"out_nodes.txt","w",encoding="utf-8")
    text="["+show_children(file1,page,1)+"]"
    file2.write(text)
    file1.close()
    file2.close()
    print("html_to_node finished, size:"+str(len(text)))
    return text

def test_tg_ph():
    t=open(s.dump_folder+"testpage.html","r",encoding="utf-8")
    htext=t.read()
    text=html_to_node(htext)
    print(text)
    init("-")
    #res=create_page("TESTPAGE",text)
    res=upload_image("test.jpg")
    print(res)

if __name__=="__main__":
    test_tg_ph()
