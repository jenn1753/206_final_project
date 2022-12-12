import json 
import requests
import os
import sqlite3
import matplotlib.pyplot as plt
import numpy as np

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
        if country != None and len(country) != 0:
            regions[x] = country[0]['region']
    return regions


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
        celebrated_pct = round(country_christmas_count / country_in_region_count, 2) * 100
        new_dict[region] = celebrated_pct
    return new_dict

#not sure if we want to remove later on?
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

def create_country_id_table(cur, conn):
    cur.execute('create table if not exists country_ids (country_id INTEGER PRIMARY KEY, country_name TEXT)')
    conn.commit()

#create country and region id table
def create_country_table(cur, conn):
    cur.execute('create table if not exists country_data (country_id INTEGER PRIMARY KEY, region_id INTEGER)')
    conn.commit()

#create country and covid data of before and after
def create_country_before_after_data_table(cur, conn):
    cur.execute('create table if not exists country_covid_data (country_id INTEGER PRIMARY KEY, before_covid_data INTEGER, after_covid_data INTEGER)')
    conn.commit()

#add region information to table

def add_region(cur, conn, sorted_covid_reg_diff_dict, celebrated_pct_per_region):
    cur.execute('select max(region_id) from region_data')
    max_region_id = cur.fetchone()[0]
    # print(max_country_id)
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
    
#add country information to table
def add_country(cur, conn, regions_dict):
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

    

#add covid information to table
def add_covid_info(cur, conn, filtered_covid_before_after_dict):
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
    #joins country_ids table and country_covid_data table on country_id column
    cur.execute('select country_ids.country_name, country_covid_data.before_covid_data, country_covid_data.after_covid_data from country_ids join country_covid_data on country_ids.country_id = country_covid_data.country_id')
    tup_list_country_covid_ba = cur.fetchall()
    return tup_list_country_covid_ba


#spike for each country - differences between before and after
def calc_db_covid_diff(tup_list_covid_data):
    country_covid_diff = []
    for country in tup_list_covid_data:
        name = country[0]
        before = country[1]
        after = country[-1]
        diff = after - before
        tup = (name, diff)
        country_covid_diff.append(tup)
    return country_covid_diff

#function that gets region name and country name
def region_country(cur, conn):
    cur.execute('select region_data.region_name, country_ids.country_name from region_data join country_data on region_data.region_id = country_data.region_id join country_ids on country_data.country_id = country_ids.country_id')
    tup_list_country_region = cur.fetchall()
    return tup_list_country_region

#function that takes in list of tuples w country, diff  +  list of tuples w country name and region name?
#output : [(region_name, total_region_diff), (region_name, total_region_diff)]
def region_diff_dict(country_diff_tup_list, country_region_tup_list):
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

#function that gets region percent that celebrates christmas
def get_region_percent(cur, conn):
    cur.execute('select region_data.region_name, region_data.celebrate_pct from region_data')
    x = cur.fetchall()
    return x

def prep_country_csv(tup_list_covid_data, country_covid_diff):
    lst = []
    for i in range(len(tup_list_covid_data)):
        name = tup_list_covid_data[i][0]
        before = tup_list_covid_data[i][1]
        after = tup_list_covid_data[i][-1]
        diff = country_covid_diff[i][-1]
        lst.append((name, before, after, diff))
    return lst

def prep_region_csv(region_xmas_pct, region_diff_d):
    lst = []
    for region_tup in region_xmas_pct:
        region = region_tup[0]
        total_diff = region_diff_d[region]
        pct = region_tup[-1]
        lst.append((region, total_diff, pct))
    return lst

    
def write_country_csv(file_name, prep_lst):
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
    sorted_15_coutries = sorted(country_covid_diff, key= lambda x:x[1], reverse=True)[:15]
    print(sorted_15_coutries)
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
    rects1 = ax.bar(ind, yvals, width, color='r')
    zvals = z_vals_lst
    rects2 = ax.bar(ind+width, zvals, width, color='g')

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


cur, conn = setUpDatabase('MerryCovid.db')
tup_list_covid_ba = select_db_covid_data(cur, conn)
country_covid_diff = calc_db_covid_diff(tup_list_covid_ba)
ba_15_countries = sorted_covid_diff(country_covid_diff,  tup_list_covid_ba)
country_double_bc(ba_15_countries)

def sorted_region_diff(reg_diff_d):
    tup_lst = []
    sorted_5_regions = sorted(reg_diff_d, key= lambda x:reg_diff_d[x], reverse=True)[:5]
    for reg in sorted_5_regions:
        tup_lst.append((reg, reg_diff_d[reg]))
    return tup_lst


def region_diff_single_bc(sorted_5_regions_lst):

    regions_lst = []
    ba_diff_lst = []
    for tup in sorted_5_regions_lst:
        regions_lst.append(tup[0])
        ba_diff_lst.append(tup[1])

    # x = regions_lst
    # y = ba_diff_lst

    # plt.bar(x,y,label="Region",color="blue")

    # plt.xlabel("Regions")
    # plt.ylabel("Total Difference")
    # plt.title("Total Regional Differences in COVID cases Before and After Xmas")
    # plt.legend()
    # plt.show()

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
    # plt.bar(color="blue")
    for p in pps:
        height = p.get_height()
        ax.text(x=p.get_x() + p.get_width() / 2, y=height+.10,
        s="{}".format(height),
        ha='center')
    plt.show()

# cur, conn = setUpDatabase('MerryCovid.db')
# tup_list_covid_ba = select_db_covid_data(cur, conn)
# country_covid_diff = calc_db_covid_diff(tup_list_covid_ba)
# region_country_tup_list = region_country(cur, conn)
# reg_diff_d = region_diff_dict(country_covid_diff, region_country_tup_list)
# region_diff_single_bc(sorted_region_diff(reg_diff_d))



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

main() 
