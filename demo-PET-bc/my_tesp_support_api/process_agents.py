#   Copyright (C) 2017-2019 Battelle Memorial Institute
# file: process_agents.py
"""Functions to plot data from GridLAB-D substation agents

Public Functions:
        :process_agents: Reads the data and metadata, then makes the plots.  

"""
import json
import sys
import numpy as np
try:
  import matplotlib as mpl
  import matplotlib.pyplot as plt
except:
  pass

def plot_agents (dict, save_file=None, save_only=False):
  hrs = dict['hrs']
  data_a = dict['data_a']
  data_h = dict['data_h']
  idx_a = dict['idx_a']
  idx_h = dict['idx_h']
  keys_a = dict['keys_a']
  keys_h = dict['keys_h']
  hidx = dict['high_bid_idx']
  # display a plot
  fig, ax = plt.subplots(2,2, sharex = 'col')

  ax[0,0].plot(hrs, data_a[0,:,idx_a['CLEAR_PRICE_IDX']], color='blue', label='Cleared')
  ax[0,0].plot(hrs, data_h[hidx,:,idx_h['BID_P_IDX']], color='red', label='Bid')
  ax[0,0].set_ylabel(idx_a['CLEAR_PRICE_UNITS'])
  ax[0,0].set_title ('Prices at ' + keys_h[hidx])
  ax[0,0].legend(loc='best')

  ax[1,0].plot(hrs, data_h[hidx,:,idx_h['BID_Q_IDX']], color='red', marker='o', label='Quantity')
  ax[1,0].set_ylabel(idx_h['BID_Q_UNITS'])
  ax[1,0].set_title ('Bid Quantity at ' + keys_h[hidx])
  ax[1,0].set_xlabel('Hours')

  ax[0,1].plot(hrs, data_a[0,:,idx_a['CONSUMER_SURPLUS_IDX']].cumsum(), color='blue', label='Consumer')
  ax[0,1].plot(hrs, data_a[0,:,idx_a['SUPPLIER_SURPLUS_IDX']].cumsum(), color='red', label='Supplier')
  ax[0,1].set_ylabel(idx_a['CONSUMER_SURPLUS_UNITS'])
  ax[0,1].set_title ('Surplus')
  ax[0,1].legend(loc='best')

  q1 = (data_h[:,:,idx_h['BID_Q_IDX']]).squeeze()
  q2 = q1.sum(axis=0)
  ax[1,1].plot(hrs, q2, color='red')
  ax[1,1].set_ylabel(idx_h['BID_Q_UNITS'])
  ax[1,1].set_title ('Total House Bids')
  ax[1,1].set_xlabel('Hours')

  if save_file is not None:
    plt.savefig(save_file)
  if not save_only:
    plt.show()

def read_agent_metrics(dir, nameroot, dictname = '', print_dictionary=False):
  # first, read and print a dictionary of relevant agents
  if len (dictname) > 0:
    lp = open (dir + dictname).read()
  else:
    lp = open (dir + nameroot + '_agent_dict.json').read()
  dict = json.loads(lp)
  a_keys = list(dict['markets'].keys())
  a_keys.sort()
  c_keys = list(dict['hvacs'].keys()) # hvac name list
  h_keys = [ val['houseName'] for key, val in dict['hvacs'].items()] # home name list
  c_keys.sort()
  if print_dictionary:
    print('\nMarket Dictionary:')
    print('ID Period Unit Init StDev')
    for key in a_keys:
      row = dict['markets'][key]
      print (key, row['period'], row['unit'], row['init_price'], row['init_stdev'])
    print('\nController Dictionary:')
    print('ID House Mode BaseDaylight Ramp Offset Cap')
    for key in c_keys:
      row = dict['hvacs'][key]
      print (row['houseName'], row['control_mode'], row['daylight_set'], row['ramp'], row['offset_limit'], row['price_cap'])

  # read the auction metrics file
  lp_a = open (dir + 'auction_' + nameroot + '_metrics.json').read()
  lst_a = json.loads(lp_a)
  print ('\nAuction Metrics data starting', lst_a['StartTime'])

  # make a sorted list of the times, and NumPy array of times in hours
  lst_a.pop('StartTime')
  meta_a = lst_a.pop('Metadata')
  times = list(map(int,list(lst_a.keys())))
  times.sort()
  print ('There are', len (times), 'sample times at', times[1] - times[0], 'second intervals')
  hrs = np.array(times, dtype=np.float)
  denom = 3600.0
  hrs /= denom

  # parse the metadata for things of specific interest
  #print ('\nAuction Metadata [Variable Index Units]')
  idx_a = {}
  for key, val in meta_a.items():
    #print (key, val['index'], val['units'])
    if key == 'clearing_price':
      idx_a['CLEAR_PRICE_IDX'] = val['index']
      idx_a['CLEAR_PRICE_UNITS'] = val['units']
    if key == 'clearing_type':
      idx_a['CLEAR_TYPE_IDX'] = val['index']
      idx_a['CLEAR_TYPE_UNITS'] = val['units']
    if key == 'consumer_surplus':
      idx_a['CONSUMER_SURPLUS_IDX'] = val['index']
      idx_a['CONSUMER_SURPLUS_UNITS'] = val['units']
    if key == 'average_consumer_surplus':
      idx_a['AVERAGE_CONSUMER_SURPLUS_IDX'] = val['index']
      idx_a['AVERAGE_CONSUMER_SURPLUS_UNITS'] = val['units']
    if key == 'supplier_surplus':
      idx_a['SUPPLIER_SURPLUS_IDX'] = val['index']
      idx_a['SUPPLIER_SURPLUS_UNITS'] = val['units']

  # create a NumPy array of all auction metrics
  data_a = np.empty(shape=(len(a_keys), len(times), len(lst_a[str(times[0])][a_keys[0]])), dtype=np.float)
  print ('\nConstructed', data_a.shape, 'NumPy array for Auctions')
  j = 0
  for key in a_keys:
    i = 0
    for t in times:
      ary = lst_a[str(t)][a_keys[j]]
      data_a[j, i,:] = ary
      i = i + 1
    j = j + 1

  # read the houses metrics file
  lp_h = open (dir + 'house_' + nameroot + '_metrics.json').read()
  lst_h = json.loads(lp_h)
  print ('\nController Metrics data starting', lst_h['StartTime'])

  # parse the metadata for things of specific interest
  # c_keys = ['house1_R1_12_47_1_tm_507_thermostat_controller']
  lst_h.pop('StartTime')
  meta_h = lst_h.pop('Metadata')
  #print ('\nController Metadata [Variable Index Units]')
  idx_h = {}
  for key, val in meta_h.items():
    #print (key, val['index'], val['units'])
    if key == 'bid_price':
      idx_h['BID_P_IDX'] = val['index']
      idx_h['BID_P_UNITS'] = val['units']
    elif key == 'bid_quantity':
      idx_h['BID_Q_IDX'] = val['index']
      idx_h['BID_Q_UNITS'] = val['units']

  # create a NumPy array of all houses metrics - many are 'missing' zero-bids
  data_h = np.empty(shape=(len(h_keys), len(times), len(meta_h.items())), dtype=np.float)
  print ('\nConstructed', data_h.shape, 'NumPy array for Controllers')
  zary = np.zeros(len(meta_h.items()))
  j = 0
  for key in h_keys:
    i = 0
    for t in times:
      if h_keys[j] in lst_h[str(t)]:
        ary = lst_h[str(t)][h_keys[j]]
      else:
        ary = zary
      data_h[j, i,:] = ary
      i = i + 1
    j = j + 1

  # identify the controller that put in the highest bid
  hidx = 0
  nbidding = 0
  max_p = 0.0
  for i in range (len(h_keys)):
    this_max_p = np.amax (data_h[i,:,idx_h['BID_P_IDX']])
    if this_max_p > 0.0:
      nbidding += 1
    if this_max_p > max_p:
      max_p = this_max_p
      hidx = i
  print ('Out of {:d} houses, {:d} submitted bids and the highest bidder was {:s} [{:d}]'.format (len(c_keys), nbidding, c_keys[hidx], hidx))

  dict = {}
  dict['hrs'] = hrs
  dict['data_a'] = data_a
  dict['data_h'] = data_h
  dict['idx_a'] = idx_a
  dict['idx_h'] = idx_h
  dict['keys_a'] = a_keys
  dict['keys_c'] = c_keys
  dict['keys_h'] = h_keys
  dict['high_bid_idx'] = hidx
  return dict

def process_agents(nameroot, dictname = '', print_dictionary=False, save_file=None, save_only=False):
  """ Plots cleared price, plus bids from the first HVAC controller

  This function reads *auction_nameroot_metrics.json* and  
  *controller_nameroot_metrics.json* for the data;
  it reads *nameroot_glm_dict.json* for the metadata. 
  These must all exist in the current working directory.  
  Makes one graph with 2 subplots:
  
  1. Cleared price from the only auction, and bid price from the first controller
  2. Bid quantity from the first controller

  Args:
      nameroot (str): name of the TESP case, not necessarily the same as the GLM case, without the extension
      dictname (str): metafile name (with json extension) for a different GLM dictionary, if it's not *nameroot_glm_dict.json*. Defaults to empty.
      save_file (str): name of a file to save plot, should include the *png* or *pdf* extension to determine type.
      save_only (Boolean): set True with *save_file* to skip the display of the plot. Otherwise, script waits for user keypress.
  """
  dict = read_agent_metrics (nameroot, dictname, print_dictionary)
  plot_agents (dict, save_file, save_only)
