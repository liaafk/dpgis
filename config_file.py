QUERY = ["SELECT ST_ENVELOPE(loc) FROM orders_de WHERE minutes >= 60"]
DATAPOINT_ATTRIBUTE = 'loc'
EPSILON = [1.0, 2.0, 3.0, 4.0, 5.0]
REMOVE_EXTREME_POINTS = [True, False]
NOISY_POINTS = [True, False]
NOISY_RESULT = [True, False]
