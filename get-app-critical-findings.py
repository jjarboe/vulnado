import sys
import requests
import os

api_token = os.environ['SHIFTLEFT_API_TOKEN']
org_id = os.environ['SHIFTLEFT_ORG_ID']

vars = {
    'authHDR': 'Bearer '+api_token,
    'api_base': 'https://www.shiftleft.io/api/v4',
    'orgID': org_id,
}

def resolve(x, **extra):
    global vars

    _vars = {}
    _vars.update(vars)
    _vars.update(extra)

    for k,v in _vars.items():
        x = x.replace('{'+k+'}', v)
    return x

def make_url(x, **extra):
    return resolve('{api_base}'+x, **extra)

def get_app_id(appname):
    url = make_url('/orgs/{orgID}/apps')

    r = requests.get(url, headers={'Authorization': vars['authHDR']})
    r.raise_for_status()

    id = [x['id'] for x in r.json()['response'] if x['name']==appname][0]

    return id

def get_crit_findings(appid):
    url = make_url('/orgs/{orgID}/apps/{appID}/findings', appID=appid)

    filters = {
        'severity': 'critical',
        'per_page': 249,
    }

    r = requests.get(url, params=filters, headers={'Authorization': vars['authHDR']})
    r.raise_for_status()

    if r.json().get('next_page'):
        print('Warning: results may be incomplete')

    findings = r.json()['response']['findings']
    return findings

def usage():
    print('usage: %s <app_name>\n')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    app_id = get_app_id(sys.argv[1])
    crit_findings = get_crit_findings(app_id)
    crit_findings = sorted([ (x['id'],x['title']) for x in crit_findings])
    crit_findings = [ '#%s %s'%x for x in crit_findings ]
    if crit_findings:
        print('Critical severity findings:')
        print( '\n'.join(crit_findings) )
