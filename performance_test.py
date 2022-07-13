import time
import csv
from geo_dp_functions import getQueryParts, noisy_sql_response
import geopandas as gpd
import psycopg2
#import pydp as dp
from configparser import ConfigParser
from geo_dp_functions import noisy_sql_response, getNoisyPoints, getQueryPoints, testquery
import matplotlib.pyplot as plt
import numpy as np
from itertools import product
import sys
import config_file
from shapely import geometry

def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()

        epsilon = 100
        datapoint_attribute = 'loc'
        remove_extreme_points = False
        noisy_points = True
        noisy_result = True
        with open('query_list.csv', newline='') as f:
            reader = csv.reader(f)
            query_list = [x[0] for x in reader]#list(reader)
            #print(query_list)
        with open('query_list_postgis.csv', newline='') as f:
            reader = csv.reader(f)
            query_list_postgis = [x[0] for x in reader]#list(reader)
            #print(query_list_postgis)

        noisy_responses, responses = compare_noise_without(query_list, query_list_postgis, datapoint_attribute, conn, epsilon, remove_extreme_points, noisy_points, noisy_result)
        print("Comparison noise or without noise: ", noisy_responses, responses)
        
        response_extreme, response_points, response_result = compare_noise_options(query_list, datapoint_attribute, conn, epsilon)
        print("Options result: ", response_extreme, response_points, response_result)
	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    return noisy_responses, responses

def compare_noise_without(query_list, query_list_postgis, datapoint_attribute, conn, epsilon, remove_extreme_points, noisy_points, noisy_result):
        meantime_noisy_list = []
        meantime_wo_noise_list = []
        #execute all queries of query_list with noise
        noisy_responses = []
        for query in query_list:
            print("********************QUERY****************************")
            print(query)
            #execute each query 10 times and calculate the mean
            for l in range(1, 31):
                time_noisy = 0
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, remove_extreme_points, noisy_points, noisy_result)
                end = time.time()
                t = end - start
                time_noisy += t
            noisy_responses.append(response)
            meantime_noisy = time_noisy/30
            meantime_noisy_list.append(meantime_noisy)
        print("**********************************************************")
        print("meantime_noisy_list: ", meantime_noisy_list)
        print("**********************************************************")

        #execute all queries of query_list without noise
        responses = []
        for query in query_list_postgis:
            print("********************QUERY****************************")
            for l in range (1, 31):
                time_wo_noise = 0
                start = time.time()
                type_select = query.split()[1].lower().split('(')[0]
                response = gpd.read_postgis(query, conn, geom_col=type_select)
                #response = gpd.GeoDataFrame.from_postgis(query, conn)#, geom_col=datapoint_attribute)
                end = time.time()
                t = end - start
                time_wo_noise += t
            meantime_wo_noise = time_wo_noise/30
            meantime_wo_noise_list.append(meantime_wo_noise)
            responses.append(response)
        print("**********************************************************")
        print("meantime_wo_noise_list: ", meantime_wo_noise_list)
        print("**********************************************************")

        labels = ['BB100', 'BB1000', 'Centroid100', 'Centroid1000', 'Union100', 'Union1000']

        x = np.arange(len(labels))  # the label locations
        width = 0.35  # the width of the bars
        plt.xticks(rotation=45)
        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width/2, meantime_noisy_list, width, label='With noise')
        rects2 = ax.bar(x + width/2, meantime_wo_noise_list, width, label='Without noise')

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Execution time')
        ax.set_title('With and without noise')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)

        fig.tight_layout()
        plt.show()
        return noisy_responses, responses

def compare_noise_options(query_list, datapoint_attribute, conn, epsilon):
        meantime_delete_extreme = []
        meantime_noisy_points = []
        meantime_noisy_result = []
        #execute all queries of query_list with noise
        noisy_responses_extreme = []
        noisy_responses_points = []
        noisy_responses_result = []
        for query in query_list[:2]:
            print("********************QUERY****************************")
            print(query)
            #execute each query 10 times and calculate the mean
            for l in range(1, 31):
                #only deleting extreme points
                time_extreme = 0
                start = time.time()
                response_extreme = noisy_sql_response(query, datapoint_attribute, conn, epsilon, True, False, False)
                end = time.time()
                t = end - start
                time_extreme += t

                #only noising points 
                time_points = 0
                start = time.time()
                response_points = noisy_sql_response(query, datapoint_attribute, conn, epsilon, False, True, False)
                end = time.time()
                t = end - start
                time_points += t

                #only noising points 
                time_result = 0
                start = time.time()
                response_result = noisy_sql_response(query, datapoint_attribute, conn, epsilon, False, False, True)
                end = time.time()
                t = end - start
                time_result += t

            noisy_responses_extreme.append(response_extreme)
            meantime_extreme = time_extreme/30
            meantime_delete_extreme.append(meantime_extreme)

            noisy_responses_points.append(response_points)
            meantime_points = time_points/30
            meantime_noisy_points.append(meantime_points)

            noisy_responses_result.append(response_result)
            meantime_result = time_result/30
            meantime_noisy_result.append(meantime_result)

        print("**********************************************************")
        print("meantime_delete_extreme: ", meantime_delete_extreme)
        print("**********************************************************")

        print("**********************************************************")
        print("meantime_noisy_points: ", meantime_noisy_points)
        print("**********************************************************")

        print("**********************************************************")
        print("meantime_noisy_result: ", meantime_noisy_result)
        print("**********************************************************")

        labels = ['BB100', 'BB1000']

        x = np.arange(len(labels))  # the label locations
        width = 0.15  # the width of the bars
        plt.xticks(rotation=45)
        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width, meantime_delete_extreme, width, label='Delete Extreme Points')
        rects2 = ax.bar(x, meantime_noisy_points, width, label='Noise Points')
        rects3 = ax.bar(x + width, meantime_noisy_result, width, label='Noise Result')

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Execution time')
        ax.set_title('Options to obfuscate data')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)
        ax.bar_label(rects3, padding=3)

        fig.tight_layout()
        plt.show()
        return response_extreme, response_points, response_result


if __name__ == '__main__':
    noisy_responses, responses = connect()
    print(noisy_responses)
    print(responses)


def sql_response(query, datapoint_attribute, conn):
    #points relevant to query
    points = getQueryPoints(query, datapoint_attribute, conn)
    #print("points wo noise: ", points)

    geo_df = gpd.GeoDataFrame(points, crs="EPSG:4326")
    select_query =  getQueryParts(query)[0].lower()
    if "st_envelope" in select_query:
        result = geo_df.dissolve().total_bounds
           
    elif "st_centroid" in select_query:
        result = geo_df.dissolve().centroid[0]

    elif "st_union" in select_query:
        print(geo_df.longitude)
        result = geometry.Polygon([[p.x, p.y] for p in geo_df])
        
    else:
        result = ""
        print("ERROR: No geo spacial method found in SELECT-part.")
    print("Result: ")
    return result