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
        single_report=lw_session.get(reporturl).json() 
        if single_report['ok'] != False:
            reports.append(single_report)
    return reports


def build_spreadsheet(all_reports):
    ws = {}
    wb = xlwt.Workbook()

    header = xlwt.easyxf(
        'font: bold true, height 240;'
        'align: horizontal center;'
        'pattern: pattern solid, fore_colour gray25;')
    boldline = xlwt.easyxf('font: bold true, height 240;')
    resline = xlwt.easyxf('font: height 200, colour blue_gray;')

    for acc in all_reports:
        acc = acc['data'][0]
        reportname = "%s" % (acc['accountId'])
        reporttitle = "%s %s" % (acc['accountAlias'], acc['accountId'])

        ws[reportname] = wb.add_sheet(reportname)

        ws[reportname].col(0).width = 35 * 256
        ws[reportname].col(1).width = 115 * 256
        ws[reportname].col(2).width = 25 * 256
        ws[reportname].col(3).width = 11 * 256
        ws[reportname].col(4).width = 11 * 256
        ws[reportname].col(5).width = 11 * 256

        ws[reportname].write(0, 0, reporttitle, boldline)
        ws[reportname].write(2, 0, "ID", header)
        ws[reportname].write(2, 1, "Recommendation", header)
        ws[reportname].write(2, 2, "Status", header)
        ws[reportname].write(2, 3, "Severity", header)
        ws[reportname].write(2, 4, "Affected", header)
        ws[reportname].write(2, 5, "Assessed", header)

        row = 3
        for rec in acc['recommendations']:
            rec.setdefault('VIOLATIONS', [])
            titlelink = 'HYPERLINK("{}", "{}")'.format(
                rec['INFO_LINK'], rec['TITLE'].replace('"', ""))
            ws[reportname].write(row, 0, rec['REC_ID'], boldline)
            ws[reportname].write(row, 1, xlwt.Formula(titlelink), boldline)
            ws[reportname].write(row, 2, rec['STATUS'], boldline)
            ws[reportname].write(row, 3, rec['SEVERITY'], boldline)
            ws[reportname].write(row, 4, len(rec['VIOLATIONS']),boldline)
            ws[reportname].write(row, 5, rec['ASSESSED_RESOURCE_COUNT'], boldline)
            row += 1
            if len(rec['VIOLATIONS']) > 0:
                for affected in rec['VIOLATIONS']:
                    affected.setdefault('resource', '')
                    if affected['resource'] != "":
                        row += 1
                        ws[reportname].write(row, 1, affected['resource'], resline)
                row += 1

        wb.save("/tmp/testing.xls")


def save_report():
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file('/tmp/testing.xls', 'lw-hennessy-reports', 'compliance-reports/latest.xls')
    

def lambda_handler(event, context):
    lw_session = lw_auth()
    all_reports = get_report(lw_session)
    build_spreadsheet(all_reports)
    #save_report()

    return {
        'statusCode': 200,
        'body': 'allgood'
    }


if __name__ == "__main__":
    print(lambda_handler("hi", "hi"))
