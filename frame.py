import psycopg2
#import pydp as dp
from configparser import ConfigParser
from geo_dp_functions import dp_sql_response, getNoisyDomain, getQueryPoints, testquery
import sys

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
        
	# execute a statement
        #print('PostgreSQL database version:')
        #cur.execute('SELECT version()')
        
        #print(testquery(conn,'SELECT * FROM orders LIMIT 10;'))

        # display the PostgreSQL database server version
        #db_version = cur.fetchone()
        #print(db_version)
       
    # Get SQL Query and name of the attribute datapoint in table
        query = input("Please enter a SQL query: ")
        datapoint_attribute = input("Please enter name of datapoint attribute: ")
        epsilon = input("Please enter epsilon (float, e.g. 1.0): ")
    
    # Get raw points of query
        #print(getQueryPoints(query, datapoint_attribute, conn))
        print(dp_sql_response(query, datapoint_attribute, conn, epsilon))

    # DP Mechanism ...
        #print(getNoisyDomain(getQueryPoints(query, datapoint_attribute, conn), 2.0))

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