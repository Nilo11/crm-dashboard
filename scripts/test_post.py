import requests
url='http://127.0.0.1:5000/api/leads'
samples=[
    {'name':'Test User','email':'testuser1@example.com','phone':'','company':'Acme','value':100,'status':'New','notes':'from api test'},
    {'name':'Test User2','email':'testuser2@example.com','phone':'+919876543210','company':'Beta','value':200,'status':'New','notes':'from api test'}
]
for p in samples:
    r=requests.post(url,json=p)
    print(p['email'], r.status_code, r.text)
