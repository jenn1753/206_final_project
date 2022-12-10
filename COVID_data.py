import json 
import requests

API_KEY = '9YA19ufyJHqrr6xZn8KqMg==EtbuNPSvSj7NEj3u'

# Covid data API __________________________________________

def get_covid_data(api_k, date):
    """Takes in API key and country to get covid data in form of list"""
    api_url = 'https://api.api-ninjas.com/v1/covid19?date={}'.format(date)
    response = requests.get(api_url, headers={'X-Api-Key': api_k})
    if response.status_code == requests.codes.ok:
        covid_data = response.json()
        return covid_data
    else:
        print("Error:", response.status_code, response.text)
    
# c19_data = get_covid_data(API_KEY, '2021-12-25')
# print(c19_data)

c19_data_before = get_covid_data(API_KEY, '2021-12-19')
c19_data_after = get_covid_data(API_KEY, '2021-12-31')

def create_country_before_after_data_dict(before_data, after_data):
    new_dict = {}
    for index in range(len(before_data)):
        new_dict[before_data[index]['country']] = {'before': before_data[index]['cases']['new'], 'after': after_data[index]['cases']['new']}
    return new_dict

before_after_dict = create_country_before_after_data_dict(c19_data_before, c19_data_after)


# def get_covid_increase_for_date(covid_data, input_date):
#     """Takes in covid data and date returns number of new cases for the date entered"""
#     for date in covid_data[0]['cases'].keys():
#         if input_date == date:
#           return covid_data[0]['cases'][date]['new']
    

# print(get_covid_increase_for_date(c19_data, '2021-01-01'))
# month_covid_data = get_covid_data_for_month(c19_data, '2021', '05')

# def get_month_covid_increase(covid_month_data):
#     """Takes in dict containing covid data for the month and returns total increase in covid cases for month's covid data"""
#     total_increase = 0
#     for day_data in covid_month_data.values():
#         total_increase += day_data['new']
#     return total_increase

# covid_month_increase = get_month_covid_increase(month_covid_data)


# Holidays data API __________________________________________
API_KEY_2 = 'zCA4zeQDtprhKig1OKirLw==dFYnM8mjk65UenZ6'

def get_holiday_data(api_key, country, year):
    api_url = 'https://api.api-ninjas.com/v1/holidays?country={}&year={}'.format(country, year)
    response = requests.get(api_url, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        holiday_data = response.text
        return holiday_data
    else:
        print("Error:", response.status_code, response.text) 

# print(get_holiday_data(API_KEY_2, 'US', '2021'))   



def main():
    c19_data = get_covid_data(API_KEY, 'US')
    print(c19_data)
    month_covid_data = get_covid_increase_for_date(c19_data, '2021', '05')
    covid_month_increase = get_month_covid_increase(month_covid_data)
    # print(covid_month_increase)
    holidays = get_holiday_data(API_KEY_2, 'US', '2021')
    print(holidays)

main()



    




