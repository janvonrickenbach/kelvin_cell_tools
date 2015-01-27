import os
import subprocess as sp
import shutil as sh
import pickle as pic
try:
  import utils as ut
except:
  print("could not import simulation")
  
import job_configurations as jc
import time
try:
  from simulation import *
except:
  print("could not import simulation")

def find_casename(src_files):
  stt_files = ut.files_ending_with(src_files,'.stt')
  if len(stt_files)!=1:
      print 'Need to have exactly one .stt file in the template directory'
      print 'Currently: '+stt_files
      self.casename=None
      sys.exit(-1)
  else:
      return stt_files[0].split(".")[0] 

class info:
   """ Info class
      Contains info of the job (mainly directory information"
  """
   def __init__(self):
      self.cluster = {}
      self.local   = {}

class command_runner:
   """
    The job of this class is to run a command 
    It conains an init function that sets up 
    the communication channel if needed
    __call__ is used to run the command
    it should return the tuple (stdin,stdout,stderr)
   """
   pass

class command_runner_paramiko(command_runner):
   """
      This implementation of the command runner 
      uses the paramiko module to run commands 
      on the cluster
   """
   def __init__(self,sim_class):
      self.sim_class = sim_class

      import paramiko as pa
      self.pa = pa
      self.cdw         = 'cd ' + self.sim_class.info.cluster["dir"]

   def connect(self):
      self.ssh = self.pa.SSHClient()
      self.ssh.set_missing_host_key_policy(self.pa.AutoAddPolicy())
      self.ssh.connect(self.sim_class.info.cluster["host"],
                       username=self.sim_class.info.cluster["username"])

   def __call__(self,command,quiet=False):
      self.connect()
      command = self.cdw  + "; " + command
      stdin, stdout, stderr = self.ssh.exec_command(command)
      while not stdout.channel.exit_status_ready():
         time.sleep(0.1)
      self.exit()
      if not quiet:
         self._print_stdout(stdout,stderr)
      return (stdout,stderr)

   def _print_stdout(self,stdout,stderr):
      for i in stdout:
         print(i[0:-1])
      for i in stderr:
         print(i[0:-1])

   def exit(self):
      self.ssh.close()

class command_runner_local(command_runner):
   """
   This implementation of the command runner 
   runs a command locally with subprocess
   """
   def __init__(self,sim_class):
      self.sim_class = sim_class

   def __call__(self,command,quiet=False,wait=True):
  
      temp_command = []
      for item in command:
         if not item == '':
            temp_command.append(item)
      
      directory = self.sim_class.info.local["sim_folder"]
      process = sp.Popen(temp_command,cwd=directory,shell=False,stdout=open(os.path.join(directory,"std_out_commands.log"),'a'),stderr=open(os.path.join(directory,"std_err_commands.log"),'a'))
      if wait:
         process.wait()
      else:
         self.sim_class.status_handler.process = process
      process.stderr = [""]
      if not quiet:
         pass
         #self._print_stdout(process.stdout,process.stderr)
      return (process.stdout,process.stderr)

   def _print_stdout(self,stdout,stderr):
      for line in stdout:
         print(line[0:-1])
      for line in stderr:
         print(line[0:-1])

class application:
   """
     An application can be run from the job directory
     The commmand that is run is 
     application.prefix  application.run_command application.argument
     load is the command that should be run before the application
     is started and can be used to load the correct environment
     The prepare function can be implemented if the application
     has to be prepared (compiled, copied) before it is run 
     It can make sense to implement the same application (TransAT)
     two different classes depending where it should be run
    """
   def prepare(self):
      pass

class application_transatmb_remote(application):
   def __init__(self,sim_class,executable=None):
       self.executable = executable
       self.sim_class = sim_class
 
       self.prefix      = "mpirun"
       self.run_command = "./transatmbDP"
       self.argument    = " ".join(["-pc_hypre_boomeramg_max_iter" 
                                   ,"-pc_hypre_boomeramg_coarsen_type HMIS" 
                                   ,"-pc_hypre_boomeramg_interp_type ext+i" 
                                   ,"-pc_hypre_boomeramg_P_max 4" 
                                   ,"-pc_hypre_boomeramg_strong_treshold 0" 
                                   ,"-pc_hypre_boomeramg_agg_nl 2"])

       self.load      = None

   def stop(self):
      self.sim_class.command_runner_remote('echo "stop" > transat_mb.rti')

   def prepare(self):
      if self.executable:
         exec_path = os.path.join(sim_class.info.cluster["home"],self.executable,'bin','transatmbDP')
         cp_command = 'cp ' + exec_path + ' ' +  sim_class.info.cluster["dir"]
      else:
         cp_command = 'cp $TRANSATMB_PAR_DIR/bin/transatmbDP ' + self.sim_class.info.cluster["dir"]
      if self.load:
         self.sim_class.command_runner_remote(self.load+";"+cp_command)
      else:
         self.sim_class.command_runner_remote(cp_command)
      
   # The change input function should be generalized. Probably the application
   # class is not the best place to implement this
   def change_input(self,key,value,newline=None,filename="transat_mb.inp"):

      separator = " "
      if filename == "properties.dat":
         separator = " "
      if filename == "transat_mb.inp":
         separator = "="

      input_path      = os.path.join(self.sim_class.info.local["sim_folder"],filename)
      input_save_path = os.path.join(self.sim_class.info.local["sim_folder"],filename+"_save")
      sh.copy(input_path,input_save_path)
      f = file(input_save_path)
      newlines = []
      for line in f:
         if key.lower() in line.lower():
            if newline:
               line = newline
            else:
               line = key + separator +  value + "\n"
         newlines.append(line)
      outfile = file(input_path,"w")
      outfile.writelines(newlines)
      f.close()
      outfile.close()

class application_transat_local(application):
    def __init__(self,sim_class,executable=None):
        self.executable = executable
        self.sim_class = sim_class
 
        self.prefix      = ""
        if executable:
           self.run_command = executable
        else:
           self.run_command = os.path.join(os.getenv("TRANSATDIR"),"bin","transatDP")
        self.argument    = ""
        

        self.load      = None

class application_wc_python(application):
    def __init__(self,sim_class,executable=None):
        self.executable = executable
        self.sim_class = sim_class
 
        self.prefix      = ""
        if executable:
           self.run_command = executable
        else:
           self.run_command = "./wc_test.py"
        self.argument    = ""
        

        self.load      = None

class application_transatmb_local(application):
    def __init__(self,sim_class,executable=None):
        self.executable = executable
        self.sim_class = sim_class
 
        self.prefix      = "mpiexec"
        if executable:
           self.run_command = executable
        else:
           self.run_command = os.path.join(os.getenv("TRANSATMB_PAR_DIR"),"bin","transatmbDP")
        self.argument    = ""

        self.load      = 'mkdir RESULT'

    def change_input(self,input,value):

      input_path      = os.path.join(self.sim_class.info.local["sim_folder"],"transat_mb.inp")
      input_save_path = os.path.join(self.sim_class.info.local["sim_folder"],"transat_save.inp")
      sh.copy(input_path,input_save_path)
      f = file(input_save_path)
      newlines = []
      for line in f:
        splitted_line = line.split("=")
        if splitted_line[0].strip().lower() ==  input.strip().lower():
          line = input + "=" +  value + "\n"
        newlines.append(line)
      outfile = file(input_path,"w")
      outfile.writelines(newlines)
      f.close()


class application_tmb_init_remote(application):
   def __init__(self,sim_class,executable=None):
      self.sim_class = sim_class
      self.prefix = 'mpirun'
      self.run_command = './transatmbinitialDP'
      self.argument    = ''
      self.load        = None

class application_compile_init_remote(application):
   def __init__(self,sim_class,executable=None):
      self.sim_class = sim_class
      self.prefix = ''
      self.run_command = 'tmb_init_compile.py'
      self.argument    = ''
      self.load        = None
      
class application_tmb_init_local(application):
   def __init__(self,sim_class,executable=None):
      self.sim_class = sim_class
      self.prefix = ''
      self.run_command = './transatmbinitialDP'
      self.argument    = ''
      self.load        = None
   def prepare(self):
        if self.load:
           self.sim_class.command_runner_remote(self.load+";"+"tmb_init_compile.py")
        else:
           self.sim_class.command_runner_remote(["tmb_init_compile.py"])
      

class application_paraview_remote(application):
   def __init__(self,sim_class,executable=None):
      self.sim_class = sim_class
      if executable:
         self.executable = executable
      else:
         self.executable = '/cluster/home/vjan/ParaView-4.0.1-Linux-64bit/bin/pvbatch --use-offscreen-rendering'

      self.prefix         = 'mpirun'
      self.argument       = ''
      self.run_command    = self.executable
      self.load           = 'source $HOME/.bashrc_paraview'   
   def prepare(self):
      pass

class application_paraview_local(application):
   def __init__(self,sim_class,executable=None):
      self.sim_class = sim_class
      if executable:
         self.executable = executable
      else:
         self.executable = 'pvpython'

      self.prefix         = ''
      self.argument       = ''
      self.run_command    = self.executable
      self.load           = ''   
   def prepare(self):
      pass

class application_restarter_remote(application):
   def __init__(self,sim_class):
      self.sim_class = sim_class
      self.run_command = './post_command.py'
      self.prefix      = ''
      self.argument    = ''
      self.load        = None

   def prepare(self):
      self._create_post_command()

   def _create_post_command(self):
      """ This essentially creates the restarter application
          and copies it and its dependencies to the cluster. 
          Not yet the perfect solution
      """
      post_command = []
      post_command.append('#! /usr/bin/python')
      post_command.append('import simulation_brutus as js')
      post_command.append('import job_configurations as jc')
      post_command.append('import subprocess as sp')
      post_command.append('config = jc.configuration_mb_local')
      post_command.append('config["root_folder"] = \"' + self.sim_class.info.cluster["scratch"] + '\"')
      post_command.append('config["jobname"] = \"' + self.sim_class.info.local["jobname"] + '\"')
      post_command.append('job = js.job(**config)')
      post_command.append('job.application.change_input("RESTART_METHOD",' + '\'\\\"restart\\\"\'' + ')')
      post_command.append('copy_command = "cp " + job.info.local["project_name"] + ".runb " + job.info.local["project_name"] + ".rstb"')
      post_command.append('copy_command = copy_command.split()') 
      post_command.append('job.command_runner(copy_command)')

      file = open(os.path.join(self.sim_class.info.local["sim_folder"],'post_command.py'),'w')
      for line in post_command: 
        file.write(line + '\n')
      file.close()
      self.sim_class.communicator.sync_input()
      command = "cp /home/vonrickenbach/contrib_git/python/cluster_interface/simulation_brutus.py "  + self.sim_class.info.local["sim_folder"]
      command = command.split()
      self.sim_class.command_runner(command)


class app_runner:
   """ This class runs the application.
       Based on the application it submits a job
       to the queueing system
   """
   pass

class app_runner_lsf(app_runner):
   """ This class runs the application with lsf.
        Essentially adds bsub and the lsf queue arguments
        It also supports a restart_application that will
        be submitted to restart the jobs for job chaining
    """
   def __init__(self,sim_class):
      self.sim_class = sim_class

   def kill_app(self,arg=' '):
      kill_command = "bkill " + arg + " -J " + self.sim_class.info.local["jobname"]
      self.sim_class.command_runner_remote(kill_command)


   def run_app(self,application,restart_application,nproc='8',time='60',memory='2048',output='std_out.log' \
                      , njobs=2,restart=False,endtime=40,quiet=False,depend=False,args=None):
      
      jobname = self.sim_class.info.local["jobname"]
      application.prepare()

      if args:
         application.argument = args

      if restart_application:
         restart_application.prepare()

      try:
         application.change_input("TLIMIT",str(int(time)*60-endtime*60))
      except:
         pass

      self.sim_class.communicator.sync_input()

      dependency_string = '\"ended(' + jobname + ')\"'

      for i in range(njobs):
         if i==0:
            if depend:
              dependency=dependency_string
            else:
              dependency=None
            if restart == True:
               bsub_command = self._run_app_command(restart_application
                                                    ,nproc="1"
                                                    ,time="60"
                                                    ,memory=memory
                                                    ,output="post_command.log"
                                                    ,depend=dependency)
               print bsub_command
               self.sim_class.command_runner_remote(bsub_command)
               dependency = dependency_string
         else:
            dependency = dependency_string
  
         bsub_command = self._run_app_command(application
                                          ,nproc=nproc
                                          ,time=time
                                          ,memory=memory
                                          ,output=output
                                          ,depend=dependency)
         print bsub_command
         self.sim_class.command_runner_remote(bsub_command,quiet=quiet)
  
         dependency = dependency_string
  
         if i < njobs-1:
            bsub_command = self._run_app_command(restart_application
                                             ,nproc="1"
                                             ,time="60"
                                             ,memory=memory 
                                             ,output="post_command.log"
                                             ,depend=dependency)
            print bsub_command
            self.sim_class.command_runner_remote(bsub_command,quiet=True)


   def _run_app_command(self,application,nproc='8',time='60',memory='2048',output='std_out.log', depend=None):


      if not depend:
         dependency = ''
      else:
         dependency = '-w ' + depend

      argument_list = ['bsub'
                      ,'-n',nproc
                      ,'-W',time
                      ,'-R "rusage[mem='+memory+']"'
                      ,'-J',self.sim_class.info.local["jobname"]
                      ,'-o',output
                      ,'-e',"std_err.log"
                      ,dependency
                      ,application.prefix
                      ,application.run_command
                      ,application.argument]

      if application.load:
         bsub_command = application.load +'; ' + " ".join(argument_list)
      else:
         bsub_command = " ".join(argument_list)
      return bsub_command

class app_runner_local(app_runner):
   def __init__(self,sim_class):
      self.sim_class = sim_class

   def run_app(self,application,restart_application,nproc,time,memory,output \
                             ,njobs,restart,endtime,quiet,depend=False,args=None):
      application.prepare()
      # This is pretty ugly...
      if int(nproc) > 1:
         prefix = " ".join([application.prefix,"-n",nproc])
      else:
         prefix = application.prefix

      run_command = " ".join([prefix
                             ,application.run_command
                             ,application.argument]).split()
      if application.load:
        self.sim_class.command_runner(application.load.split())
      self.sim_class.command_runner(run_command,quiet,wait=False)
      
   def kill_app(self):
      if self.sim_class.status_handler.process.poll() == None:
         self.sim_class.status_handler.process.terminate()


class communicator:
   pass

class communicator_remote(communicator):
   def __init__(self,sim_class):
      self.sim_class = sim_class
      mkdir_command = 'mkdir ' + self.sim_class.info.cluster["dir"]
      self.sim_class.command_runner_remote(mkdir_command)

   def sync_input(self):
      print "==================================================="
      print " Syncing Current Working Directory with Cluster "
      print "==================================================="

      f = open(os.path.join(self.sim_class.info.local["sim_folder"],"job.pickle"),"w")
      pic.dump(self.sim_class.postprocess,f)
      f.close()

      local_dir     = self.sim_class.info.local["sim_folder"]
      cluster_dir   = self.sim_class.info.cluster["ssh"]
      rsync_command = 'rsync -a -ave ssh --exclude RESULT --exclude \"*.runb\" --exclude processed ' \
                       + local_dir + '/ '                    \
       	              + cluster_dir
      rsync_command = rsync_command.split()
      self.sim_class.command_runner(rsync_command)
      chmod_command = 'chmod +x post_command.py'
      self.sim_class.command_runner_remote(chmod_command)


   def sync_result(self,dirname="RESULT"):
      local_dir     = self.sim_class.info.local["sim_folder"]
      cluster_dir   = os.path.join(self.sim_class.info.cluster["ssh"],dirname)

      rsync_command = 'rsync -a -ave ssh ' + cluster_dir + ' ' + local_dir
      rsync_command = rsync_command.split()
      print "==================================================="
      print " Syncing " + dirname + " folder  with Cluster      "
      print "==================================================="
      self.sim_class.command_runner(rsync_command)

   def get_log(self,filename="std_out.log",n=10,quiet=False):
      self.cp(filename)
      loc_file = os.path.join(self.sim_class.info.local["sim_folder"],filename+"_cluster")
      self.sim_class.command_runner(["tail","-n",str(n),loc_file],quiet)
      return os.path.join(loc_file)
    
   def cp(self,filename='std_out.log'):
      local_dir     = os.path.join(self.sim_class.info.local["sim_folder"],filename)
      cluster_dir   = os.path.join(self.sim_class.info.cluster["ssh"],filename)
      cp_command = 'rsync -ave ssh ' + cluster_dir + ' ' + local_dir + \
                    '_cluster'
                    
      cp_command = cp_command.split()
      self.sim_class.command_runner(cp_command)

class status_handler:
   pass


class status_handler_lsf:

   def __init__(self,sim_class):
      self.sim_class = sim_class

   def peek(self,arg=' '):
      peek_command = "bpeek " + arg + " -J " + self.sim_class.info.local["jobname"]
      self.sim_class.command_runner_remote(peek_command)


   def status(self):
      jobname = self.sim_class.info.local["jobname"]
      status_list = []
      stdout,stderr = self.sim_class.command_runner_remote("bjobs -J " + jobname,quiet=True)
      for line in stdout:
         if "PEND" in line:
            status_list.append("pending")
         elif "RUN" in line:
            status_list.append("running")

      for line in stderr:
         if "not found" in line:
            print("job not found")
            status_list.append("job not found")


      stdout,stderr = self.sim_class.command_runner_remote("bjobs -p -J " + jobname,quiet=True)
      pending_list = []
      for line in stdout:
         if "invalid" in line:
            pending_list.append("invalid job was killed")
            self.sim_class.app_runner.kill()
         elif "host based" in line:
            pending_list.append("host based")
         elif "waiting for scheduling" in line:
            pending_list.append("waiting for scheduling")
         elif "satisfied" in line:
            pending_list.append("dependency condition not satisfied")
         elif "job slot limit" in line:
            pending_list.append("reached job slot limit")
         elif "PEND" in line:
            pass
        
      print("=========================")
      print("Summary of job " + jobname)
      print("Job status")
      print(status_list)
      print("Reason for pending")
      print(pending_list)
      print("=========================")

      for status in status_list:
         if status == "job not found":
             return "finished"
         elif status == "running":
             return "running"

      # Not running 
      return "pending"


   def alljobs(self,arg=' '):
      self.sim_class.command_runner_remote("bjobs " + arg)
   def ltnt(self,arg=' '):
      self.sim_class.command_runner_remote("busers -w lsf_pouli")

class status_handler_local:

    def __init__(self,sim_class):
       self.sim_class = sim_class


    def status(self):
       return self.process.poll()
  


class job:
   def __init__(self,**kwargs):

      self.info = info()
      if kwargs["has_remote"]:
         self.info.cluster["host"]          = kwargs["host"]
         self.info.cluster["username"]      = kwargs["username"]
         self.info.cluster["scratch"]       = kwargs["cluster_scratch"]
         self.info.cluster["dir"]           = os.path.join(kwargs["cluster_scratch"],kwargs["jobname"])
         self.info.cluster["ssh"]           = kwargs["username"] + '@' + kwargs["host"] + ':' + self.info.cluster["dir"]

      self.info.local["jobname"]         = kwargs["jobname"]
      self.info.local["sim_folder"]      = os.path.abspath(os.path.join(kwargs["root_folder"],self.info.local["jobname"]))

      src_files                        = os.listdir(self.info.local["sim_folder"])
      try:
        self.info.local["project_name"]  = find_casename(src_files)
      except:
	print("Could not find stt file, probably not a TransAT case")


      self.command_runner        = command_runner_local(self)
      self.postprocess           = {}
      self.restart_application   = None

      if kwargs["has_remote"]:
         self.command_runner_remote = command_runner_paramiko(self)
         self.communicator          = communicator_remote(self)
         self.postprocessor         = application_paraview_remote(self,kwargs["paraview_executable"])
         if kwargs["transat_version"] == "MB":
            self.application           = application_transatmb_remote(self)
            self.restart_application   = application_restarter_remote(self)
            self.init_application      = application_tmb_init_remote(self,kwargs["transat_init_executable"])
            self.compile_init_application      = application_compile_init_remote(self)
         else:
            print("Single Block code not available on remote server")

         if kwargs["queue"] == "lsf":
            self.app_runner            = app_runner_lsf(self)
            self.status_handler        = status_handler_lsf(self)
         else:
            print("Warning: queue ",queue, " not implemented")

      # Local simulation
      else:
         self.command_runner_remote = command_runner_local(self)
         self.postprocessor         = application_paraview_local(self,kwargs["paraview_executable"])
         self.status_handler        = status_handler_local(self)
         self.app_runner            = app_runner_local(self)
         if kwargs["transat_version"] == "MB":
            self.application = application_transatmb_local(self,kwargs["transat_executable"])
            self.init_application = application_tmb_init_local(self,kwargs["transat_init_executable"])
            print("Warning Initial conditions with single block code not supported")
         else:
            self.application = application_transat_local(self,kwargs["transat_executable"])
            print("Warning Initial conditions with single block code not supported")
         if kwargs["transat_version"] == "wc_python":
            self.application = application_wc_python(self,kwargs["transat_executable"])


#      print '==============================================='
#      for keys in self.info.cluster.keys():
#        print keys.ljust(15), self.info.cluster[keys].ljust(40)
#      for keys in self.info.local.keys():
#        print keys.ljust(15), self.info.local[keys].ljust(40)
#      print '==============================================='


   def run_sim(self,nproc='8',time='60',memory='2048',output='std_out.log' \
            ,njobs=2,restart=False,endtime=40,quiet=False,depend=False):
      self.app_runner.run_app(self.application,self.restart_application,nproc=nproc,time=time,memory=memory,output=output \
                          ,njobs=njobs,restart=restart,endtime=endtime,quiet=quiet,depend=depend)

   def run_init(self,nproc='8',time='60',memory='2048',output='std_out.log',quiet=False,depend=False):
      self.app_runner.run_app(self.init_application,None,nproc=nproc,time=time,memory=memory,output=output \
                          ,njobs=1,restart=False,endtime=0,quiet=quiet,depend=depend)

   def compile_init(self,nproc='8',time='60',memory='2048',output='std_out.log',quiet=False):
      self.app_runner.run_app(self.compile_init_application,None,nproc="1",time=time,memory=memory,output=output \
                          ,njobs=1,restart=False,endtime=0,quiet=quiet)

   def run_postprocess(self,script="postprocess.py",nproc='1',time='60',memory='2048',output='postprocess.out',quiet=True,depend=False,args=None):
      self.postprocessor.argument = script
      self.app_runner.run_app(self.postprocessor,None,nproc=nproc,time=time,memory=memory,output=output \
                          ,njobs=1,restart=False,endtime=0,quiet=quiet,depend=depend,args=None)

   def peek(self,arg=' '):
    self.status_handler.peek(arg=arg)

   def status(self):
      return self.status_handler.status()

   def alljobs(self,arg=' '):
      self.status_handler.alljobs(arg=arg)
   def ltnt(self,arg=' '):
      self.status_handler.ltnt(arg=arg)

   def sync_input(self):
      self.communicator.sync_input()

   def sync_result(self,dirname="RESULT"):
      self.communicator.sync_result(dirname=dirname)

   def get_log(self,filename="std_out.log",n=10,quiet=False):
      return self.communicator.get_log(filename=filename,n=n,quiet=quiet)
   
   def cp(self,filename='std_out.log'):
      self.communicator.cp(filename=filename)

   def kill(self):
      self.app_runner.kill_app()

   def stop(self):
      self.application.stop()

if __name__ == '__main__':
   from time import sleep
   
   # Testing running a local simulation
   sh.copytree(os.path.join("test","channel"),
           os.path.join("test","channel_run"))
   config = jc.configuration_mb_local
   config["jobname"] = "channel_run"
   config["root_folder"] = "test"
   print config
   simulation = job(**config)
   simulation.run_sim(nproc='3')

   while simulation.status() == None:
      print("waiting for job to finish")
      sleep(3)
   print("finished",simulation.status())
   sh.rmtree(os.path.join("test","channel_run"))
   
   
   sh.copytree(os.path.join("test","channel"),
           os.path.join("test","channel_run"))
   # Running a simulation on a remote machine
   config = jc.configuration_brutus
   config["jobname"] = "channel_run"
   config["root_folder"] = "test"
   simulation_remote = job(**config)

   simulation_remote.command_runner_remote("rm -r ../channel_run")
   simulation_remote = job(**config)
   
   simulation_remote.sync_input()
   sleep(10)
   simulation_remote.run_init(nproc='2',memory='1024')
   
   print("submitting init")
   sleep(5)
   while not simulation_remote.status() == "finished":
      sleep(5)
      print(simulation_remote.status())
   
   print("submitting sim")
   simulation_remote.run_sim(nproc='3',memory='1024',njobs=3)
   sleep(5)
   
   while not simulation_remote.status() == "finished":
      simulation_remote.peek()
      sleep(5)
      print(simulation_remote.status())
   
   print("submitting postprocess")
   simulation_remote.run_postprocess("postprocess.py")
   sleep(5)
   
   while not simulation_remote.status() == "finished":
      simulation_remote.peek()
      sleep(5)
      print(simulation_remote.status())
   
   simulation_remote.sync_result()
   simulation_remote.cp()
   simulation_remote.get_log("postprocess.out")
   simulation_remote.get_log()
   
   success_post = False
   success      = False
   
   logfile = open(simulation_remote.get_log())
   for line in logfile:
      if "2D VTK XY-FILE WRITTEN AT TIME-STEP/ITERATION:           74" in line:
         success = True
   
   logfile = open(simulation_remote.get_log("postprocess.out"))
   for line in logfile:
      if "postprocessing" in line:
         success_post = True
   
   if success_post:
      print("POSTPROCESSING SUCCESSFUL")
   else:
      print("POSTPROCESSING FAILED")
   
   if success:
      print("SIMULATION SUCCESSFUL")
   else:
      print("SIMULATION FAILED")

   if (simulation.status() == 0):
      print("LOCAL SIMULATION SUCCESSFUL")
   else:
      print("LOCAL SIMULATION FAILED")

   sh.rmtree(os.path.join("test","channel_run"))

