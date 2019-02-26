#!/usr/bin/python

# author mhakala
import json
import re
import subprocess

# find slurm-job-ids active on this node
def jobs_running():
   task = subprocess.Popen('ps -ef|grep "/var/spool/slurmd/"|grep job|sed s/.*job//|cut -d"/" -f1', shell=True, stdout=subprocess.PIPE)
   data = task.stdout.read()
   assert task.wait() == 0
   jobs = []

   for row in data.split('\n'):
      if len(row) > 1:
          jobs.append(row)

   return jobs

# convert pid to slurm jobid
def pid2id(pid):
   output = subprocess.check_output("cat /proc/%s/cgroup |grep cpuset" % pid, shell=True)
   m = re.search('.*job_(\d+)\/.*', output)
   if m:
      return m.group(1)
   else:
      return '0'

# get needed slurm values for each running job on the node
def job_info(jobs,current):
   for job in jobs:
      output = subprocess.check_output("scontrol -o show job %s" % job, shell=True)
      cpus   = re.search('.*NumCPUs=(\d+)\s',output)
      gres   = re.search('.*Gres=.*:(\d+)\s',output)
      nodes  = re.search('.*NumNodes=(\d+)\s',output)

      # drop multi-node jobs (will be added later if needed)
      if int(nodes.group(1)) > 1:
         del current[job]
      else:
         current[job]['ngpu']=int(gres.group(1))
         current[job]['ncpu']=int(cpus.group(1))

   return current


def gpu_info(jobinfo):
   # get gpu/mem/pid stats in a single line per gpu-core (a bit ugly to get one-liner output)
   output = subprocess.check_output("nvidia-smi -q -d pids,utilization | \
   egrep '(Gpu|^\s+Memory\s+:|Process ID|^GPU)' | \
   grep -B2 ID|grep -v '\-\-' | \
   sed 'N;N;s/\\n//g'|sed s/'\s\s*'/' '/g",  shell=True)

   for row in output.split('\n'):
      if(len(row) > 2):
         vals=row.split(' ')
         jobid=pid2id(vals[12])
         gutil = float(vals[3])
         mutil = float(vals[7])

         # only update, if jobid not dropped (multinode jobs)
         if jobid in jobinfo.keys():
            jobinfo[jobid]['util']+=gutil/jobinfo[jobid]['ngpu']
            jobinfo[jobid]['mem']+=mutil/jobinfo[jobid]['ngpu']

   return jobinfo

def read_shm():
   import os.path
   fil = '/run/gpustats.json'
   jobinfo = {}

   if(os.path.exists(fil)):
      with open(fil) as fp:
         jobinfo=json.loads(fp.read())

   return jobinfo


def write_shm(jobinfo):
   with open('/run/gpustats.json', 'w') as fp:
      json.dump(jobinfo, fp)

def main():

   # initialize stats
   current = {}
   jobs    = jobs_running()

   for job in jobs:
      current[job]={'util': 0, 'mem': 0, 'ngpu': 0, 'ncpu': 0, 'step': 1}

   # get current job info
   current = job_info(jobs, current)
   current = gpu_info(current)

   # combine with previous steps
   prev = read_shm()
   for job in jobs:
      if job in prev.keys():
         n = prev[job]['step']
         current[job]['util'] = ( float(prev[job]['util'])*n+float(current[job]['util']) )/(n+1)
         current[job]['mem']  = ( float(prev[job]['mem'])*n+float(current[job]['mem']) )/(n+1)
         current[job]['step'] = n+1

   # write json
   write_shm(current)


if __name__ == '__main__':
    main()

