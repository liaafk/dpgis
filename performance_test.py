import time

from geo_dp_functions import noisy_sql_response
import geopandas as gpd


epsilon = 1.0
datapoint_attribute = "loc"
remove_extreme_points = True
noisy_points = True
noisy_result = True
query_list = [] #csv datei mit 15 queries(5 pro select function)
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





    