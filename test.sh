for pid in 22275 22326 22329; do
    vtune -collect memory-access -duration 15 -target-pid $pid -cpu-mask=6 -result-dir /home/ubuntu/vtune_results/results_$pid
done
