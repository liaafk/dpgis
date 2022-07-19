import time
from geo_dp_functions import noisy_sql_response
import geopandas as gpd
import psycopg2
from configparser import ConfigParser
import matplotlib.pyplot as plt
import numpy as np
import cProfile

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
    # Connect to the PostgreSQL database server 
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()

        # setting test parameters
        epsilon = 15
        datapoint_attribute = 'loc'
        repetitions = 1000
        # drops the upper and lower percentile, needs to be lower than 0,5
        drop_percentile = float(0.1)
        # reading the query lists
        with open('query_list.txt', newline='') as f:
            #reader = csv.reader(f)
            query_list = f.readlines() #[x[0] for x in reader]

        comparison_options(query_list, datapoint_attribute, conn, epsilon, repetitions, drop_percentile)

	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    return

def comparison_options(query_list, datapoint_attribute, conn, epsilon, repetitions, drop_percentile):
        avg_time_noisy_points_list = []
        avg_time_noisy_result_list = []
        avg_time_noisy_both_list = []
        avg_time_ldp_list = []
        avg_time_baseline_list = []
        noisy_points_responses = []
        drop_lower = int(repetitions*drop_percentile)
        drop_upper = int(repetitions-(repetitions*drop_percentile))
        amount_after_drop = int(repetitions-(2*repetitions*drop_percentile))
        print("*****************NOISY POINTS*****************")
        # executing all queries of query_list with noise
        for query in query_list:
            print(query)
            time_noisy_points = []
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, True, False, False) 
                end = time.time()
                t = end - start
                time_noisy_points.append(t)
            noisy_points_responses.append(response)
            time_noisy_points.sort()
            time_noisy_points = time_noisy_points[drop_lower:drop_upper]
            avg_time_noisy_points = round(sum(time_noisy_points)/amount_after_drop, 4)
            avg_time_noisy_points_list.append(avg_time_noisy_points)
        print("**********************************************************")
        print("avg noisy points: ", avg_time_noisy_points_list)
        print("**********************************************************")

        noisy_result_responses = []
        print("*****************NOISY RESULT*****************")
        for query in query_list:
            print(query)
            time_noisy_result = []
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, False, True, False) 
                end = time.time()
                t = end - start
                time_noisy_result.append(t)
            noisy_result_responses.append(response)
            time_noisy_result.sort()
            time_noisy_result = time_noisy_result[drop_lower:drop_upper]
            avg_time_noisy_result = round(sum(time_noisy_result)/amount_after_drop, 4)
            avg_time_noisy_result_list.append(avg_time_noisy_result)
        print("**********************************************************")
        print("avg noisy result: ", avg_time_noisy_result_list)
        print("**********************************************************")

        noisy_both_responses = []
        print("*****************NOISY POINTS AND RESULT*****************")
        for query in query_list:
            print(query)
            time_noisy_both = []
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, True, True, False) 
                end = time.time()
                t = end - start
                time_noisy_both.append(t)
            noisy_both_responses.append(response)
            time_noisy_both.sort()
            time_noisy_both = time_noisy_both[drop_lower:drop_upper]
            avg_time_noisy_both = round(sum(time_noisy_both)/amount_after_drop, 4)
            avg_time_noisy_both_list.append(avg_time_noisy_both)
        print("**********************************************************")
        print("avg noisy points and result: ", avg_time_noisy_result_list)
        print("**********************************************************")
        ldp_responses = []

        print("*****************RESPONSES WITH LDP*****************")
        for query in query_list:
            print(query)
            time_ldp = []
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, False, False, True)
                end = time.time()
                t = end - start
                time_ldp.append(t)
            ldp_responses.append(response)
            time_ldp.sort()
            time_ldp = time_ldp[drop_lower:drop_upper]
            avg_time_ldp = round(sum(time_ldp)/amount_after_drop, 4)
            avg_time_ldp_list.append(avg_time_ldp)
        print("**********************************************************")
        print("avg_time_ldp_list: ", avg_time_ldp_list)
        print("**********************************************************")

        # executing all queries of query_list_wo_postgis_func without noise
        responses = []
        time_baseline = []
        print("*****************RESPONSES BASELINE*****************")
        for query in query_list:
            for l in range (1, repetitions+1):
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, False, False, False)
                end = time.time()
                t = end - start
                time_baseline.append(t)
            time_baseline.sort()
            time_baseline = time_baseline[drop_lower:drop_upper]
            avg_time_baseline = round(sum(time_baseline)/amount_after_drop, 4)
            avg_time_baseline_list.append(avg_time_baseline)
            responses.append(response)
        print("**********************************************************")
        print("avg time baseline list: ", avg_time_baseline_list)
        print("**********************************************************")

        # putting results into a diagram
        labels = ['Bounding box 100', 'Bounding box 1000', 'Extent 100', 'Extent 1000', 'Centroid 100', 'Centroid 1000', 'Union 100', 'Union 1000']
        x = np.arange(len(labels))
        width = 0.18
        plt.setp
        fig, ax = plt.subplots(figsize=(15,8))
        rects1 = ax.bar(x - 2*width, avg_time_noisy_points_list, width, label='Laplace noise: points')
        rects2 = ax.bar(x - width, avg_time_noisy_result_list, width, label='Laplace noise: result')
        rects3 = ax.bar(x, avg_time_noisy_both_list, width, label='Laplace noise: points and result')
        rects4 = ax.bar(x + width, avg_time_ldp_list, width, label='LDP')
        rects5 = ax.bar(x + 2*width, avg_time_baseline_list, width, label='Baseline')
        plt.ylim(0, 0.5)
        ax.set_ylabel('Latency')
        ax.set_title('Performance comparison')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=5, rotation=45)
        ax.bar_label(rects2, padding=5, rotation=45)
        ax.bar_label(rects3, padding=5, rotation=45)
        ax.bar_label(rects4, padding=5, rotation=45)
        ax.bar_label(rects5, padding=5, rotation=45)
        fig.autofmt_xdate()
        plt.show()
        return noisy_points_responses, noisy_result_responses, noisy_both_responses, ldp_responses, responses

if __name__ == '__main__':
    con = connect()
