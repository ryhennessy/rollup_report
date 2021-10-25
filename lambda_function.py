import json
import os
import requests
import boto3

def lw_auth():
   keyid = os.environ.get("LW_KEYID")
   secretkey = os.environ.get("LW_SECRETKEY")
   baseurl="%s%s" % (os.environ.get("LW_BASEURL"), "/api/v2/access/tokens")

   myheader={'X-LW-UAKS': "{}".format(secretkey), 'Content-Type': 'application/json'} 
   mybody=json.dumps({'keyId': "{}".format(keyid), "expiryTime": 3600})
   r=requests.post(baseurl, headers=myheader, data=mybody)
   
   sheader={'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(r.json()['token'])}
   s=requests.Session()
   s.headers.update({'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(r.json()['token'])})
   return s

def lambda_handler(event, context):
    lw_session=lw_auth()

    mydata=lw_session.get("https://lwint-se.lacework.net/api/v2/AlertRules")
    
    
    s3 = boto3.resource("s3")
    rpt_object = s3.Object('lw-hennessy-reports', 'report-test/myfile.txt')
    rpt_object.put(Body=json.dumps(mydata.json(), indent=4))  

    return {
        'statusCode': 200,
        'body': json.dumps(mydata.json())
    }

if __name__ == "__main__":
   print(lambda_handler("hi","hi"))

