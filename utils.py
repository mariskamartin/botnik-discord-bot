from datetime import datetime, timedelta
import calendar
import random
import giphy_client
from giphy_client.rest import ApiException
import requests
import const


def get_random_giphy_url(tag='hello'):
  api = giphy_client.DefaultApi()
  api_key = 'Q5rqo6PTqOJRVOjyDeQuhPMUdY0XjJSH'
  try: 
    api_response = api.gifs_search_get(api_key, tag, limit=20, offset=0, rating='g', lang='en', fmt='json')
    return random.choice(api_response.data).url
#    api_response = api.gifs_random_get(api_key=api_key, tag=tag, rating='g', fmt='json')
#    return api_response.data.url
  except ApiException as e:
    print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)


def months_add(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime(year, month, day)


def parse_mention_id(mention: str):
  ''' 
    parse user or role mention <@796009503904628767> z mob a <@!796009503904628767> z ntb  
  '''
  if mention.startswith('<@') and mention.endswith('>'):
    mention = mention[2:-1]
    if mention.startswith('!') or mention.startswith('&'):
      mention = mention[1:]
  return int(mention)


def has_valid_predplatne(db_user):
  return db_user['predplatne_start'] < datetime.utcnow() < db_user['predplatne_end']


def last_day_of_month(date):
  if date.month == 12:
    return date.replace(day=31)
  return date.replace(month=date.month+1, day=1) - timedelta(days=1)


_mtgi2_last_update_date = None


async def fetch_mtgi2(_channel_bot_logs, force_update = False):
  if datetime.utcnow().strftime(const.D_FORMAT) == globals()['_mtgi2_last_update_date'] and not force_update:
    print('skipping for now fetch_mtgi2')
    return
  globals()['_mtgi2_last_update_date'] = datetime.utcnow().strftime(const.D_FORMAT)

  try:
    r = requests.get('http://mtgi.hopto.org')
    fetched = requests.get(f'{r.url}/rest/dci/fetch/editions/AFR,AFE,MH2,M2E,IKO,IKE', timeout=600)
    json = fetched.json()
    await _channel_bot_logs.send(f'aktualizováno mtgi2 (t:{fetched.elapsed} #:{len(json)})')
  except Exception as e:
    globals()['_mtgi2_last_update_date'] = None
    print(e)

