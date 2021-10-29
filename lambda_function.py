import json
import os
import requests
import boto3
import xlwt


def lw_auth():
    keyid = os.environ.get("LW_KEYID")
    secretkey = os.environ.get("LW_SECRETKEY")
    baseurl = "%s%s" % (os.environ.get("LW_BASEURL"), "/api/v2/access/tokens")

    myheader = {
        'X-LW-UAKS': "{}".format(secretkey), 'Content-Type': 'application/json'}
    mybody = json.dumps({'keyId': "{}".format(keyid), "expiryTime": 3600})
    r = requests.post(baseurl, headers=myheader, data=mybody)

    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json',
                     'Authorization': 'Bearer {}'.format(r.json()['token'])})
    return s


def get_report(lw_session):
    cfgurl = "%s%s" % (os.environ.get("LW_BASEURL"),
                       "/api/v1/external/integrations/type/AWS_CFG")

    reports = []
    aws_cfg = lw_session.get(cfgurl)
    for c in aws_cfg.json()['data']:
        reporturl = "%s%s%s%s" % (os.environ.get(
            "LW_BASEURL"), "/api/v1/external/compliance/aws/GetLatestComplianceReport?AWS_ACCOUNT_ID=", c['DATA']['AWS_ACCOUNT_ID'], "&FILE_FORMAT=json")
        reports.append(lw_session.get(reporturl).json())
    return reports


def lambda_handler(event, context):

    lw_session = lw_auth()
    all_reports = get_report(lw_session)

    #s3 = boto3.resource("s3")
    #rpt_object = s3.Object('lw-hennessy-reports', 'report-test/myfile.txt')
    #rpt_object.put(Body=json.dumps(mydata.json(), indent=4))

    return {
        'statusCode': 200,
        'body': all_reports[0]
    }


if __name__ == "__main__":
    print(lambda_handler("hi", "hi"))
