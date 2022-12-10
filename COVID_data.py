import json 
import requests

API_KEY = '9YA19ufyJHqrr6xZn8KqMg==EtbuNPSvSj7NEj3u'


def get_covid_data(api_k, country):
    """Takes in API key and country to get covid data in form of list"""
    api_url = 'https://api.api-ninjas.com/v1/covid19?country={}'.format(country)
    response = requests.get(api_url, headers={'X-Api-Key': api_k})
    if response.status_code == requests.codes.ok:
        covid_data = response.json()
        return covid_data
    else:
        print("Error:", response.status_code, response.text)
    
c19_data = get_covid_data(API_KEY, 'US')
# print(c19_data)

def get_covid_data_for_month(covid_data, year_str, month_str):
    """Takes in covid data, year string and month string and returns dict of covid data for entered month and year"""
    new_covid_data_dict = {}
    for date in covid_data[0]['cases'].keys():
        if f'{year_str}-{month_str}' in date:
          new_covid_data_dict[date] = covid_data[0]['cases'][date]
    return new_covid_data_dict 

# print(get_covid_data_for_month(c19_data, '2021', '05'))
month_covid_data = get_covid_data_for_month(c19_data, '2021', '05')

def get_month_covid_increase(covid_month_data):
    """Takes in dict containing covid data for the month and returns total increase in covid cases for month's covid data"""
    total_increase = 0
    for day_data in covid_month_data.values():
        total_increase += day_data['new']
    return total_increase

covid_month_increase = get_month_covid_increase(month_covid_data)



    




