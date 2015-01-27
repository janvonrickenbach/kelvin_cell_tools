'''
Created on Oct 9, 2013

@author: vonrickenbach
'''

import os
configuration_brutus = {}

configuration_brutus["host"]             = "brutus.ethz.ch"
configuration_brutus["username"]         = "vjan"
configuration_brutus["jobname"]          = os.path.basename(os.getcwd())
configuration_brutus["cluster_scratch"]  = "/cluster/scratch_xp/public/vjan/"
configuration_brutus["cluster_home"]     = "/cluster/home/mavt/vjan/"
configuration_brutus["has_remote"]       = True
configuration_brutus["root_folder"]      = "."
configuration_brutus["queue"]            = "lsf"
configuration_brutus["transat_init_executable"]            = None
configuration_brutus["transat_executable"]                 = None
configuration_brutus["transat_init_executable"]            = None
configuration_brutus["paraview_executable"]                = None
configuration_brutus["transat_version"]                    = "MB"


configuration_mb_local = {}
configuration_mb_local["host"]             = None
configuration_mb_local["username"]         = None
configuration_mb_local["jobname"]          = os.path.basename(os.getcwd())
configuration_mb_local["cluster_scratch"]  = None
configuration_mb_local["cluster_home"]     = None
configuration_mb_local["has_remote"]       = False
configuration_mb_local["root_folder"]      = "."
configuration_mb_local["queue"]            = None
configuration_mb_local["transat_init_executable"]            = None
configuration_mb_local["transat_executable"]                 = None
configuration_mb_local["transat_init_executable"]            = None
configuration_mb_local["paraview_executable"]                = None
configuration_mb_local["transat_version"]                    = "MB"
