import numpy as np    
def filter_simulations(sim_list,**kwargs):
  filtered_list = []
  for sim in sim_list:
      match_all = True
      for key, item in kwargs.iteritems():
            if not sim.sim_info[key] == item:  
              match_all = False
      if match_all:
        filtered_list.append(sim)
  return filtered_list
    
def sort_sims(sim_list,prop): 
    return sorted(sim_list,key=lambda it: it.sim_info[prop])    

def get_array(sim_list,func=None,var=None):
    prop_list = []
    if func:
        for sim in sim_list:
           if var:
               prop_list.append(func(sim,var))
           else:
               prop_list.append(func(sim))
    return np.array(prop_list)

def fa(sim_list,func,*args,**kwargs):
    [getattr(sim,func)(*args,**kwargs) for sim in sim_list]
