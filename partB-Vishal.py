import cvxpy as cp
import numpy as np
import pandas as pd
import gurobipy

Elec_Demand = pd.read_csv('Electricity_Demand.csv')
Hydro_Demand = pd.read_csv('Hydrogen_Demand.csv')
Elec_Price = pd.read_csv('Electricity_Prices.csv')
Solar_Supply = pd.read_csv('Solar_Forecast.csv')

# Define Parameters
sE = Solar_Supply['% of Rated Output'].to_numpy() # Percentage of rated output at solar farm for hour i
pE = Elec_Price['Price ($/MWh)'].to_numpy() # Electricity price per MWh at hour i
pH = np.array([10 for i in range(pE.size)]) # Price of hydrogen per kg at hour i
dE = Elec_Demand['Demand (MWh)'].to_numpy() # Electricity demand in MWh at hour i
dH = Hydro_Demand['Demand (kg)'].to_numpy() # Hydrogen demand in kg at hour i

# Define Decision Variables
xE = cp.Variable(pE.size) # Number of MWhs of electricity purchased at hour i
xH = cp.Variable(pE.size) # Number of kgs of hydrogen purchased at hour i
nH = cp.Variable(pE.size) # Number of kgs of hydrogen in inventory at end of hour i

constraints=[]
for i in range(0,pE.size):
    constraints += [xE[i] + 2*sE[i] >= dE[i]] # Electricity Demand Constraint
    constraints += [cp.sum(xH[:i+1])-sum(dH[0:i]) >= dH[i]] # Hydrogen Demand Constraint 
    constraints += [xE[i] >= 0, xH[i] >= 0, nH[i] >=0] # Sign constraints

objective = cp.Minimize(pE.T@xE + pH.T@xH)    # Minimize the cost

problem = cp.Problem(objective, constraints)
problem.solve(solver=cp.GUROBI)
print("The optimal value is:", problem.value)

Solution_DataFrame = pd.DataFrame()
Solution_DataFrame['Energy Needed'] = dE
Solution_DataFrame['Solar Energy Generated'] = sE
Solution_DataFrame["Hourly Electricity Purchase (MWh)"] = xE.value
Solution_DataFrame['Energy Cost at Hour'] = pE
Solution_DataFrame['Hydrogen Needed'] = dH
Solution_DataFrame['Hydrogen Stored'] = nH.value
Solution_DataFrame['Hourly Hydrogen Purchase (kg)'] = xH.value
Solution_DataFrame['Hydrogen Cost at Hour'] = pH
Solution_DataFrame['Total Cost at Hour'] = (Solution_DataFrame['Hourly Electricity Purchase (MWh)'].values * Solution_DataFrame['Energy Cost at Hour'].values
                                            + Solution_DataFrame['Hourly Hydrogen Purchase (kg)'].values * Solution_DataFrame['Hydrogen Cost at Hour'].values)
Solution_DataFrame['Total Cost ($)'] = Solution_DataFrame['Total Cost at Hour'].cumsum(axis=0)
Solution_DataFrame.index.name = 'Hour'
Solution_DataFrame.index = Solution_DataFrame.index+1
Solution_DataFrame.to_csv('output.csv')
