GEM5_BIN="build/ALL/gem5.debug"
PM_SCRIPT_PATH="configs/example/gem5_library/arm_a9_with_mcpat.py"
MCPAT_PARSER="./gem5_mcpat_parser.py"
MCPAT_PATH="../mcpat"

workloads=(
    "hello-world" \
    "iax" \
    "iaxpy" \
    "daxpy" \
    "sax" \
    "saxpy"
)

cpus=(
    "o3" \
    "minor" \
    "timing"
)
for w in "${workloads[@]}"; do
    for c in "${cpus[@]}"; do
	output_dir="./mcpat-runs/$w-$c"
	echo "Exeucting: $GEM5_BIN -r --silent-redirect -q -d "$output_dir" $PM_SCRIPT_PATH --cpu_type $c --workload $w"
	./$GEM5_BIN -r --silent-redirect -q -d "$output_dir" $PM_SCRIPT_PATH --cpu_type $c --workload $w
	if [[ $c == "o3" ]]; then
	    cpu_type="out-of-order"
	else
	    cpu_type="in-order"
	fi

	python3 $MCPAT_PARSER --m5_stats "$output_dir/stats.txt" --cpu_type "$cpu_type" --mcpat_path "$MCPAT_PATH" --cpu_name $c --benchmark_name $w
    done
done


# build/ALL/gem5.debug -d ./test/ configs/example/gem5_library/arm-a9-power-modeling.py
# python3 mcpat_parser_2.py
