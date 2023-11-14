import pandas as pd
import os
import cvxpy as cp
import numpy as np
import gurobipy

# os.chdir('C:\\Users\\cozmemis3\\OneDrive - Georgia Institute of Technology\\Desktop\\Courses\\Deterministic Optimization - ISYE-6669\\project-a\\to-submit')

# obtaining parameters
solar_data = pd.read_csv('Solar_Forecast.csv')
e_price_data = pd.read_csv('Electricity_Prices.csv')
h_demand_data = pd.read_csv('Hydrogen_Demand.csv')
e_demand_data = pd.read_csv('Electricity_Demand.csv')

num_hours = 72
solar_rate = 2

solar = np.array([solar_rate*solar_data['% of Rated Output'][i-1] for i in range(1,num_hours+1)])
h_price = np.array([10 for i in range(1,num_hours+1)])
e_price = np.array([e_price_data['Price ($/MWh)'][i-1] for i in range(1,num_hours+1)])
h_demand = np.array([h_demand_data['Demand (kg)'][i-1] for i in range(1,num_hours+1)])
e_demand = np.array([e_demand_data['Demand (MWh)'][i-1] for i in range(1,num_hours+1)])

# defining decision variables
x_E = cp.Variable(num_hours)
x_H = cp.Variable(num_hours)
n_H = cp.Variable(num_hours) 

# introducing the objective function
objective = cp.Minimize(cp.sum(cp.multiply(e_price, x_E)) + cp.sum(cp.multiply(h_price, x_H)))

# adding constraints
constraints = []

for i in range(num_hours):
    constraints += [x_E[i] + solar[i] >= e_demand[i]]
    
constraints += [x_H[0] >= h_demand[0] + n_H[0]]
    
for i in range(num_hours):
    if i != 0:
        constraints += [n_H[i-1] + x_H[i] >= h_demand[i] + n_H[i]]
        
constraints += [x_E >= 0]
constraints += [x_H >= 0]
constraints += [n_H >= 0]
        
#solving the problem
prob = cp.Problem(objective, constraints)

prob.solve(solver=cp.GUROBI)

# printing the solution
print('Minimum cost is: {}'.format(prob.value))
print('-------------') 
print('Hourly electricity purchases in MW')
count=1
for i in list(x_E.value):
    print('Hour {0}: {1}'.format(count,i)) 
    count+=1
print('-------------')    
print('Hourly hydrogen purchases in kg')
count=1
for i in list(x_H.value):
    print('Hour {0}: {1}'.format(count,i))   
    count+=1
    
# exporting the solution
data = pd.DataFrame(index=range(num_hours))
data['Hour'] = [i+1 for i in range(num_hours)]
data['x_E'] = list(x_E.value)
data['x_H'] = list(x_H.value)
data['n_H'] = list(n_H.value)
data.to_csv('output-Cagri.csv',index=False)
