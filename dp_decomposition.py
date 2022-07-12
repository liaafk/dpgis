import numpy as np
import pandas as pd
import time


def is_in_domain(x, y, left, bottom, top, right): #includes left and bottom border
        if (x >= left) and (x < right) and (y < top) and (y >= bottom):
            return True
        else:
            return False

def count_in_domain(xs, ys, domain):
    count = 0
    
    for i in range(xs.shape[0]):
        if is_in_domain(xs[i], ys[i], domain[0], domain[1], domain[2], domain[3]):
            count += 1
    
    return count

def laplace_noise(Lambda, seed=7): # using inverse transform sampling
    # for numbers between -N and N
    N = Lambda*10
    x = np.arange(-N,N+1,N/20000)

    # pdf P
    P = 1.0 / (2*Lambda) * np.exp(-np.abs(x) / Lambda)
    P = P / np.sum(P)
    
    # cdf C
    C = P.copy()
    for i in np.arange(1, P.shape[0]):
        C[i] = C[i-1] + P[i]
    
    # get sample from laplace distribution wiht uniform random number
    u = np.random.rand()
    sample = x[np.argmin(np.abs(C-u))]
    
    return sample

def get_domain_subdomains(domain):
    
    # domain = [left, bottom, top, right]
    # left = domain[0]
    # bottom = domain[1]
    # top = domain[2]
    # right = domain[3]
    
    # -----------
    # | q1 | q2 |
    # -----------
    # | q3 | q4 |
    # -----------
    
    dom_h = domain[2] - domain[1]
    dom_w = domain[3] - domain[0]
    
    q1 = [domain[0], domain[1] + dom_h/2, domain[2] , domain[3] - dom_w/2]
    q2 = [domain[0] + dom_w/2, domain[1] + dom_h/2, domain[2] , domain[3]]
    q3 = [domain[0], domain[1], domain[1] + dom_h/2, domain[3] - dom_w/2]
    q4 = [domain[0] + dom_w/2, domain[1], domain[1] + dom_h/2 , domain[3]]
    
    return q1, q2, q3, q4

def priv_tree(x, y, lam=2, theta=100, delta=10, domain_margin=1e-2, seed=7):
    # simple tree parameters
    #x, y = data['longitude'].values, data['latitude'].values
    #lam = laplace noise parameter
    #theta = 50 #min count per domain
    #h = 10 # max tree depth
    np.random.seed(seed)

    #initialise counters and holders
    domains = []
    unvisited_domains = []
    counts = []
    noisy_counts = []
    tree_depth = 0
    
    # data limits
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)

    # root domain
    v0 = [x_min, y_min, y_max+domain_margin, x_max+domain_margin] # +margin around borders to include all points
    #domains.append(v0)
    unvisited_domains.append(v0)
    #tree_depth += 1
    #print('tree root initialised.')

    # create subdomains where necessary
    while not not unvisited_domains: # while unvisited_domains is not empty
        for unvisited in unvisited_domains:
            # calculate count and noisy count
            count = count_in_domain(x, y, unvisited)
            b = count - (delta*tree_depth)
            b = max(b, (theta - delta))
            noisy_b = b + laplace_noise(lam)
            if (noisy_b > theta): #split if condition is met
                v1, v2, v3, v4 = get_domain_subdomains(unvisited)
                # mark new domains as unvisited
                unvisited_domains.append(v1)
                unvisited_domains.append(v2)
                unvisited_domains.append(v3)
                unvisited_domains.append(v4)
                # remove domain that was just visited and split
                unvisited_domains.remove(unvisited)
                # add to tree depth
                tree_depth += 1
                #print('*** domain split ***')
                #print('\ttree depth: {:d}'.format(tree_depth))
            else:
                # remove domain that was just visited
                unvisited_domains.remove(unvisited)
                # record count and noisy count
                counts.append(count)
                # add domain to final domains
                noisy_counts.append(noisy_b)
                domains.append(unvisited)
                #print('domain visited but not split.')
        
    return domains, noisy_counts, counts, tree_depth
 
if __name__ == "__main__":
    data = pd.read_csv("beijing_taxi_data_30k.csv", sep=',', names=['latitude', 'longitude'], header=None)
    start = time.time()
    domains, noisy_counts, counts, tree_depth = priv_tree(data['longitude'].values, data['latitude'].values, lam=2, theta=100, delta=10, domain_margin=1e-2, seed=7)
    end = time.time()
    print(f"elapsed time: {end-start}")
    print(len(noisy_counts), len(domains))