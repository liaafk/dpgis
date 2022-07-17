from ast import Pass
import math
import random
from scipy.optimize import minimize
import pandas as pd

def normalize_points(xory_list):
    lower = min(xory_list)
    upper = max(xory_list)
    middle = (upper-lower)/2
    normalized = [a-middle for a in xory_list]
    upper_norm = upper-middle
    return normalized, middle, upper_norm

def compute_center(xory, side_length, upper_norm):
    lower_norm = upper_norm * -1
    if xory <= lower_norm + side_length/2:
        return lower_norm + side_length/2
    elif lower_norm + side_length/2 < xory and xory <= upper_norm - side_length/2:
        return xory
    else:
        return upper_norm - side_length/2

def normalizing_term(side_length, eps, upper_norm_x, upper_norm_y):
    return 1/((side_length**2) * (math.exp(eps)-1) + 4*upper_norm_x*upper_norm_y)

def get_opt_side_length(eps, upper_norm_x, upper_norm_y):
    max_bound = min(upper_norm_x, upper_norm_y)
    fun = lambda w: ((1/((w**2)*(math.exp(eps)-1) + 4*upper_norm_x*upper_norm_y))*4*upper_norm_x*upper_norm_y*(upper_norm_x**2 + upper_norm_y**2))/3 + ((1/((w**2)*(math.exp(eps)-1)+4*upper_norm_x*upper_norm_y))*(w**4)*(math.exp(eps)-1))/12+((1/((w**2)*(math.exp(eps)-1)+4*upper_norm_x*upper_norm_y))*(w**5)*(math.exp(eps) - 1)*(upper_norm_x+upper_norm_y))/(48*upper_norm_x*upper_norm_y)
    cons = ({'type':'ineq', 'fun': lambda w: w > 0},
    {'type':'ineq', 'fun': lambda w: w < 2*max_bound})
    return minimize(fun, 3, method='COBYLA', constraints=cons).x[0]

def square_mechanism(domain, eps):
    x = [point[0] for point in domain]
    y = [point[1] for point in domain]
    norm_x, middle_x, upper_norm_x = normalize_points(x)
    norm_y, middle_y, upper_norm_y = normalize_points(y)
    side_length = get_opt_side_length(eps, upper_norm_x, upper_norm_y)
    norm_term = normalizing_term(side_length, eps, upper_norm_x, upper_norm_y)
    new_points =[]
    for norm_x_point, norm_y_point in list(zip(norm_x, norm_y)):
        center_x = compute_center(norm_x_point, side_length, upper_norm_x)
        center_y = compute_center(norm_y_point, side_length, upper_norm_y)
        threshold = random.uniform(0,1)
        if threshold <= 4*norm_term*upper_norm_x*upper_norm_y:
            new_points.append([random.uniform(min(norm_x), max(norm_x)) + middle_x, random.uniform(min(norm_y), max(norm_y)) + middle_y])
        else:
            new_points.append([random.uniform(center_x - side_length/2, center_x + side_length/2) + middle_x, random.uniform(center_y - side_length/2, center_y + side_length/2) + middle_y])
    return new_points