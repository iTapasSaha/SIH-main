import torch
from googletrans import Translator
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from transformers import BartTokenizer, BartForConditionalGeneration
from flask_mysqldb import MySQL
from flask import Flask,render_template,url_for
from flask import request as req
#flaskfrom newspaper import Article
import urllib.request
from flask_mysqldb import MySQL
import requests
import textwrap

from bs4 import BeautifulSoup
from hashlib import new
from ntpath import join
import mysql.connector
from dateutil import parser
url1="https://pib.gov.in/Allrel.aspx"
r=requests.get(url1)
htmlContent=r.content

soup=BeautifulSoup(htmlContent,'html.parser')

target=soup.find('div',class_="content-area")
anchors=target.find_all('a')
all_links=list()

z=0
j=0
i=0


     
     
for link in anchors:




    
    
    if(link.get('href').startswith('/PressRelease')):
         linkText="https://pib.gov.in"+link.get('href')
         all_links.insert(i,linkText)
    else:
         all_links.insert(i,link.get('href')) 
    i=i+1

    
    db=mysql.connector.connect(user="root",password="monkey123",database="piblinks")
    cursor= db.cursor()
    url = all_links[j]
   

#opening the url for reading
    html = urllib.request.urlopen(url)
  
#parsing the html file
    htmlParse = BeautifulSoup(html, 'html.parser')


#for extracting date and time
    datetime1=htmlParse.find('div', {'class':"ReleaseDateSubHeaddateTime text-center pt20"})
    datetime2=datetime1.get_text()
    res = parser.parse(datetime2+"UTC-5", fuzzy=True,)
    computed_date= str(res)[:10]
    ministry_name=htmlParse.find('div', {'class':"MinistryNameSubhead text-center"})
    ministry_name=ministry_name.get_text()
    target1=htmlParse.find('div', {'class':"innner-page-main-about-us-content-right-part"})
    target2=target1.find('h2')
    mainheading=target2.get_text()
    
    if (len(mainheading)<100):

        a=mainheading
    else:
        b = len(mainheading)/3
        str1  = textwrap.shorten(mainheading, width=b, placeholder='....')
        a=str1
    
   
    add_links=("INSERT IGNORE INTO Press_releases( LINKS,Post_Date,ministry,headings) VALUES( %s,%s,%s,%s)")
    
    data_links=(all_links[j],computed_date,ministry_name,a)
    
    cursor.execute(add_links,data_links)


   
    db.commit()
    
    
    cursor.close()
    db.close()
    j=j+1
def header(url):
    html = urllib.request.urlopen(url)
# parsing the html file
    htmlParse = BeautifulSoup(html, 'html.parser')
#for extracting heading
    target1=htmlParse.find('div', {'class':"innner-page-main-about-us-content-right-part"})
    target2=target1.find('h2')
    mainheading=target2.get_text()
    return(mainheading)

def datetime(url):
    html = urllib.request.urlopen(url)
# parsing the html file
    htmlParse = BeautifulSoup(html, 'html.parser')
    datetime1=htmlParse.find('div', {'class':"ReleaseDateSubHeaddateTime text-center pt20"})
    datetime2=datetime1.get_text()
    return(datetime2)

def summarize(url):
    html = urllib.request.urlopen(url)
    # parsing the html file
    htmlParse = BeautifulSoup(html, 'html.parser')
    target=htmlParse.find('div')
    paras=target.find_all('p')

    arr = []    

    for para in paras:
        out=para.get_text()
        arr.append(out)

    list2 = "\n\n".join(arr)
    

    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

    ARTICLE_TO_SUMMARIZE = list2 

    inputs = tokenizer([ARTICLE_TO_SUMMARIZE], max_length=1024, return_tensors="pt")
    summary_ids = model.generate(inputs["input_ids"], num_beams=2, min_length=200, max_length=300)
    summary = tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        #return(summary)

    model_name = 'tuner007/pegasus_paraphrase'
    torch_device = 'cuda' if torch.cuda.is_available() else 'cpu'
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    model = PegasusForConditionalGeneration.from_pretrained(model_name).to(torch_device)

    def get_response(input_text,num_return_sequences):
        batch = tokenizer.prepare_seq2seq_batch([input_text],truncation=True,padding='longest',max_length=60, return_tensors="pt").to(torch_device)
        translated = model.generate(**batch,max_length=60,num_beams=10, num_return_sequences=num_return_sequences, temperature=1.5)
        tgt_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
        return tgt_text

    # Paragraph of text
    context = summary

    # Takes the input paragraph and splits it into a list of sentences
    from sentence_splitter import SentenceSplitter, split_text_into_sentences

    splitter = SentenceSplitter(language='en')

    sentence_list = splitter.split(context)
    #sentence_list

    # Do a for loop to iterate through the list of sentences and paraphrase each sentence in the iteration
    paraphrase = []

    for i in sentence_list:
        a = get_response(i,1)
        paraphrase.append(a)

    # This is the paraphrased text
    #paraphrase

    paraphrase2 = [' '.join(x) for x in paraphrase]
    #paraphrase2

    # Combines the above list into a paragraph
    paraphrase3 = [' '.join(x for x in paraphrase2) ]
    paraphrased_text = str(paraphrase3).strip('[]').strip("'")
    return(paraphrased_text)
    #paraphrased_text

def translate_hindi(url_content):
    translator = Translator()
    result = translator.translate(url_content , dest="hi")
    return (result.text)
def translate_tamil(url_content):
    translator = Translator()
    result = translator.translate(url_content,dest="ta")
    return (result.text)
    
def translate_bengali(url_content):
    translator = Translator()
    result = translator.translate(url_content, dest="bn")
    return (result.text)
    
def translate_marathi(url_content):
    translator = Translator()
    result = translator.translate(url_content, dest="mr")
    return (result.text)
def translate_telegu(url_content):
    translator = Translator()
    result = translator.translate(url_content, dest="te")
    return (result.text)
    




app = Flask(__name__)
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='monkey123'
app.config['MYSQL_DB']='piblinks'
mysql=MySQL(app)
@app.route("/",methods=["GET","POST"])

def Index():
    if req.method == "POST":
        url = req.form.get("submit")
        
        date_content = datetime(url)
        url_content = summarize(url)
        header_content = header(url)
        translate_text1=translate_hindi(url_content)
        translate_text2=translate_tamil(url_content)
        translate_text3=translate_bengali(url_content)
        translate_text4=translate_marathi(url_content)
        translate_text5=translate_telegu(url_content)
        return render_template("test.html",value1=header_content,value3=date_content,value2=url_content,value4=translate_text1,value5=translate_text2,value6=translate_text3,value7=translate_text4,value8=translate_text5)
    cur=mysql.connection.cursor()
    cur.execute("SELECT * from press_releases")
            
    data=cur.fetchall()
    cur.close()
    return render_template("home1.html",press_releases = data)
    
# def press_releases():
#         if req.method == "POST":
#             url = req.form.get("submit")
#             #return render_template("main1.html",value1=url)

#         cur=mysql.connection.cursor()
#         cur.execute("SELECT * from press_releases")
            
#         data=cur.fetchall()
#         cur.close()
#         return render_template("home1.html",press_releases = data)

if __name__ == "__main__":
    app.run(debug=True)