import cvxpy as cp
import numpy as np
import pandas as pd
import gurobipy
#-------------------------------------------------------------
# Function to store the output in a dataframe
#-------------------------------------------------------------
def initial_df(dE,sE,pE,dH,pH,xE,xH):
    Solution_DataFrame = pd.DataFrame()
    Solution_DataFrame['Energy Needed'] = dE
    Solution_DataFrame['Solar Energy Generated'] = 2*sE
    Solution_DataFrame['Energy Cost at Hour'] = pE
    Solution_DataFrame['Hydrogen Needed'] = dH
    Solution_DataFrame['Hydrogen Cost at Hour'] = pH
    Solution_DataFrame['Energy Purchased'] = xE.value
    Solution_DataFrame['Hydrogen Purchased'] = xH.value
    Solution_DataFrame['Total Cost at Hour'] = (Solution_DataFrame['Energy Purchased'].values * Solution_DataFrame['Energy Cost at Hour'].values
                                                + Solution_DataFrame['Hydrogen Purchased'].values * Solution_DataFrame['Hydrogen Cost at Hour'].values)
    Solution_DataFrame['Total Cost ($)'] = Solution_DataFrame['Total Cost at Hour'].cumsum(axis=0)
    return(Solution_DataFrame)

# Load data
Elec_Demand = pd.read_csv('Electricity_Demand.csv')
Hydro_Demand = pd.read_csv('Hydrogen_Demand.csv')

Elec_Price = pd.read_csv('Electricity_Prices.csv')
Solar_Supply = pd.read_csv('Solar_Forecast.csv')

# Manipulate data to get it into a convienient form
Solar_Supply['Datetime'] = pd.to_datetime(Solar_Supply['Datetime'])
Solar_Supply['Hour'] = Solar_Supply['Datetime'].dt.hour
cols = ['Datetime', 'Hour', '% of Rated Output']
Solar_Supply = Solar_Supply[cols]

# Define Parameters
sE = Solar_Supply['% of Rated Output'].to_numpy() # Number of MWs of electricity produced at solar farm for hour i
pE = Elec_Price['Price ($/MWh)'].to_numpy() # Electricity price per MWh at hour i
pH = np.array([10 for i in range(pE.size)]) # Price of hydrogen per kg at hour i
dE = Elec_Demand['Demand (MWh)'].to_numpy() # Electricity demand in MWh at hour i
dH = Hydro_Demand['Demand (kg)'].to_numpy() # Hydrogen demand in kg at hour i


#-------------------------------------------------------------
# Part-A
#-------------------------------------------------------------
# Define Decision Variables
xE = cp.Variable(pE.size) # Number of MWhs of electricity purchased at hour i
xH = cp.Variable(pE.size) # Number of kgs of hydrogen purchased at hour i

constraints = [xE[0] + 2*sE[0] >= dE[0],                              # Electricity Demand Constraint at hour 1
               xH[0] >= dH[0],                                      # Hydrogen Demand Constraint at hour 1
               xE[0] >= 0, xH[0] >= 0]                              # Sign constraints at hour 1
for i in range(1,pE.size):
    constraints += [xE[i] + 2*sE[i] >= dE[i],                         # Electricity Demand Constraint at hour 2 to i
                    sum(xH[0:i+1])-sum(dH[0:i]) >= dH[i],           # Hydrogen Demand Constraint at hour 2 to i
                    xE[i] >= 0, xH[i] >= 0]                         # Sign constraints at hour 2 to i

objective = cp.Minimize(pE.T@xE + pH.T@xH)                          # Minimize the cost

problem = cp.Problem(objective, constraints)
problem.solve(solver=cp.GUROBI)
Solution_DataFrame = initial_df(dE,sE,pE,dH,pH, xE, xH)
Solution_DataFrame.index.name = 'Hour'
Solution_DataFrame.index = Solution_DataFrame.index+1
Solution_DataFrame.to_csv('output_part-A.csv')
# display(Solution_DataFrame)

print("\nThe optimal value for part-A is:", problem.value)

#-------------------------------------------------------------
# Part-B Q1 - Electrolyser
#-------------------------------------------------------------

# Define Decision Variables
xE = cp.Variable(pE.size) # Number of MWhs of electricity purchased at hour i
xH = cp.Variable(pE.size) # Number of kgs of hydrogen purchased at hour i
a = cp.Variable(pE.size, boolean=True) # 1 if electrolyser is on for hour i; 0 otherwise

constraints=[]
for i in range(0,pE.size):
    constraints += [xE[i] + 2*sE[i] - 0.5*a[i] >= dE[i]] # Electricity Demand Constraint
    constraints += [cp.sum(xH[:i+1]) + 9*cp.sum(a[:i+1]) - sum(dH[0:i]) >= dH[i]] # Hydrogen Demand Constraint 
    constraints += [xE[i] >= 0, xH[i] >= 0] # Sign constraints

objective = cp.Minimize(pE.T@xE + pH.T@xH)    # Minimize the cost

problem = cp.Problem(objective, constraints)
problem.solve(solver=cp.GUROBI)
print("\nThe optimal value with electrolyser is:", problem.value)

Solution_DataFrame = initial_df(dE,sE,pE,dH,pH, xE, xH)
Solution_DataFrame['Electrolyser Usage'] = a.value
Solution_DataFrame.index.name = 'Hour'
Solution_DataFrame.index = Solution_DataFrame.index+1
Solution_DataFrame.to_csv('output_part-B_Q1_Electrolyser.csv')

Electrolyser_Use = pd.DataFrame()
Electrolyser_Use['Is electrolyser used? (1: yes - 0: no)'] = a.value
Electrolyser_Use.index.name = 'Hour'
Electrolyser_Use.index = Electrolyser_Use.index+1
Electrolyser_Use.to_csv('Electrolyser_use.csv')
#-------------------------------------------------------------
# Part-B Q2a - 2 Solar panels
#-------------------------------------------------------------
# Define Parameters
b = 2 # number of solar panels purchased

# Define Decision Variables
xE = cp.Variable(pE.size) # Number of MWhs of electricity purchased at hour i
xH = cp.Variable(pE.size) # Number of kgs of hydrogen purchased at hour i

constraints = []
for i in range(0,pE.size):
    constraints += [xE[i] + (sE[i]*(2+(0.2*b))) >= dE[i],           # Electricity Demand Constraint at hour 2 to i
                    sum(xH[0:i+1])-sum(dH[0:i]) >= dH[i],           # Hydrogen Demand Constraint at hour 2 to i
                    xE[i] >= 0, xH[i] >= 0]                         # Sign constraints at hour 2 to i

objective = cp.Minimize(pE.T@xE + pH.T@xH)                          # Minimize the cost

problem = cp.Problem(objective, constraints)
problem.solve(solver=cp.GUROBI)
print("\nThe optimal value for 2 solar panels is:", problem.value)
Solution_DataFrame = initial_df(dE,sE,pE,dH,pH, xE, xH)
Solution_DataFrame['Solar Energy Generated'] = sE*(2+(0.2*b))
Solution_DataFrame.index.name = 'Hour'
Solution_DataFrame.index = Solution_DataFrame.index+1
Solution_DataFrame.to_csv('output_part-B_Q2a.csv')

#-------------------------------------------------------------
# Part-B Q2b - Number of Solar  panels as a decision variable
#-------------------------------------------------------------

# Define Decision Variables
xE = cp.Variable(pE.size) # Number of MWhs of electricity purchased at hour i
xH = cp.Variable(pE.size) # Number of kgs of hydrogen purchased at hour i
b = cp.Variable(1, integer=True) # number of solar panels purchased

constraints = [b >= 0]
for i in range(0,pE.size):
    constraints += [xE[i] + (sE[i]*(2+(0.2*b))) >= dE[i],           # Electricity Demand Constraint at hour 2 to i
                    sum(xH[0:i+1])-sum(dH[0:i]) >= dH[i],           # Hydrogen Demand Constraint at hour 2 to i
                    xE[i] >= 0, xH[i] >= 0]                         # Sign constraints at hour 2 to i

objective = cp.Minimize(pE.T@xE + pH.T@xH + + 2113.5*b)             # Minimize the cost

problem = cp.Problem(objective, constraints)
problem.solve(solver=cp.GUROBI)
print("The optimal value with number of solar panels as a decision variable is:", problem.value)
print("The optimal number of solar panels to purchase:", b.value[0])

Solution_DataFrame = initial_df(dE,sE,pE,dH,pH, xE, xH)
Solution_DataFrame['Solar Energy Generated'] = sE*(2+(0.2*b.value))
Solution_DataFrame['Total Cost at Hour'] = (Solution_DataFrame['Energy Purchased'].values * Solution_DataFrame['Energy Cost at Hour'].values
                                            + Solution_DataFrame['Hydrogen Purchased'].values * Solution_DataFrame['Hydrogen Cost at Hour'].values + 2113.5/72*b.value)
Solution_DataFrame['Total Cost'] = Solution_DataFrame['Total Cost at Hour'].cumsum(axis=0)
Solution_DataFrame.index.name = 'Hour'
Solution_DataFrame.index = Solution_DataFrame.index+1
Solution_DataFrame.to_csv('output_part-B_Q2b.csv')
# display(Solution_DataFrame)

#-------------------------------------------------------------
# Part-B Q3 - Battery
#-------------------------------------------------------------

# Define Decision Variables
xE = cp.Variable(pE.size) # Number of MWhs of electricity purchased at hour i
xH = cp.Variable(pE.size) # Number of kgs of hydrogen purchased at hour i
C = cp.Variable(pE.size)  # charge in the battery at the end of hour i
charge_t0 = 0 # initial charge

constraints_c = []
constraints_c += [xE[0] + 2*sE[0] + charge_t0 >= dE[0] + C[0]] # Electricity Demand Constraint at first hour
for i in range(0,pE.size):
    if i != 0:
        constraints_c += [xE[i] + 2*sE[i] + C[i-1] >= dE[i] + C[i]] # Electricity Demand Constraint
    constraints_c += [C[i]<=0.5] # Battery storage constraint
    constraints_c += [cp.sum(xH[:i+1])-sum(dH[0:i]) >= dH[i]] # Hydrogen Demand Constraint 
    constraints_c += [xE[i] >= 0, xH[i] >= 0, C[i] >= 0] # Sign constraints

objective_c = cp.Minimize(pE.T@xE + pH.T@xH)    # Minimize the cost
problem_c = cp.Problem(objective_c, constraints_c)
problem_c.solve(solver=cp.GUROBI)
print("\nThe optimal value with a battery is:", problem_c.value)
Solution_DataFrame = initial_df(dE,sE,pE,dH,pH, xE, xH)
Solution_DataFrame[ 'Charge in the Battery at Hour'] = C.value
Solution_DataFrame.index.name = 'Hour'
Solution_DataFrame.index = Solution_DataFrame.index+1
Solution_DataFrame.to_csv('output_part-B_Q3.csv')