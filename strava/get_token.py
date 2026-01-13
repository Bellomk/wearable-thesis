import requests

client_id = "ENTER-YOUR-CLIENT-ID-HERE"
client_secret = 'ENTER-YOUR-CLIENT-SECRET-KEY-HERE'
code = 'ENTER-YOUR-CODE-HERE'

url = "https://www.strava.com/oauth/token"
data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'code': code,
    'grant_type': 'authorization_code'
}

response = requests.post(url, data=data)
token_data = response.json()

print("Full Token:", token_data)
print("Access Token:", token_data['access_token'])
print("Refresh Token:", token_data['refresh_token'])