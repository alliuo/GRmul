read_lef {LEF}
read_lib {LIB}
read_verilog ./netlist.v
link_design {MUL_NAME}
set_max_delay -from [all_inputs] 0
set critical_path [lindex [find_timing_paths -sort_by_slack] 0]
set path_delay [sta::format_time [[$critical_path path] arrival] 4]
puts "wns $path_delay"
report_design_area
exit