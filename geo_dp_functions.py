def testquery(cur):
    cur.execute('SELECT loc FROM orders_de LIMIT 10;')
    query_results = cur.fetchall()
    return(query_results)