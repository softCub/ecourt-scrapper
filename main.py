from bs4 import BeautifulSoup
import requests

url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/"

page = requests.get(url)

soup=BeautifulSoup(page.text,'html')

soup=soup.find_all('select').find_all('option')
state=[]
for option in state:
    print(option)
