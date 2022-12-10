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

def create_country_before_after_data_dict(before_data, after_data):
    new_dict = {}
    for index in range(len(before_data)):
        new_dict[before_data[index]['country']] = {'before': before_data[index]['cases']['new'], 'after': after_data[index]['cases']['new']}
    return new_dict


# Country data API __________________________________________

API_KEY_2 = 'zCA4zeQDtprhKig1OKirLw==dFYnM8mjk65UenZ6'

def get_country_data(api_key, country):
    api_url = 'https://api.api-ninjas.com/v1/country?name={}'.format(country)
    response = requests.get(api_url, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        country_data = response.json()
        return country_data
    else:
        return None
        
def get_regions(country_list):
    regions = []
    for x in country_list:
        country = get_country_data(API_KEY_2, x)
        #print(country)
        if len(country) != 0:
            regions.append(country[0]['region'])
    print(regions)
    return regions



# Main Function __________________________________________

def main():
    c19_data_before = get_covid_data(API_KEY, '2021-12-19')
    c19_data_after = get_covid_data(API_KEY, '2021-12-31')
    before_after_dict = create_country_before_after_data_dict(c19_data_before, c19_data_after)
    country_list = list(before_after_dict.keys())
    #print(country_list)
    get_regions(country_list)   

main()  


    




