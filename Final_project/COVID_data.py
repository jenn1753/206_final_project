import json 
import requests
import os
import sqlite3
import matplotlib.pyplot as plt

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
    regions = {}
    for x in country_list:
        country = get_country_data(API_KEY_2, x)
        #print(country)
        if len(country) != 0:
            regions[x] = country[0]['region']
    return regions

#create new dict with regions being the keys and the dict of combined covid data for before and after being the values
#example dict : {'region': {total_regional_before_data: 123, total_regional_after_data: 123}}

def sorted_regional_covid_increase_difference(filtered_before_after_data, regions_dict):
    new_dict = {}
    for country in regions_dict:
        region = regions_dict[country]
        if region not in new_dict.keys():
            new_dict[region] = 0
        before_after_country_diff = filtered_before_after_data[country]['after'] - filtered_before_after_data[country]['before']
        new_dict[region] += before_after_country_diff
    sorted_region_list = sorted(new_dict, key= lambda x:new_dict[x], reverse=True)
    sorted_new_dict = {}
    for reg in sorted_region_list:
        sorted_new_dict[reg] = new_dict[reg]
    return sorted_new_dict

#go through filtered list of countries
#count how many countries are in each region total
#count how many countries celebrate christmas officially and unofficially combined for the region
#For each region, divide num of countries celebrated over total countries in region
#create new dictionary in form of {region: percent_celerate %}

def celebrated_pct_per_region(sorted_reg_covid_diff_data, region_dict, filename):
    f = open(os.path.abspath(os.path.join(os.path.dirname(__file__), filename)))
    file_data = f.read()
    f.close()
    christmas_celebrated_data = json.loads(file_data)
    new_dict = {}
    for region in sorted_reg_covid_diff_data:
        country_in_region_count = 0
        for country in region_dict:
            if region_dict[country] == region:
                country_in_region_count += 1
        country_christmas_count = 0
        for country2 in christmas_celebrated_data:
            if country2['country'] in region_dict.keys() and country2['celebrated'] in ['Yes', 'Unofficially']:
                if region_dict[country2['country']] == region:
                    country_christmas_count += 1
        celebrated_pct = round(country_christmas_count / country_in_region_count, 2) 
        new_dict[region] = celebrated_pct
    return new_dict


#data coding 0, 1, 2

# Database ________________________________________

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


# create region id and region table
def create_region_table(cur, conn):
    cur.execute('create table if not exists region_data (region_id INTEGER PRIMARY KEY, region_name TEXT, celebrate_pct NUMBER)')
    conn.commit()

#create country and region id table
def create_country_table(cur, conn):
    cur.execute('create table if not exists country_data (country_name TEXT PRIMARY KEY, region_id INTEGER)')
    conn.commit()

#create country and covid data of before and after
def create_country_before_after_data_table(cur, conn):
    cur.execute('create table if not exists country_covid_data(country_name TEXT PRIMARY KEY, before_covid_data INTEGER, after_covid_data INTEGER)')
    conn.commit()

#add region information to table
def add_region(cur, conn, sorted_covid_reg_diff_dict, celebrated_pct_per_region):
    id = 1
    for region in sorted_covid_reg_diff_dict.keys():
        cur.execute('insert or ignore into region_data (region_id, region_name, celebrate_pct) values (?,?,?)', (id, region, celebrated_pct_per_region[region]))
    # cur.execute('Select jobs.job_title, employees.salary from employees join jobs on jobs.job_id = employees.job_id')
        id += 1
    
    conn.commit()
    
#add country information to table
def add_country(cur, conn, regions_dict):
    for country in regions_dict:
        cur.execute('SELECT region_id from region_data where region_name=?', (regions_dict[country]))
        region_id = cur.fetchone()[0]
        cur.execute('insert or ignore into country_data (country_name, region_id) values (?,?)', (country, int(region_id)))
        conn.commit()

#add covid information to table
def add_covid_info(cur, conn, filtered_covid_before_after_dict):
    for country in filtered_covid_before_after_dict.keys():
        cur.execute('insert or ignore into country_covid_data (country_name, before_covid_data, after_covid_data) values (?,?,?)', (country, filtered_covid_before_after_dict[country]['before'], filtered_covid_before_after_dict[country]['after']))
    conn.commit()


# Main Function __________________________________________

def main():
    c19_data_before = get_covid_data(API_KEY, '2021-12-19')
    c19_data_after = get_covid_data(API_KEY, '2021-12-31')
    before_after_dict = create_country_before_after_data_dict(c19_data_before, c19_data_after)
    # print(before_after_dict)
    country_list = list(before_after_dict.keys())
    #print(country_list)
    regions_dict = get_regions(country_list)  
    # print(regions_dict) 


    filtered_before_after_dict = {}
    for country in country_list:
        if country in regions_dict.keys():
            filtered_before_after_dict[country] = before_after_dict[country]

    regional_covid_increase_diff_dict = sorted_regional_covid_increase_difference(filtered_before_after_dict, regions_dict)
    # print(regional_covid_increase_diff_dict)


    # sorted_reg_covid_diff_data, region_dict, filename
    celebrated_reg_pct = celebrated_pct_per_region(regional_covid_increase_diff_dict, regions_dict, 'countries_celebrate_christmas.json')
    # print(celebrated_reg_pct)

    cur, conn = setUpDatabase('MerryCovid.db')

    create_region_table(cur, conn)
    create_country_table(cur, conn)
    create_country_before_after_data_table(cur, conn)

    add_region(cur, conn, regional_covid_increase_diff_dict, celebrated_reg_pct)
    add_country(cur, conn, regions_dict)
    add_covid_info(cur, conn, filtered_before_after_dict)

    # cur.execute('drop table if exists country_covid_data')

main()  