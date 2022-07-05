import sys
import time
import datetime
from turtle import bgcolor
import requests as req
import json

from sympy import arg

index = 0
try:
    index = int(sys.argv[len(sys.argv)-1]) # возможно порядковый номер понадобится для партиционирования
except:
    pass

baseUrl = "http://127.0.0.1:8181/" #"http://127.0.0.1:8181/" | "http://192.168.4.19:8181/"
timeoutTrys = 60 * 10
networkReTrys = 50
maxStartSleep = 10
waitsleep = 1.5


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(*args):
    print(bcolors.UNDERLINE,  datetime.datetime.now().isoformat(), bcolors.ENDC, *args)


def update(stage, status, duration, comment):
    print(
        "UPDATE", 
        stage,  
        ("success" if status else "failed") if type(status) is bool else status, 
        duration.total_seconds(), 
        comment)

def step(stage, prefix):
    start = datetime.datetime.now()
    try:
        status, comment = prefix()
    except Exception as err:
        status, comment = "error", json.dumps(str(err))
    stop = datetime.datetime.now()
    update(stage, status, stop-start, comment)
    return status


def sendReq(code, thread="", token="", params={}):
    cntTrys = 0
    lastError = None
    while cntTrys < networkReTrys:
        try:
            return req.post(baseUrl, data={"code" : code, "streamreciver" : thread, "token" : token, "params" : json.dumps(params)})
        except Exception as e:
            log(e)
            cntTrys += 1
            lastError = e
            time.sleep(waitsleep)
    raise lastError

def sendGet(guid):

    cntTrys = 0
    lastError = None
    while cntTrys < networkReTrys:
        try:
            return req.get(baseUrl, params={"id": guid})
        except Exception as e:
            log(e)
            cntTrys += 1
            lastError = e
            time.sleep(waitsleep)
    raise lastError

         


def sendGetWhilePending(guid, prefix):
    finish = False
    cntTrys = 0
    while not finish:
        resp = sendGet(guid)
        body = resp.json()
        log(prefix, resp.status_code, resp.reason, json.dumps(body))
        time.sleep(waitsleep)
        if 'result' not in body or body['result'] != -1:
            return body
        cntTrys += 1
        if cntTrys > timeoutTrys:
            return None


class User:
    def loginSend(self, login="test", password="test"):
        resp = sendReq(code="CMS.LOGIN", params={"userName": login, "password": password})
        if resp.status_code != 200:
            return False, "томкат мёртв("
        self.loginGuid = resp.text
        return True, self.loginGuid

    def loginGet(self):
        result = sendGetWhilePending(self.loginGuid, 'loginGet')
        if result is None:
            return "timeout", ""
        
        if result["result"] == 0:
            return False, json.dumps(result, ensure_ascii=False)

        self.token = result['token']
        return True, self.token

    def logout(self):
        sendReq(code="CMS.LOGOUT", token=self.token)
        return True, self.token

    def cnCreateSend(self):
        resp = sendReq(code="CN.CREATE", params={"type_id": "db-pg"}, token=self.token)
        self.cnCreteGuid = resp.text
        return True, self.cnCreteGuid

    def cnCreateGet(self):
        result = sendGetWhilePending(self.cnCreteGuid, 'cnCreateGet')
        if result is None:
            return "timeout", ""
        
        if result["result"] == 0:
            return False, json.dumps(result, ensure_ascii=False)

        self.createdConnector = result

        self.createdConnector["header"]["name"] = "connector-"+ str(index)
        self.createdConnector["data"]["fields"] = [
            {
                "fieldKey": "SERVER",
                "fieldName": "Имя или IP сервера",
                "required": True,
                "type": "string",
                "value": "192.168.4.148"
            },
            {
                "fieldKey": "PORT",
                "fieldName": "Порт",
                "required": True,
                "type": "number",
                "value": 5432
            },
            {
                "fieldKey": "DATABASE",
                "fieldName": "Название Базы, SID, Имя сервиса",
                "required": True,
                "type": "string",
                "value": "TA"
            },
            {
                "fieldKey": "UID",
                "fieldName": "Логин",
                "required": True,
                "type": "string",
                "value": "test_usr"
            },
            {
                "fieldKey": "PWD",
                "fieldName": "Пароль",
                "required": True,
                "type": "string",
                "value": "1"
            },
            {
                "fieldKey": "external",
                "fieldName": "Дополнительные параметры",
                "required": False,
                "type": "string",
                "value": None
            }
        ]

        return True, self.createdConnector["header"]["id"]

    def cnSaveSend(self):
        resp = sendReq(code="CN.SAVE", params=self.createdConnector, token=self.token)
        self.lastGuid = resp.text
        return True, self.lastGuid
    
    def cnSaveGet(self):
        result = sendGetWhilePending(self.lastGuid, 'cnSaveGet') 
        if result is None:
            return "timeout", ""
        
        if result["result"] == 0:
            return False, json.dumps(result, ensure_ascii=False)
        
        return True, ""
    
    def cnOpenSend(self):
        resp = sendReq(code="CN.OPEN", params={"id": self.createdConnector["header"]["id"]}, token=self.token)
        self.lastGuid = resp.text
        return True, self.lastGuid
    
    def cnOpenGet(self):
        result = sendGetWhilePending(self.lastGuid, 'cnOpenGet') 
        if result is None:
            return "timeout", ""
        
        if result["result"] == 0:
            return False, json.dumps(result, ensure_ascii=False)
        

        if "header" not in result or "name" not in result["header"] or result["header"]["name"] != self.createdConnector["header"]["name"]:
            return "не совпадает", json.dumps(result, ensure_ascii=False)

        return True, ""

    def cnTablesListSend(self):
        resp = sendReq(code="CN.GET_OBJECTS", params={"id": self.createdConnector["header"]["id"]}, token=self.token)
        self.lastGuid = resp.text
        return True, self.lastGuid

    def cnTablesListGet(self):
        result = sendGetWhilePending(self.lastGuid, 'cnTablesListGet') 
        if result is None:
            return "timeout", ""
        
        if result["result"] == 0:
            return False, json.dumps(result, ensure_ascii=False)
    

        return True, json.dumps(result, ensure_ascii=False)

import random;


def randSleep():
    duration = random.random() * maxStartSleep
    time.sleep(duration)
    return True, str(duration) + ";" + datetime.datetime.now().isoformat()


step("start_sleep", randSleep)

user = User()
loginStatus = step("CMS.LOGIN", user.loginSend)
if loginStatus == True:
    loginStatus = step("CMS.LOGIN_RES", user.loginGet)

if loginStatus == True:
    connectorCreated = step("CN.CREATE", user.cnCreateSend)

    if connectorCreated == True:
        connectorCreated = step("CN.CREATE_RES", user.cnCreateGet)

    if connectorCreated == True:
        connectorCreated = step("CN.SAVE", user.cnSaveSend)

    if connectorCreated == True:
        connectorCreated = step("CN.SAVE_RES", user.cnSaveGet)

    if connectorCreated == True:
        openStart = step("CN.OPEN", user.cnOpenSend)
        if openStart == True:
            connectorCreated = step("CN.OPEN_RES", user.cnOpenGet)
    
    if connectorCreated == True:
        openStart = step("CN.GET_OBJECTS", user.cnTablesListSend)
        if openStart == True:
            connectorCreated = step("CN.GET_OBJECTS_RES", user.cnTablesListGet)

if loginStatus == True:
    step("CMS.LOGOUT", user.logout)

# print("UPDATE", 0, "success", 0, "мой id -- это", index)
# print("всякий бред можно писать -- он попадёт в лог, но не в итоговый результат")
# start = datetime.datetime.now()
# time.sleep(index)
# stop = datetime.datetime.now()
# print("UPDATE", "первый_слип", "success", -(start-stop).total_seconds())
# start = datetime.datetime.now()
# print(1, index)
# time.sleep(index)
# stop = datetime.datetime.now()
# print("UPDATE", "второй_слип", "статус_может_быть_неожиданным", -(start-stop).total_seconds())
# print(2, index)