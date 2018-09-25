from instrumenter import CodeInstrumenter
import argparse
import json

from pycparser import c_parser, c_ast,c_generator


parser= argparse.ArgumentParser(description="Tool to generate a DFE host code from a given input c code.")
parser.add_argument('input_host_code',metavar="input_host_code",nargs=1, help='path to the file containing the DFE host code.')
parser.add_argument('access_trace',metavar="access_trace",nargs=1, help='path to the file containing the access trace generated for the source code')
#parser.add_argument('vector_mapping_file',metavar="vector_mapping_file",nargs=1, help='path to the file containing the polymem configuration options')



args = parser.parse_args()

input_host_code=args.input_host_code[0]
access_trace_file=args.access_trace[0]
#cfg_code=args.polymem_cfg_file[0]
#vector_mapping_file=args.vector_mapping_file[0]
#
with open(input_host_code) as f:
    input_c_code_string = f.read()

with open(access_trace_file) as f:
    access_trace_string = f.read()
    number_of_sequential_accesses=len(access_trace_string.split(","))
#
#with open(vector_mapping_file) as f:
#            vec_access_info = json.load(f)
#
##Create a vector of length len(vec_access_info)
#vectors_ids = [None] * len(vec_access_info)
#
#for key in vec_access_info[0]:
#    vec_id=vec_access_info[0][key]
#    vectors_ids[vec_id]=key 
##vectors_ids contains the ordered lables of the vectors
#print vectors_ids
#
#configuration={}
#with open(cfg_code) as f:
#    for line in f:
#        conf_line = line.strip().split("=")
#        configuration[conf_line[0]]=conf_line[1].replace('"','')

print input_c_code_string
instrumenter=CodeInstrumenter(input_c_code_string,["Schedule","max_file_t","max_engine_t","PRFStream_actions_t"])

instrumenter.add_include('#include <sys/time.h>')
instrumenter.add_include('#include <float.h>')
instrumenter.add_include('#include <limits.h>')
instrumenter.add_include('#include <math.h>')
instrumenter.add_include('#define NTIMES 10')
instrumenter.add_include('# ifndef MIN')
instrumenter.add_include('# define MIN(x,y) ((x)<(y)?(x):(y))')
instrumenter.add_include('# endif')
instrumenter.add_include('# ifndef MAX')
instrumenter.add_include('# define MAX(x,y) ((x)>(y)?(x):(y))')
instrumenter.add_include('# endif')
#initialize schedule
string = "int size_used="+str(number_of_sequential_accesses)+";"
string+='''
        static char	*label[3] = {"Load:      ","Compute:   ","Offload:   "};
        static double	avgtime[3] = {0}, maxtime[3] = {0},
		mintime[3] = {FLT_MAX,FLT_MAX,FLT_MAX};
        double		t, times[4][NTIMES];
        double	bytes[3] = {
        1 * sizeof(double) * size,
        3 * sizeof(double) * size_used,
        1 * sizeof(double) * size,
        };
            if(argc>2){
                num_copy=atoi(argv[2]);
            }
        FILE *fp;
        if( access( "benchmark_output.csv", F_OK ) != -1 ) {
            fp  =fopen("benchmark_output.csv","a");
        }
        else{
            fp  =fopen("benchmark_output.csv","w");
            if(fp==NULL){
                printf("Problems opening the output file benchmark_output.csv\\n");
            }else{
                fprintf(fp,"Vector size(64bits elements),Load Bytes(B),Load AVG(s),Load Min(s),Load Max(s),Offload Bytes(B),Offload AVG(s),Offload Min(s),Offload Max(s),Copy Bytes(B),Copy AVG(s),Copy Min(s),Copy Max(s)\\n");
            }    
        }
       '''

instrumenter.insert_before_pragma("beginning_of_original_main",string)
print instrumenter.generate_code()

mysecond_code='''
    double mysecond()
{

        struct timeval tp;
        struct timezone tzp;
        int i;

        i = gettimeofday(&tp,&tzp);
        return ( (double) tp.tv_sec + (double) tp.tv_usec * 1.e-6 );
}'''
instrumenter.insert_funct_outside_main(mysecond_code)
print instrumenter.generate_code()

load_code='''
#pragma polymem begin_benchmark
prfStreamInput.param_prfMode=LOAD;
'''
instrumenter.insert_before_pragma('load',load_code)
print instrumenter.generate_code()
end_benchmark='''
#pragma polymem end_benchmark
'''
instrumenter.insert_after_polymem_offload(end_benchmark)
print instrumenter.generate_code()

start_load_timer='''
            times[0][k] = mysecond();
'''
instrumenter.insert_before_pragma('load',start_load_timer)
end_load_timer='''
            times[0][k] = mysecond() - times[0][k];
'''
instrumenter.insert_after_pragma('load',end_load_timer)

start_compute_timer='''
            times[1][k] = mysecond();
'''
instrumenter.insert_before_pragma('compute',start_compute_timer)
end_compute_timer='''
            times[1][k] = mysecond() - times[1][k];
'''
instrumenter.insert_after_pragma('compute',end_compute_timer)

start_offload_timer='''
            times[2][k] = mysecond();
'''
instrumenter.insert_before_pragma('offload',start_offload_timer)
end_offload_timer='''
            times[2][k] = mysecond() - times[2][k];
'''
instrumenter.insert_after_pragma('offload',end_offload_timer)
print instrumenter.generate_code()

blocks= instrumenter.extract_nodes_between_pragmas("begin_benchmark","end_benchmark")

for i in range(0,len(blocks)):
    print "block "+str(i)
    blocks[i].show()

benchmark_for_loop='''
for(int k=0;k<NTIMES;k++){
    #pragma to_replace
    #pragma to_replace2
}
'''
loop_node= instrumenter.wrap_and_parse_snippet(benchmark_for_loop)
loop_node[0].show()
loop_node[0].stmt.block_items=blocks

loop_node[0].stmt.show()
blocks= instrumenter.remove_nodes_between_pragmas("begin_benchmark","end_benchmark")
instrumenter.insert_node_right_after_pragma('begin_benchmark',loop_node)
print instrumenter.generate_code()

compute_benchmark_results_and_write='''
        for (int k=1; k<NTIMES; k++) 
        {
            for (int j=0; j<3; j++) {
            avgtime[j] = avgtime[j] + times[j][k];
            mintime[j] = MIN(mintime[j], times[j][k]);
            maxtime[j] = MAX(maxtime[j], times[j][k]);
            }
        }
        printf("Function    Best Rate MB/s  Avg time     Min time     Max time     Bytes\\n");
        for (int j=0; j<3; j++) {
            avgtime[j] = avgtime[j]/(double)(NTIMES-1);

            printf("%s%12.1f  %11.6f  %11.6f  %11.6f  %f\\n", label[j],
               1.0E-06 * bytes[j]/mintime[j],
               avgtime[j],
               mintime[j],
               maxtime[j],
                bytes[j]);
        }
        
        if(fp!=NULL){
            fprintf(fp,"%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\\n",size,bytes[0],avgtime[0],mintime[0],maxtime[0],bytes[1],avgtime[1],mintime[1],maxtime[1],bytes[2]
                ,avgtime[2],mintime[2],maxtime[2]);
            fclose(fp);
        }
'''
instrumenter.insert_end_of_main(compute_benchmark_results_and_write)
print instrumenter.generate_code()

with open("PRFStreamCpuCode_benchmark.c","w") as f:
    f.write(instrumenter.generate_code())

 





