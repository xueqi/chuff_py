#!/bin/csh
cd /Volumes/Home/xueqi/lab/proj/chuff_py/chuff
if(-e parallel_jobs/parallel_1/status_files/.csh_finished) /bin/rm parallel_jobs/parallel_1/status_files/.csh_run

set output_interactive = 0
if(1 == 1) set output_interactive = 1
if(1 == 0 && 0 == 0) set output_interactive = 1

@ qcore = 1

while($qcore <= 1)
    set q_status_file = parallel_jobs/parallel_1/status_files/qsub_1_${qcore}_status

    if(-e parallel_jobs/parallel_1/list_files/qsub_list_1_${qcore}.txt) then
        set file_list = (\`cat parallel_jobs/parallel_1/list_files/qsub_list_1_${qcore}.txt\`)
    else
    if($?file_list) unset file_list
    endif

    if($output_interactive == 1 && 1 == 1 && $qcore == 1) then
    set run_in_background = 0
    else
    set run_in_background = 1
    endif

    if($?file_list) then
        if($run_in_background == 1) then
      (scripts/test_script.py $file_list  background=0 filesync_pause=120 group_mts=0 queue_name=sindelar job_type=by_arg test=0 max_cpus=1 parjob_nuke=0 q_debug=0 qsub=1 min_cores=1 cores=16 nodes=1 >>&        parallel_jobs/parallel_1/proc_log_files/qsub_1_${qcore}.log; echo $status > $q_status_file) &
    endif
    else
    echo "Note: no work for core number $qcore; skipping..."
    echo 0 > $q_status_file
    endif
    @ qcore = $qcore + 1
end

if($output_interactive == 1 && 1 == 1) then
  echo '#####################################'
  echo 'Output for node, core 1:'
  echo '#####################################'

  set file_list = (\`cat parallel_jobs/parallel_1/list_files/qsub_list_1_1.txt\`)
  set q_status_file = parallel_jobs/parallel_1/status_files/qsub_1_1_status

  scripts/test_script.py $file_list  background=0 filesync_pause=120 group_mts=0 queue_name=sindelar job_type=by_arg test=0 max_cpus=1 parjob_nuke=0 q_debug=0 qsub=1 min_cores=1 cores=16 nodes=1 |&        tee parallel_jobs/parallel_1/proc_log_files/qsub_1_1.log;

  echo $status > $q_status_file
endif

wait

