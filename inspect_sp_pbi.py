import requests
import json

url = "https://www.transparencia.sp.gov.br/Home/ExecutaLicita"
response = requests.get(url, verify=False)
print("Status Code:", response.status_code)
print("Conteúdo:")
print(response.text[:1000])
