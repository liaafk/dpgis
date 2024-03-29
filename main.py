import psycopg2
from configparser import ConfigParser
from geo_dp_functions import noisy_sql_response
from itertools import product
from local_dp import square_mechanism
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

    # Get SQL Query and name of the attribute datapoint in table out of the config file
        query = list(config_file.QUERY)
        datapoint_attribute = config_file.DATAPOINT_ATTRIBUTE
        epsilon = list(config_file.EPSILON)
        laplace_points = config_file.LAPLACE_POINTS
        laplace_result = config_file.LAPLACE_RESULT
        local_dp = config_file.LOCAL_DP

        # Check if privacy methods parameters are used correctly
        if (laplace_points or laplace_result) and local_dp:
            print("Cannot choose both Laplace and local DP!")
            return -1
    # Executing query using the noisy SQL query
        for (iter_query, iter_epsilon) in product(query, epsilon):
            print(noisy_sql_response(iter_query, datapoint_attribute, conn, iter_epsilon, laplace_points, laplace_result, local_dp))

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