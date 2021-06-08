import sys
import requests
import os

class Resolver(object):
    '''
    Resolver() performs string substitutions based on a dict of replacement values.
    Initial replacement values are used for ShiftLeft API calls and pulled
    from well-known environment variables that contain the API token and
    organization id.  Other replacement values can be passed into the resolve()
    method if desired.

    Template strings take the form of normal Python strings, and replacements
    are performed on the string, such that substrings like '{<key>}' will be
    replaced with the value of <key> in the dict.

    The initial replacement dict contains:
    authHDR => 'Bearer '+<API TOKEN>
    api_base => 'https://www.shiftleft.io/api/v4'
    orgID => <ORGANIZATION ID>

    For example, a template string of 'Organization id: {orgID}' will resolve
    to 'Organization id: <value of SHIFTLEFT_ORG_ID environment variable>'.

    Environment variables used:
    SHIFTLEFT_API_TOKEN
    SHIFTLEFT_ORG_ID
    '''
    def __init__(self):
        # Pull our ShiftLeft secrets from the environment
        api_token = os.environ['SHIFTLEFT_API_TOKEN']
        org_id = os.environ['SHIFTLEFT_ORG_ID']

        self.vars = {
            'authHDR': 'Bearer '+api_token,
            'api_base': 'https://www.shiftleft.io/api/v4',
            'orgID': org_id,
        }

    def resolve(self, template, **extra):
        '''
        resolve() performs string substitutions on input variable template
        if **extra keyword parameters are included, they will be merged with
        the replacement dict prior to performing the substitutions.
        '''
        _vars = {}
        _vars.update(self.vars)
        _vars.update(extra)

        x = template
        for k,v in _vars.items():
            x = x.replace('{'+k+'}', v)
        return x

resolver = Resolver()

# Headers used for all ShiftLeft API calls
api_headers = {
    'Authorization': resolver.vars['authHDR'],
}

def make_url(template, **extra):
    '''
    A helper function that prepares a full URL for an API endpoint

    Parameters:
    template is the string upon which substitutions will be performed.
    **extra keyword arguments will be available for replacements in
    the template string.

    Return value:
    template with substitutions performed
    '''
    return resolver.resolve('{api_base}'+template, **extra)

def get_app_id(appname):
    '''
    Function to get the application id for the application whose name matches
    appname.

    Parameters:
    appname: the name of the application whose id to return

    Return value:
    The application id of the application whose name matches appname
    '''

    # Prepare the URL for the API endpoint
    url = make_url('/orgs/{orgID}/apps')

    # Perform a GET request to that endpoint, including necessary auth info
    r = requests.get(url, headers=api_headers)
    # Raise exception on error
    r.raise_for_status()

    # Extract the id of the named app
    id = [x['id'] for x in r.json()['response'] if x['name']==appname][0]

    return id

def get_crit_findings(appid):
    '''
    Function to get a list of critical findings in the application whose id is appid.

    Parameters:
    appid: The application id of the application whose findings to return

    Return value:
    A list of critical findings in the application with id, appid.
    '''

    # Prepare the URL for the API endpoint
    # Include the appid passed to this function
    url = make_url('/orgs/{orgID}/apps/{appID}/findings', appID=appid)

    # Additional filters for the API call:
    # severity == 'critical'
    # Include 249 entries per page, which is the maximum, to minimize the
    # chance of overflow.
    filters = {
        'severity': 'critical',
        'per_page': 249,
    }

    # Perform a GET request to the appropriate endoint, including appropriate
    # parameters and auth info
    r = requests.get(url, params=filters, headers=api_headers)
    # Raise exception on error
    r.raise_for_status()

    if r.json().get('next_page'):
        print('!!! Warning: results truncated to 249 findings')
        # TODO: Although out of scope for this exercise, should handle multi-page output

    # Return just the relevant part of the API response
    findings = r.json()['response']['findings']
    return findings

#####################################################################

def usage():
    print('usage: %s <app_name>\n')

if __name__ == '__main__':
    # Make sure we are given an application name upon which to act
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    # Get the id of the application name passed on the command line
    app_id = get_app_id(sys.argv[1])

    # Get a list of critical findings for that application
    crit_findings = get_crit_findings(app_id)

    # Make a list of the id and title of each finding, sorted by id
    crit_findings = sorted([ (x['id'],x['title']) for x in crit_findings])

    # Format the output
    crit_findings = [ '#%s %s'%x for x in crit_findings ]
    if crit_findings:
        print('Critical severity findings:')
        print( '\n'.join(crit_findings) )
