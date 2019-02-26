if nvidia-smi -L|grep -q GPU; then
  /usr/bin/scontrol update jobid=$SLURM_JOBID comment="`/usr/local/bin/jobinfo.pl $SLURM_JOBID`"
fi

