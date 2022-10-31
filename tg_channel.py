import requests

__token=""
__chat_id=""
req_prefix="https://api.telegram.org/bot"

def init(token,chat_id):
    global __token,__chat_id
    print("Posting to "+chat_id+", token len: "+str(len(token)))
    __token=token
    __chat_id=chat_id
    
def send_text(text,preview=True):
    if preview==True:
        disable_preview_text="False"#потому что дизейбл
    else:
        disable_preview_text="True"
    data = {"chat_id": __chat_id, "text": text,"parse_mode":"Markdown","disable_web_page_preview":disable_preview_text}
    url=req_prefix+__token+"/sendMessage"
    #print("url:"+url)
    #print("text:"+text)
    res=requests.post(url,data=data);
    return res

def send_image(caption,file):
    data = {"chat_id": __chat_id, "caption": caption}
    with open(file, "rb") as image_file:
        res=requests.post(req_prefix+__token+"/sendPhoto",data=data,files={"photo":image_file});
    return res