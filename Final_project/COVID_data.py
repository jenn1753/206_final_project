import json 
import requests
import os
import sqlite3
import matplotlib.pyplot as plt
import numpy as np

API_KEY = '9YA19ufyJHqrr6xZn8KqMg==EtbuNPSvSj7NEj3u'

# Covid data API __________________________________________

def get_covid_data(api_k, date):
    """
    Input: 
    API key and date string in format 'YYYY-MM-DD'
    
    Output: 
    Covid data in form of list of dictionaries containing global countries covid information for that date
        Format:
        [{'country': 'Afghanistan', 'region': '', 'cases': {'total': 157787, 'new': 42}}, {'country': 'Albania', 'region': '', 'cases': {'total': 205777, 'new': 228}}]
    """
    api_url = 'https://api.api-ninjas.com/v1/covid19?date={}'.format(date)
    response = requests.get(api_url, headers={'X-Api-Key': api_k})
    if response.status_code == requests.codes.ok:
        covid_data = response.json()
        return covid_data
    else:
        print("Error:", response.status_code, response.text)


def create_country_before_after_data_dict(before_data, after_data):
    """
    Input: 
    Two list of dictionaries, one for global covid data from the date before Christmas and one for global data from the date after Christmas
        Format:
        [{'country': 'Afghanistan', 'region': '', 'cases': {'total': 157787, 'new': 42}}, {'country': 'Albania', 'region': '', 'cases': {'total': 205777, 'new': 228}}]

    Output:
    Dictionary that contains country names as the keys and a dictionary containing that countries' increase in number of covid cases before Christmas and after Christmas as the values
        Format:
        {'country1': {'before':123, 'after':123}, 'country2': {'before':123, 'after':123}}

    """
    new_dict = {}
    for index in range(len(before_data)):
        new_dict[before_data[index]['country']] = {'before': before_data[index]['cases']['new'], 'after': after_data[index]['cases']['new']}
    return new_dict


# Country data API __________________________________________

API_KEY_2 = 'zCA4zeQDtprhKig1OKirLw==dFYnM8mjk65UenZ6'

def get_country_data(api_key, country):
    """
    Input: 
    API key and country name string
    
    Output: 
    A list of one dictionary containing the entered country's information
        Format:
        [{"name": "United States", "pop_growth": "0.6", "region": "Northern America","pop_density": "36.2", "internet_users": "87.3", "gdp_per_capita": "62917.9","fertility": "1.8"}]
    """
    api_url = 'https://api.api-ninjas.com/v1/country?name={}'.format(country)
    response = requests.get(api_url, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        country_data = response.json()
        return country_data
    else:
        return None
        
def get_regions(country_list):
    """
    Input:
    List of countries

    Output: 
    Dictionary containing country name as the keys and region category as the value
        Format:
        {'country':'region', 'country2':'region'}
    """
    regions = {}
    for x in country_list:
        country = get_country_data(API_KEY_2, x)
        if country != None and len(country) != 0:
            regions[x] = country[0]['region']
    return regions


def celebrated_pct_per_region(sorted_reg_covid_diff_data, region_dict, filename):
    """
    Input:
    A dictionary containing, in descending order, region names as keys and the total region differences of all covid increase data before christmas and after christmas

    A dictionary containing the country name as keys and the region category as the keys

    The file name of the json file holding a list of dictionaries containing country name and whether they celebrated Christmas (unofficially, yes, or no)
        Format: 
        [{"country": "Afghanistan", "celebrated": "No", "date": "-", "notes": "Christmas and Christianity are actively—and at times violently—discouraged by the current rulers of Afghanistan"}]

    Output:
    A dictionary containg the region name as the key and the percentage of all countries in region that celebrates Christmas (Yes and Unoffically) as values
        Format: 
        {'region_name': 90, 'region_name':88}
    """
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
        celebrated_pct = round(country_christmas_count / country_in_region_count, 2) * 100
        new_dict[region] = celebrated_pct
    return new_dict


def sorted_regional_covid_increase_difference(filtered_before_after_data, regions_dict):
    """ 
    Input: 
    A list of dictionaries containing countries that are confirmed to be in both the COVID and countries API as the keys and a dictionary containng their covid cases increase before christmas and covid cases increase after christmas as the values
        Format:
        {'country':{'before': 123, 'after':123}}
        
    A dictionary containing the country name as keys and the region category as the values

    Output:
    A dictionary containing, in descending order, region names as keys and the total region differences of all covid increase data before christmas and after christmas
    
    """
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

# Database ________________________________________

def setUpDatabase(db_name):
    """
    Input: 
    Database name (string)
    
    Output: 
    Creates cursor and connection variables and sets up empty database
    """
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


def create_region_table(cur, conn):
    """
    Input: 
    Cursor and connection variables
    
    Output: 
    Creates table regions_data with columns: region_id, region_name, and celebrate_pct (percent of region that celebrates Xmas)
    """
    cur.execute('create table if not exists region_data (region_id INTEGER PRIMARY KEY, region_name TEXT, celebrate_pct NUMBER)')
    conn.commit()

def create_country_id_table(cur, conn):
    """
    Input: 
    Cursor and connection variables
    
    Output: 
    Creates table country_ids with columns: country_id and country_name
    """
    cur.execute('create table if not exists country_ids (country_id INTEGER PRIMARY KEY, country_name TEXT)')
    conn.commit()


def create_country_table(cur, conn):
    """
    Input: 
    Cursor and connection variables
    
    Output: 
    Creates table country_data with columns: country_id and region_id
    """
    cur.execute('create table if not exists country_data (country_id INTEGER PRIMARY KEY, region_id INTEGER)')
    conn.commit()


def create_country_before_after_data_table(cur, conn):
    """
    Input: 
    Cursor and connection variables
    
    Output: 
    Creates table country_covid_data with columns: country_id, before_covid_data (cases reported before Xmas), after_covid_data (cases reported after Xmas)
    """
    cur.execute('create table if not exists country_covid_data (country_id INTEGER PRIMARY KEY, before_covid_data INTEGER, after_covid_data INTEGER)')
    conn.commit()



def add_region(cur, conn, sorted_covid_reg_diff_dict, celebrated_pct_per_region):
    """
    Input: 
    Cursor and connection variables

    A dictionary containing region names as keys and the total region differences of all covid increase data before christmas and after christmas

    A dictionary containg, in descending order, the region name as the key and the percentage of all countries in region that celebrates Christmas (Yes and Unoffically) as values
        Format: 
        {'region_name': 90, 'region_name':88}
    
    Output: 
    Populates region_data table with country_id, before_covid_data (cases reported before Xmas), and after_covid_data (cases reported after Xmas) for each country, limiting to 25 entries at a time
    """
    cur.execute('select max(region_id) from region_data')
    max_region_id = cur.fetchone()[0]
    if max_region_id == None:
        max_region_id = 0
    add_amount = len(sorted_covid_reg_diff_dict) - max_region_id
    
    if add_amount >= 25:
        count = 25  
    else:
        count = add_amount

    id = max_region_id + 1
    for region in list(sorted_covid_reg_diff_dict.keys())[max_region_id: max_region_id + count]:
        cur.execute('insert or ignore into region_data (region_id, region_name, celebrate_pct) values (?,?,?)', (id, region, celebrated_pct_per_region[region]))
        id += 1    
    conn.commit()


def add_country_ids(cur, conn, regions_dict):
    """
    Input: 
    Cursor and connection variables

    A dictionary containing the country name as keys and the region category as the values
    
    Output: 
    Populates country_ids table with country_id and country_name for each country, limiting to 25 entries at a time
    """
    cur.execute('select max(country_id) from country_ids')
    max_country_id = cur.fetchone()[0]
    if max_country_id == None:
        max_country_id = 0
    add_amount = len(regions_dict) - max_country_id
    
    if add_amount >= 25:
        count = 25
    else:
        count = add_amount

    id = max_country_id + 1
    for country in list(regions_dict.keys())[max_country_id: max_country_id + count]:
        cur.execute('insert or ignore into country_ids (country_id, country_name) values (?,?)', (id, country))
        id += 1    
    conn.commit()
    

def add_country(cur, conn, regions_dict):
    """
    Input:
    Cursor and connection variables

    A dictionary containing the country name as keys and the region category as the values

    Output:
    Populates region_data table with country_id and region_id for each country, limiting to 25 entries at a time
    """
    cur.execute('select max(country_id) from country_data')
    max_country_id = cur.fetchone()[0]
    if max_country_id == None:
        max_country_id = 0
    add_amount = len(regions_dict) - max_country_id
    
    if add_amount >= 25:
        count = 25 
    else:
        count = add_amount

    id = max_country_id + 1
    for country in list(regions_dict.keys())[max_country_id: max_country_id + count]:
        cur.execute('SELECT region_id from region_data where region_name=?', [regions_dict[country]])
        first_row = cur.fetchone()
        region_id = first_row[0]
        cur.execute('SELECT country_id from country_ids where country_name=?', [country])
        country_row = cur.fetchone()
        country_id = country_row[0]
        cur.execute('insert or ignore into country_data (country_id, region_id) values (?,?)', (country_id, int(region_id)))
        id += 1
    conn.commit()

    
def add_covid_info(cur, conn, filtered_covid_before_after_dict):
    """
    Input:
    Cursor and connection variables

    A list of dictionaries containing countries that are confirmed to be in both the COVID and countries API as the keys and a dictionary containng their covid cases increase before christmas and covid cases increase after christmas as the values
        Format:
        {'country':{'before': 123, 'after':123}}
    
    Output:
    Populates country_covid_data table with country_id, before xmas covid data, and after xmas covid data for each country, limiting to 25 entries at a time
    """
    cur.execute('select max(country_id) from country_covid_data')
    max_country_id = cur.fetchone()[0]
    if max_country_id == None:
        max_country_id = 0
    add_amount = len(filtered_covid_before_after_dict) - max_country_id

    if add_amount >= 25:
        count = 25 
    else:
        count = add_amount

    id = max_country_id + 1
    for country in list(filtered_covid_before_after_dict.keys())[max_country_id: max_country_id + count]:
        cur.execute('SELECT country_id from country_ids where country_name=?', [country])
        country_row = cur.fetchone()
        country_id = country_row[0]
        cur.execute('insert or ignore into country_covid_data (country_id, before_covid_data, after_covid_data) values (?,?,?)', (country_id, filtered_covid_before_after_dict[country]['before'], filtered_covid_before_after_dict[country]['after']))
        id += 1
    conn.commit()

#Calculations - writing out calculated data to a file _____________

def select_db_covid_data(cur, conn):
    """
    Input:
    Cursor and connection variables

    Output:
    Joins country_ids table and country_covid_data table on country_id column to create a list of tuples containing country name, number of COVID case increase before Christmas and the number of COVID case increase after Christmas 
        Format:
        [(country, 123, 123), (country, 123, 123)]

    """
    cur.execute('select country_ids.country_name, country_covid_data.before_covid_data, country_covid_data.after_covid_data from country_ids join country_covid_data on country_ids.country_id = country_covid_data.country_id')
    tup_list_country_covid_ba = cur.fetchall()
    return tup_list_country_covid_ba


def calc_db_covid_diff(tup_list_covid_data):
    """
    Input:
    A list of tuples containing country name, number of COVID case increase before Christmas and the number of COVID case increase after Christmas 
        Format:
        [(country, 123, 123), (country, 123, 123)]

    Output:
    A list of tuples containing country name and the difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas 
    """
    country_covid_diff = []
    for country in tup_list_covid_data:
        name = country[0]
        before = country[1]
        after = country[-1]
        diff = after - before
        tup = (name, diff)
        country_covid_diff.append(tup)
    return country_covid_diff

def region_country(cur, conn):
    """
    Input:
    Cursor and connection variables

    Output:
    Joins country_data table, region_data table, and country_ids table on country_id column and region_id column to create a list of tuples containing region name and country name 
        Format:
        [(region, country), (region, country)]

    """
    cur.execute('select region_data.region_name, country_ids.country_name from region_data join country_data on region_data.region_id = country_data.region_id join country_ids on country_data.country_id = country_ids.country_id')
    tup_list_country_region = cur.fetchall()
    return tup_list_country_region


def region_diff_dict(country_diff_tup_list, country_region_tup_list):
    """
    Input:
    A list of tuples containing country name and the difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas 
    
    A list of tuples containing region name and country name 
        Format:
        [(region, country), (region, country)]

    Output:
    A dictionary containing the region name as keys and the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region as values 

    """
    #(country, diff) . (region, country)
    d = {}
    for i in range(len(country_diff_tup_list)):
        country_diff = country_diff_tup_list[i][-1]
        region = country_region_tup_list[i][0]
        if region not in d:
            d[region] = country_diff
        else:
            d[region] += country_diff
    return d

def get_region_percent(cur, conn):
    """
    Input:
    Cursor and connection variables

    Output:
    A list of tuples containing region name and the percentage of the region that celebrates Christmas officially or unofficially
    Format:
        [(region, %), (region, %)] 
    """
    cur.execute('select region_data.region_name, region_data.celebrate_pct from region_data')
    x = cur.fetchall()
    return x

def prep_country_csv(tup_list_covid_data, country_covid_diff):
    """ 
    Input:
    A list of tuples containing country name, number of COVID case increase before Christmas and the number of COVID case increase after Christmas 
        Format:
        [(country, 123, 123), (country, 123, 123)]
        
    A list of tuples containing country name and difference between before and after Christmas Covid cases
        Format:
        [(country, 123), (country, 123)]
    Output:
    A list of tuples containing country name, number of COVID case increase before Christmas, number of COVID case increase after Christmas, and the difference between the two values
    Format:
        [(country, 123, 123, 123), (country, 123, 123, 123)]  
    """
    lst = []
    for i in range(len(tup_list_covid_data)):
        name = tup_list_covid_data[i][0]
        before = tup_list_covid_data[i][1]
        after = tup_list_covid_data[i][-1]
        diff = country_covid_diff[i][-1]
        lst.append((name, before, after, diff))
    return lst

def prep_region_csv(region_xmas_pct, region_diff_d):
    """
    Input:
    A list of tuples containing the region name and the percentage of countries within that region that either unofficially or does celebrate Christmas

    A dictionary containing the region names as the keys and the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region as the values
    
    Output:
    A list of tuples contaning the region name, the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region, and the percentage of countries within that region that either unofficially or does celebrate Christmas

    """
    lst = []
    for region_tup in region_xmas_pct:
        region = region_tup[0]
        total_diff = region_diff_d[region]
        pct = region_tup[-1]
        lst.append((region, total_diff, pct))
    return lst

    
def write_country_csv(file_name, prep_lst):
    """
    Input:
    The name of the file that will be created and written to
    
    A list of tuples contaning the region name, the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region, and the percentage of countries within that region that either unofficially or does celebrate Christmas
    
    Output:
    None, function writes country name, before christmas COVID cases increase, and after Christmas COVID cases increase, and the difference between before and after data into a csv file 
    """
    f = open(file_name, 'a')
    # new_lst = sorted(data, key=lambda x:x[1])
    header = 'Country, Before Christmas, After Christmas, Difference' + '\n'
    f.write(header)

    for tup in prep_lst:
        file_line = ''
        for i in range(len(tup)):
            if i < (len(tup) - 1):
                file_line += str(tup[i]) + ','
            else:
                file_line += str(tup[i]) + '\n'
        f.write(file_line)
    f.close()

def write_region_csv(file_name, prep_lst):
    """
    Input:
    File name (string)

    A list of tuples contaning the region name, the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region, and the percentage of countries within that region that either unofficially or does celebrate Christmas
    
    Output:
    None, function writes region name, the difference between before and after data, and the percentage of countries within that region that either unofficially or does celebrate Christmas into a csv file

    """
    f = open(file_name, 'a')
    # new_lst = sorted(data, key=lambda x:x[1])
    header = 'Region, Total COVID Difference, Celebrates Xmas (%)' + '\n'
    f.write(header)

    for tup in prep_lst:
        file_line = ''
        for item in tup:
            if item is not tup[-1]:
                file_line += str(item) + ','
            else:
                file_line += str(item) + '\n'
        f.write(file_line) 

    f.close()

# Visualizations _________________________________________

def sorted_covid_diff(country_covid_diff, tup_list_country_covid_ba):
    """
    Input:
    A list of tuples containing country name and the difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas 

    Joins country_ids table and country_covid_data table on country_id column to create a list of tuples containing country name, number of COVID case increase before Christmas and the number of COVID case increase after Christmas 
        Format:
        [(country, 123, 123), (country, 123, 123)]
    
    Output:
    A list of tuples that contains the top 15 countries based on their difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas, their number of COVID case increase before Christmas, and their number of COVID case increase after Christmas
    """
    sorted_15_coutries = sorted(country_covid_diff, key= lambda x:x[1], reverse=True)[:15]
    # print(sorted_15_coutries)
    ba_15_countries = []
    for country in sorted_15_coutries:
        for tup in tup_list_country_covid_ba:
            if country[0] == tup[0]:
                before = tup[1]
                after = tup[-1]
                tup = (country[0], before, after)
                ba_15_countries.append(tup)
    return ba_15_countries
     
    
def country_double_bc(ba_15_countries):
    """
    Input:
    A list of tuples that contains the top 15 countries based on their difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas, their number of COVID case increase before Christmas, and their number of COVID case increase after Christmas
    
    Output:
    A double bar chart Matplotlib visualization depicting before and after Covid data for the top 15 countries
    """
    N = 15
    width = 0.425
    ind = np.arange(N)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    y_vals_lst = []
    z_vals_lst = []
    countries_list_15 = []
    for country_ba in ba_15_countries:
        countries_list_15.append(country_ba[0])
        y_vals_lst.append(country_ba[1])
        z_vals_lst.append(country_ba[-1])

    yvals = y_vals_lst
    rects1 = ax.bar(ind, yvals, width, color='g')
    zvals = z_vals_lst
    rects2 = ax.bar(ind+width, zvals, width, color='r')

    ax.set(title='Comparing Top 15 Countries COVID Cases Increase Before and After Christmas')

    ax.set_ylabel('COVID Cases')
    ax.set_xticks(ind+(width/2))
    ax.set_xticklabels(tuple(countries_list_15))
    ax.legend( (rects1[0], rects2[0]), ('Before Christmas', 'After Christmas') )

    def autolabel(rects):
        for rect in rects:
            h = rect.get_height()
            ax.text(rect.get_x()+rect.get_width()/2., 1.05*h, '%d'%int(h),
                    ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    plt.show()

def sorted_region_diff(reg_diff_d):
    """
    Input:
    A dictionary containing the region name as keys and the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region as values 

    Output:
    A list of tuples that contains the top 5 regions based on their difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas

    """
    tup_lst = []
    sorted_5_regions = sorted(reg_diff_d, key= lambda x:reg_diff_d[x], reverse=True)[:5]
    for reg in sorted_5_regions:
        tup_lst.append((reg, reg_diff_d[reg]))
    return tup_lst


def region_diff_single_bc(sorted_5_regions_lst):
    """
    Input:
    A list of tuples that contains the top 5 regions based on their difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas  

    Output:
    A bar chart Matplotlib visualization depicting the top 5 regions with the highest difference in covid cases before and after Christmas
    """
    regions_lst = []
    ba_diff_lst = []
    for tup in sorted_5_regions_lst:
        regions_lst.append(tup[0])
        ba_diff_lst.append(tup[1])
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    regions = regions_lst
    diff = ba_diff_lst
    x = np.arange(len(regions)) # the label locations
    width = 0.7 # the width of the bars
    fig, ax = plt.subplots()
    ax.set_ylabel('Total Difference')
    ax.set_xlabel('Regions')
    ax.set_title('Total Regional Differences in COVID Cases Increase Before and After Xmas')
    ax.set_xticks(x-(width/2))
    ax.set_xticklabels(regions)
    pps = ax.bar(x - width / 2, diff, width, label='diff', color='blue')
    for p in pps:
        height = p.get_height()
        ax.text(x=p.get_x() + p.get_width() / 2, y=height+.10,
        s="{}".format(height),
        ha='center')
    plt.show()

def sorted_5_region_diff(reg_diff_d, reg_pct_tup_lst):
    """
    Input:
    A dictionary containing the region name as keys and the sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region as values

    A list of tuples containing region name, sum of the difference of COVID cases increase before Christmas and COVID cases increase after Christmas for the countries in the region as values, percentage of countries in that region that celebrates Christmas

    Output:
    A list of tuples that contains the top 5 regions based on their difference in number of COVID case increase before Christmas, the number of COVID case increase after Christmas, and the percentage of countries in that region that celebrates Christmas
    """

    tup_lst = []
    sorted_regions = sorted(reg_diff_d, key= lambda x:reg_diff_d[x], reverse=True)[:5]

    for reg in sorted_regions:
        for tup in reg_pct_tup_lst:
            if reg == tup[0]:
                pct = tup[-1]
                tup_lst.append((reg, reg_diff_d[reg], pct))
    return tup_lst

def celebrates_pie_chart(reg_5_lst):
    """
    Input:
    A list of tuples that contains the top 5 regions based on their difference in number of COVID case increase before Christmas and the number of COVID case increase after Christmas and the percentage of each region that celebrates Christmas 

    Output:
    A pie chart Matplotlib visualization depicting the percentage of the top 5 regions with the highest difference in covid cases before and after Christmas that celebrate Christmas
    """
    celebrates = 0
    for reg in reg_5_lst:
        if reg[-1] == 100:
            celebrates += 1
    no_celebrate = 5 - celebrates

    labels = 'Celebrates', 'Does Not Celebrate'
    sizes = [celebrates, no_celebrate]
    explode = (0, 0)  # only "explode" the 1st slice

    fig1, ax1 = plt.subplots()

    ax1.set_title('Top 5 Regions % Celebrates Christmas')
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=False, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.show()


# Main Function __________________________________________

def main():
    c19_data_before = get_covid_data(API_KEY, '2021-12-19')
    c19_data_after = get_covid_data(API_KEY, '2021-12-31')
    before_after_dict = create_country_before_after_data_dict(c19_data_before, c19_data_after)
    country_list = list(before_after_dict.keys())
    regions_dict = get_regions(country_list)  

    filtered_before_after_dict = {}
    for country in country_list:
        if country in regions_dict.keys():
            filtered_before_after_dict[country] = before_after_dict[country]

    regional_covid_increase_diff_dict = sorted_regional_covid_increase_difference(filtered_before_after_dict, regions_dict)

    celebrated_reg_pct = celebrated_pct_per_region(regional_covid_increase_diff_dict, regions_dict, 'countries_celebrate_christmas.json')

    cur, conn = setUpDatabase('MerryCovid.db')

    create_region_table(cur, conn)
    create_country_id_table(cur, conn)
    create_country_table(cur, conn)
    create_country_before_after_data_table(cur, conn)

    add_region(cur, conn, regional_covid_increase_diff_dict, celebrated_reg_pct)
    add_country_ids(cur, conn, regions_dict)
    add_country(cur, conn, regions_dict)
    add_covid_info(cur, conn, filtered_before_after_dict)

    tup_list_covid_ba = select_db_covid_data(cur, conn)
    country_covid_diff = calc_db_covid_diff(tup_list_covid_ba)
    region_country_tup_list = region_country(cur, conn)
    reg_diff_d = region_diff_dict(country_covid_diff, region_country_tup_list)
    reg_pct_tup_list = get_region_percent(cur, conn)

    country_prep = prep_country_csv(tup_list_covid_ba, country_covid_diff)
    region_prep = prep_region_csv(reg_pct_tup_list, reg_diff_d)

    write_country_csv('countries.csv', country_prep)
    write_region_csv('regions.csv', region_prep)

    ba_15_countries = sorted_covid_diff(country_covid_diff,  tup_list_covid_ba)
    country_double_bc(ba_15_countries)

    sorted_5_regions = sorted_region_diff(reg_diff_d)
    region_diff_single_bc(sorted_5_regions)

    reg_10_lst = sorted_5_region_diff(reg_diff_d, reg_pct_tup_list)
    celebrates_pie_chart(reg_10_lst)

main()  