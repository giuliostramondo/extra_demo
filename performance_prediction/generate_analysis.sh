#!/bin/bash 
#Export analysis to csv

function read_csv_cell {
csv_filename=$1
row=$3
column=$2
cell=`tail -n+$row $csv_filename | cut --delimiter=, -f$column | head -n 1`
echo $cell
}

declare -A bw_csv_columns_scheme=( ["ReRo"]=3 ["ReCo"]=4 ["RoCo"]=5 ["ReTr"]=6 )
declare -A bw_csv_rows_mem=( ["8"]=2 ["16"]=3 )

file_name_stem=$1
output_file=${file_name_stem}.analysis
N_sequential_read=`cat ./patterns/${file_name_stem}.atrace | sed -E "s/,/\n/g"| wc -l`
echo "Memories,P,Q,Scheme,N_sequential_read,N_parallel_read,Speedup,Efficiency,Extimated_BW,schedule_file">$output_file
for schedule in $(ls ./schedules/ | grep schedule); do 
    echo "this is i -> "$schedule 
    info=(`echo $schedule | sed "s/current_input_\(.*\)_\([0-9]\+\)mems_p\([0-9]\+\)_q\([0-9]\+\).*/\1 \2 \3 \4/"`)
    scheme=${info[0]}
    mems=${info[1]}
    p=${info[2]}
    q=${info[3]}
    Npar=`wc -l ./schedules/${schedule} | sed "s/...schedules.*//"`
    Speedup=`echo "scale=2;${N_sequential_read}/${Npar}"| bc -l`
    Efficiency=`echo "scale=2;${N_sequential_read}/(${mems}*${Npar})"| bc -l`
    echo "read_csv_cell polymem_theoretical_bw.csv ${bw_csv_columns_scheme[${scheme}]} ${bw_csv_rows_mem[${mems}]}"
    read_csv_cell "./performance_prediction/polymem_theoretical_bw.csv" ${bw_csv_columns_scheme[${scheme}]} ${bw_csv_rows_mem[${mems}]}
    echo "$bla"
    echo "${bw_csv_columns_scheme[${scheme}]}" 

    Theoretical_BW=`read_csv_cell ./performance_prediction/polymem_theoretical_bw.csv ${bw_csv_columns_scheme[${scheme}]} ${bw_csv_rows_mem[${mems}]}`
    Extimated_BW=`echo "scale=2;${Theoretical_BW}*${Efficiency}"|bc -l`
    echo "${mems},${p},${q},${scheme},${N_sequential_read},${Npar},${Speedup},${Efficiency},${Extimated_BW},./schedules/${schedule}">>$output_file 
done
#for mems in 8 16; do
#    for scheme in ReRo ReCo RoCo ReTr;do
#        Npar=`wc -l ./schedules/${file_name_stem}_${scheme}_${mems}mems.schedule | sed "s/...schedules.*//"`
#        Speedup=`echo "scale=2;${N_sequential_read}/${Npar}"| bc -l`
#        Efficiency=`echo "scale=2;${N_sequential_read}/(${mems}*${Npar})"| bc -l`
#        echo "read_csv_cell polymem_theoretical_bw.csv ${bw_csv_columns_scheme[${scheme}]} ${bw_csv_rows_mem[${mems}]}"
#        read_csv_cell "./performance_prediction/polymem_theoretical_bw.csv" ${bw_csv_columns_scheme[${scheme}]} ${bw_csv_rows_mem[${mems}]}
#        echo "$bla"
#        echo "${bw_csv_columns_scheme[${scheme}]}" 
#
#        Theoretical_BW=`read_csv_cell ./performance_prediction/polymem_theoretical_bw.csv ${bw_csv_columns_scheme[${scheme}]} ${bw_csv_rows_mem[${mems}]}`
#        Extimated_BW=`echo "scale=2;${Theoretical_BW}*${Efficiency}"|bc -l`
#        echo "${mems},${scheme},${N_sequential_read},${Npar},${Speedup},${Efficiency},${Extimated_BW}">>$output_file 
#    done
#done
