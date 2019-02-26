# ansible-role-sacct_gpu
Add gpu utilization stats to Slurm batch scheduler accounting db. Tested with CentOS-7.

## Background

This is intended to be used with [Slurm](https://slurm.schedmd.com/) to provide insight on job-gpu utilization. This adds short json-formatted string to 
sacct-database comment field containing stats for:

- number of used gpu's
- over job averate gpu utilization reported by nvidia-smi
- over job averate gpu memory utilization reported by nvidia-smi

## How it works

Basic idea is to run small code in the background that writes the stats every 1min. In Slurm's TaskEpilog (this is still when the db access for writing jobinfo is open) 
this information is collected per jobid and written to Comment-field of jobinfo in Slurm-Accounting-Database. 

## Deployment

Simply apply this ansible-role to your nodes. We are using this together with [OpenHPC](https://openhpc.community/) and use this directly with OHPC-images.
