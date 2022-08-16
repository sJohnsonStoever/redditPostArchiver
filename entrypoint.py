import os
import yaml

# load credentials file
cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.yml')
credentials = yaml.load(open(cred_path), Loader=yaml.SafeLoader)

# input credentials from environment variables
try:
    credentials['client_id'] = os.environ['CLIENT_ID']
    credentials['client_secret'] = os.environ['CLIENT_SECRET']
except KeyError:
    print('Missing credentials!')


# save updated credentials
with open(cred_path, 'w') as cred_file:
    cred_file.write(yaml.dump(credentials))