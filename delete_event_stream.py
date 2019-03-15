import sys
import requests

# AMP 3rd Party API Client ID
AMP_CLIENT_ID = 'a1b2c3d4e5f6g7h8i9j0'

# AMP API Key
AMP_API_KEY = 'a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6'

def verify_auth(session):
    '''Verify which AMP cloud the provided client_id and api_key are valid for.
        Return the Domain and Region Name for the cloud the credentials are valid in.
    '''
    region_domains = {'api.amp.cisco.com':'North America',
                      'api.apjc.amp.cisco.com':'Asia',
                      'api.eu.amp.cisco.com':'Europe'
                     }

    for named_domain in region_domains:
        version_url = 'https://{}/v1/version'.format(named_domain)
        response = session.get(version_url)

        if response.status_code == 200:
            return named_domain, region_domains[named_domain]

    sys.exit('It doesn\'t look like the credentials you provided are valid in any region')

def get_streams(session, domain):
    '''Get existing event streams
    '''
    url = 'https://{}/v1/event_streams'.format(domain)
    response = session.get(url)
    response_json = response.json()
    data = response_json['data']
    return data

def delete_stream(session, domain, stream_id):
    '''Delete an event stream
    '''
    url = 'https://{}/v1/event_streams/{}'.format(domain, stream_id)
    headers = {'accept': 'application/json',
               'content-type': 'application/json',
               'Accept-Encoding': 'gzip, deflate'
               }

    if not confirm_continue():
        sys.exit("Bye!")

    response = session.delete(url, headers=headers)
    return response

def ask_for_stream_id(valid_ids):
    '''Ask the user for a Stream ID
       Keep asking until they enter a valid Stream ID
    '''
    while True:
        reply = str(input('Enter the ID of the stream you would like to delete: ')).strip()
        if reply in valid_ids:
            return reply
        sys.stdout.write('\x1b[1A')
        sys.stdout.write('\x1b[2K')
        sys.stdout.write('{} is not a valid stream ID try again.\n'.format(reply))

def confirm_continue():
    '''Ask the user if they want to continue
       Keep asking until they enter 'y', 'Y', 'n', or 'N'
    '''
    while True:
        reply = str(input('Are you sure you want to continue?'+' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            return True
        if reply[:1] == 'n':
            return False

def main():
    '''The main script logic
    '''

    # Instantiate a session object with authentication
    amp_session = requests.Session()
    amp_session.auth = (AMP_CLIENT_ID, AMP_API_KEY)

    # Check which cloud the credentials are valid in
    domain, region = verify_auth(amp_session)

    # Output which region will be used
    print('Successfully authenticated to: {}\n'.format(region))

    # Query the API for existing Event Streams
    stream_data = get_streams(amp_session, domain)
    streams = {str(stream['id']):stream['name'] for stream in stream_data}

    # Verify that you want to continue
    print('-=== WARNING THIS SCRIPT WILL DELETE THINGS ===-')
    if not confirm_continue():
        sys.exit("Bye!")

    # Exit if there are no existing Event Streams
    if not streams:
        sys.exit('There are no streams to delete')

    # Print existing Event Streams to the console
    print('{:>3} {:>12}'.format('ID', 'Name'))
    for stream_id, stream_name in streams.items():
        print('{} - {}'.format(stream_id, stream_name))

    # Ask for the Event Stream ID to delete
    to_delete = ask_for_stream_id(streams)

    # Delete the Event Stream
    delete_response = delete_stream(amp_session, domain, to_delete)

    # Check if errors were returned
    if delete_response.status_code // 100 != 2:
        reason = delete_response.json()['errors'][0]['details'][0]
        sys.exit('\nFailed to create stream: {}'.format(reason))

    print('Request to delete {} sent Successfully'.format(to_delete))

if __name__ == '__main__':
    main()
