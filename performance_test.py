import time
import csv
from geo_dp_functions import noisy_sql_response
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

        epsilon = 1.0
        datapoint_attribute = "loc"
        remove_extreme_points = True
        noisy_points = True
        noisy_result = True
        with open('file.csv', newline='') as f:
            reader = csv.reader(f)
            query_list = list(reader)
        meantime_noisy_list = [] #besser als df zusammen mit row with und without noise?
        meantime_wo_noise_list = []#^^^^^^^^^^^^
        conn = "" #muss noch hinzugefügt bzw. übergeben werden

        #execute all queries of query_list with noise
        for query in query_list:
            #execute each query 10 times and calculate the mean
            for l in range (1, 11):
                time_noisy = 0
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, remove_extreme_points, noisy_points, noisy_result)
                end = time.time()
                t = end - start
                time_noisy += t
            meantime_noisy = time_noisy/query_list.len()
            meantime_noisy_list.append(meantime_noisy)
        print("meantime_noisy_list: ", meantime_noisy_list)

        #execute all queries of query_list without noise
        for query in query_list:
            for l in range (1, 11):
                time_wo_noise = 0
                start = time.time()
                response = gpd.GeoDataFrame.from_postgis(query, conn, datapoint_attribute)
                end = time.time()
                t = end - start
                time_wo_noise += t
            meantime_wo_noise = time_wo_noise/query_list.len()
            meantime_wo_noise_list.append(meantime_wo_noise)
        print("meantime_wo_noise_list: ", meantime_wo_noise_list)

        labels = ['Bounding Box', 'Geometric Center', 'Union']
        #men_means = [20, 34, 30, 35, 27]
        #women_means = [25, 32, 34, 20, 25]

        x = np.arange(len(labels))  # the label locations
        width = 0.35  # the width of the bars

        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width/2, meantime_noisy_list, width, label='With noise')
        rects2 = ax.bar(x + width/2, meantime_wo_noise_list, width, label='Without noise')

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Execution time')
        ax.set_title('Query')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)

        fig.tight_layout()

        plt.show()
   
	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


if __name__ == '__main__':
    connect()







    