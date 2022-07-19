import time
from geo_dp_functions import noisy_sql_response
import geopandas as gpd
import psycopg2
from configparser import ConfigParser
from geo_dp_functions import noisy_sql_response
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
        noisy_points = True
        #noisy_result = True
        local_dp = True
        repetitions = 100
        # reading the query lists
        with open('query_list.txt', newline='') as f:
            #reader = csv.reader(f)
            query_list = f.readlines() #[x[0] for x in reader]
        with open('query_list_postgis.txt', newline='') as f:
            #reader = csv.reader(f)
            query_list_postgis = f.readlines() # [x[0] for x in reader]
        
        # comparing query execution time with and without noise
        #noisy_responses, ldp_responses, responses = compare_noise_without(query_list, query_list_postgis, datapoint_attribute, conn, epsilon, noisy_points, local_dp, repetitions)
        #print("Comparison noise and without noise result: ", noisy_responses, responses)
        
        # comparing the option of noising each point, noising the result and doing both
        #response_points, response_result, response_both_options = compare_noise_options(query_list, datapoint_attribute, conn, epsilon)
        #print("Comparison of options result: ", response_points, response_result, response_both_options)

        response_noisy_2,  ldp_responses_2, response_wo_postgis_func = compare_noise_with_request_wo_postgis_func(query_list, datapoint_attribute, conn, epsilon, noisy_points, local_dp, repetitions)
        #print("Comparison of noisy response and no PostGIS request result: ", response_noisy_2, response_wo_postgis_func)

	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    return

# comparing the results of queries with and without noise
def compare_noise_without(query_list, query_list_postgis, datapoint_attribute, conn, epsilon, noisy_points, local_dp, repetitions):
        meantime_noisy_list = []
        meantime_ldp_list = []
        meantime_wo_noise_list = []
        # executing all queries of query_list with noise
        noisy_responses = []
        local_dp = False
        print("*****************RESPONSES WITH NOISE*****************")
        for query in query_list:
            print(query)
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                time_noisy = 0
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, noisy_points, local_dp)
                end = time.time()
                t = end - start
                time_noisy += t
            noisy_responses.append(response)
            meantime_noisy = time_noisy/repetitions
            meantime_noisy_list.append(meantime_noisy)
        print("**********************************************************")
        print("meantime_noisy_list: ", meantime_noisy_list)
        print("**********************************************************")
        
        ldp_responses = []
        local_dp = True
        noisy_points = False
        print("*****************RESPONSES WITH LDP*****************")
        for query in query_list:
            print(query)
            # executing each query 1000 times and calculate the mean
            for l in range(100):
                time_ldp = 0
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, noisy_points, local_dp)
                end = time.time()
                t = end - start
                time_ldp += t
            ldp_responses.append(response)
            meantime_ldp = time_ldp/100
            meantime_ldp_list.append(meantime_ldp)
        print("**********************************************************")
        print("meantime_ldp_list: ", meantime_ldp_list)
        print("**********************************************************")

        # executing all queries of query_list_postgis without noise
        responses = []
        print("*****************RESPONES WITHOUT NOISE*****************")
        for query in query_list_postgis:
            for l in range (1, repetitions+1):
                time_wo_noise = 0
                start = time.time()
                to_read = query.split()[1].lower()
                type_select = to_read.split('(')[0]
                response = gpd.read_postgis(query, conn, geom_col=type_select)
                end = time.time()
                t = end - start
                time_wo_noise += t
            meantime_wo_noise = time_wo_noise/repetitions
            meantime_wo_noise_list.append(meantime_wo_noise)
            responses.append(response)
        print("**********************************************************")
        print("meantime_wo_noise_list: ", meantime_wo_noise_list)
        print("**********************************************************")

        # putting results into a diagram
        labels = ['BB100', 'BBr1000', 'Extent100', 'Extent1000', 'Centroid100', 'Centroid1000', 'Union100', 'Union1000']
        x = np.arange(len(labels))
        width = 0.35
        plt.setp
        fig, ax = plt.subplots(figsize=(10,8))
        rects1 = ax.bar(x - (2*width)/3, meantime_noisy_list, width, label='With noise')
        rects2 = ax.bar(x, meantime_ldp_list, width, label='LDP')
        rects3 = ax.bar(x + (2*width)/3, meantime_wo_noise_list, width, label='Without noise')

        ax.set_ylabel('Execution time')
        ax.set_title('With and without noise')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)
        ax.bar_label(rects3, padding=3)
        fig.autofmt_xdate()
        #fig.tight_layout()
        plt.show()
        return noisy_responses, ldp_responses, responses

# comparing the option of noising each point, noising the result and doing both
def compare_noise_options(query_list, datapoint_attribute, conn, epsilon, repetitions):
        meantime_both_options_list = []
        meantime_noisy_points_list = []
        meantime_noisy_result_list = []
        #execute all queries of query_list with noise
        noisy_responses_extreme = []
        noisy_responses_points = []
        noisy_responses_result = []
        for query in query_list[:2]:
            print("********************QUERY****************************")
            print(query)
            #execute each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                # only noising points 
                time_points = 0
                start = time.time()
                response_points = noisy_sql_response(query, datapoint_attribute, conn, epsilon, True, False)
                end = time.time()
                t = end - start
                time_points += t

                # only noising points 
                time_result = 0
                start = time.time()
                response_result = noisy_sql_response(query, datapoint_attribute, conn, epsilon, False, True)
                end = time.time()
                t = end - start
                time_result += t

                # noising points and result
                time_both_options = 0
                start = time.time()
                response_both_options = noisy_sql_response(query, datapoint_attribute, conn, epsilon, True, True)
                end = time.time()
                t = end - start
                time_both_options += t

            noisy_responses_points.append(response_points)
            meantime_noisy_points = time_points/repetitions
            meantime_noisy_points_list.append(meantime_noisy_points)

            noisy_responses_result.append(response_result)
            meantime_noisy_result = time_result/repetitions
            meantime_noisy_result_list.append(meantime_noisy_result)

            noisy_responses_extreme.append(response_both_options)
            meantime_both_options = time_both_options/repetitions
            meantime_both_options_list.append(meantime_both_options)

        print("**********************************************************")
        print("meantime_noisy_points: ", meantime_noisy_points_list)
        print("**********************************************************")

        print("**********************************************************")
        print("meantime_noisy_result: ", meantime_noisy_result_list)
        print("**********************************************************")

        print("**********************************************************")
        print("meantime_both_options: ", meantime_both_options_list)
        print("**********************************************************")

        # putting results into a diagram
        labels = ['BB100', 'BBrepetitions']
        x = np.arange(len(labels))
        width = 0.25
        plt.setp
        fig, ax = plt.subplots(figsize=(10,8))
        rects1 = ax.bar(x, meantime_noisy_points_list, width, label='Noise Points')
        rects2 = ax.bar(x + width, meantime_noisy_result_list, width, label='Noise Result')
        rects3 = ax.bar(x - width, meantime_both_options_list, width, label='Noise Points and Result')

        ax.set_ylabel('Execution time')
        ax.set_title('Options to obfuscate data')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)
        ax.bar_label(rects3, padding=3)
        fig.autofmt_xdate()
        plt.show()
        return response_points, response_result, response_both_options

def compare_noise_with_request_wo_postgis_func(query_list, datapoint_attribute, conn, epsilon, noisy_points, local_dp, repetitions):
        meantime_noisy_list = []
        meantime_ldp_list = []
        meantime_wo_noise_wo_postgis_fun_list = []
        # executing all queries of query_list with noise
        local_dp = False
        noisy_points = True
        noisy_responses = []
        print("*****************RESPONSES WITH NOISE*****************")
        for query in query_list:
            print(query)
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                time_noisy = 0
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, noisy_points, local_dp) 
                end = time.time()
                t = end - start
                time_noisy += t
            noisy_responses.append(response)
            meantime_noisy = time_noisy/repetitions
            meantime_noisy_list.append(meantime_noisy)
        print("**********************************************************")
        print("meantime_noisy_list: ", meantime_noisy_list)
        print("**********************************************************")

        local_dp = True
        noisy_points = False
        ldp_responses = []

        print("*****************RESPONSES WITH LDP*****************")
        for query in query_list:
            print(query)
            # executing each query repetitions times and calculate the mean
            for l in range(1, repetitions+1):
                time_ldp = 0
                start = time.time()
                response = noisy_sql_response(query, datapoint_attribute, conn, epsilon, noisy_points, local_dp)
                end = time.time()
                t = end - start
                time_ldp += t
            ldp_responses.append(response)
            meantime_ldp = time_ldp/repetitions
            meantime_ldp_list.append(meantime_ldp)
        print("**********************************************************")
        print("meantime_ldp_list: ", meantime_ldp_list)
        print("**********************************************************")
        
        with open('query_list_wo_postgis_func.txt', newline='') as f:
            query_list_wo_postgis_func = f.readlines()

        # executing all queries of query_list_wo_postgis_func without noise
        responses = []
        print("*****************RESPONSES WITHOUT NOISE*****************")
        for query in query_list_wo_postgis_func:
            for l in range (1, repetitions+1):
                time_wo_noise = 0
                start = time.time()
                to_read = query.split()[1].lower()
                type_select = to_read.split('(')[0]
                response = gpd.read_postgis(query, conn, geom_col=type_select)
                end = time.time()
                t = end - start
                time_wo_noise += t
            meantime_wo_noise = time_wo_noise/repetitions
            meantime_wo_noise_wo_postgis_fun_list.append(meantime_wo_noise)
            responses.append(response)
        print("**********************************************************")
        print("meantime_wo_noise_wo_postgis_fun_list: ", meantime_wo_noise_wo_postgis_fun_list)
        print("**********************************************************")

        # putting results into a diagram
        labels = ['BB100', 'BB1000', 'Extent100', 'Extent1000', 'Centroid100', 'Centroid1000', 'Union100', 'Union1000']
        x = np.arange(len(labels))
        width = 0.35
        plt.setp
        fig, ax = plt.subplots(figsize=(10,8))
        rects1 = ax.bar(x - 2*width/3, meantime_noisy_list, width, label='Laplace mechanism')
        rects2 = ax.bar(x, meantime_ldp_list, width, label='LDP')
        rects3 = ax.bar(x + 2*width/3, meantime_wo_noise_wo_postgis_fun_list, width, label='Baseline')

        ax.set_ylabel('Latency')
        ax.set_title('Performance comparison')
        ax.set_xticks(x, labels)
        ax.legend()

        ax.bar_label(rects1, padding=3)
        ax.bar_label(rects2, padding=3)
        ax.bar_label(rects3, padding=3)
        fig.autofmt_xdate()
        #fig.tight_layout()
        plt.show()
        return noisy_responses, ldp_responses, responses

if __name__ == '__main__':
    con = cProfile.run("connect()")
