import httplib2
import os.path
import datetime
import re
import json
import requests
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from oauth2client import client
from oauth2client.file import Storage
from oauth2client import tools

class CalendarPost:

    # コンストラクタ
    def __init__ (self):
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.service = None
        self.calendars = []
        self.events = []
        creds = None
    
       # incomming webhook用url取得
        with open('webhookurl.json','r') as f:
           json_load = json.load(f)

           self.url = json_load["URL"]
       
       # アクセス認証
        store = Storage("calendar_credential.json")
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets("client_secrets.json", SCOPES)
            flow.user_agent = "LR_Drive"
            creds = tools.run_flow(flow, store)
    
        # カレンダーへの認証
        http = creds.authorize(httplib2.Http())
        self.service = discovery.build('calendar','v3',http=http)

    # カレンダーの取得
    def GetCalendar(self):
        result = self.service.calendarList().list().execute()
        for calendar in result['items']:
            self.calendars.append(calendar['summary'])
        print(self.calendars)

    # イベント取得
    def GetTodayEvent(self):
        now = datetime.datetime.now()
        time_min = now.date().isoformat() + 'T00:00:00+09:00:00' # 'Z' indicates UTC time
        time_max = (now.date()+datetime.timedelta(days=1)).isoformat() + 'T00:00:00+09:00:00'

        for calendar in self.calendars:
            result = self.service.events().list(calendarId=calendar,timeMax=time_max,timeMin=time_min,timeZone='Asia/Tokyo',singleEvents=True,orderBy='startTime').execute()
            
            for event in result.get('items',[]):
                self.events.append(event)
        
        # イベントのソート
        self.events = sorted(self.events, key=lambda x:x['start'].get('dateTime'))

    def PostSlack(self):
        message = "今日の予定は次の通りです\n"

        if not self.events:
            message = "今日の予定はありません\nゆっくりしていってね"
        for event in self.events:
            start = event['start'].get('dateTime')
            line = re.split('[+T]',start)
            message = message + line[1] + " " + event['summary'] + "\n"
        print(message)

        requests.post(self.url, data=json.dumps({
            "text" : message,
        }))

if __name__ == "__main__":
    calendar = CalendarPost()
    calendar.GetCalendar()
    calendar.GetTodayEvent()
    calendar.PostSlack()
