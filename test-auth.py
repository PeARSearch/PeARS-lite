from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/auth')
def auth():

    cookies = {'OMD_SESSION_ID': '1234'}
    data = {'username': 'omd', 
    'password': 'pwd'}
    url = 'http://localhost:9090/'
    resp = requests.post(url, data=data, cookies=cookies) #unless you need to set a user agent or referrer address you may not need the header to be added.
    r = app.make_response(resp.json())
    r.mimetype = "application/json"
    return r

@app.route('/api', methods=['POST'])
def api():
    def getuserinfo():
        print("Running getuserinfo")
        info = {'username':'kim', 'displayname':'kim', 'profileimage':'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P48/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==', 'email':'test@pearsproject.org', 'valid':'true'}
        r = app.make_response(jsonify(info))
        r.mimetype = "application/json"
        return r
   
    def signin():
        print("Running signin")
        info = {'username':'kim', 'displayname':'kim', 'profileimage':'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P48/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==', 'email':'test@pearsproject.org', 'valid':'true'}
        r = app.make_response(jsonify(info))
        return r

    print(request.json)
    action = request.json['action']
    print(action)
    if action == 'getUserInfo':
        r = getuserinfo()
        return r
    if action == 'signin':
        r = signin()
        r.set_cookie('OMD_SESSION_ID', '1234')
        r.mimetype = "application/json"
        return r


app.run(host='0.0.0.0', port=9191, debug=True)
