from instrumenter import CodeInstrumenter
import argparse
import json

from pycparser import c_parser, c_ast,c_generator


parser= argparse.ArgumentParser(description="Tool to generate a benchmark code from a given input c code.")
parser.add_argument('input_source_code',metavar="input_source_code",nargs=1, help='path to the file containing the DFE host code.')
parser.add_argument('access_trace',metavar="access_trace",nargs=1, help='path to the file containing the access trace generated for the source code')
#parser.add_argument('vector_mapping_file',metavar="vector_mapping_file",nargs=1, help='path to the file containing the polymem configuration options')



args = parser.parse_args()

input_source_code=args.input_source_code[0]
access_trace_file=args.access_trace[0]

with open(input_source_code) as f:
    input_c_code_string = f.read()

with open(access_trace_file) as f:
    access_trace_string = f.read()
    number_of_sequential_accesses=len(access_trace_string.split(","))

print input_c_code_string
instrumenter=CodeInstrumenter(input_c_code_string,["Schedule","max_file_t","max_engine_t","PRFStream_actions_t"])

instrumenter.add_include('#include <sys/time.h>')
instrumenter.add_include('#include <float.h>')
instrumenter.add_include('#include <limits.h>')
instrumenter.add_include('#include <math.h>')
instrumenter.add_include('#include <unistd.h>')
instrumenter.add_include('#include <stdlib.h>')
instrumenter.add_include('#include <stdio.h>')

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
        int size=87040;
        int num_copy=1;
        static char	*label[3] = {"Initialization:      ","Kernel:              ","Finalization:        "};
        static double	avgtime[3] = {0}, maxtime[3] = {0},
		mintime[3] = {FLT_MAX,FLT_MAX,FLT_MAX};
        double		t, times[4][NTIMES];

        if(argc>1){
            num_copy=atoi(argv[1]);
        }

        double	bytes[3] = {
        1 * sizeof(double) * size,
        3 * sizeof(double) * size_used*num_copy,
        1 * sizeof(double) * size,
        };
        FILE *fp;
        if( access( "c_source_benchmark_output.csv", F_OK ) != -1 ) {
            fp  =fopen("c_source_benchmark_output.csv","a");
        }
        else{
            fp  =fopen("c_source_benchmark_output.csv","w");
            if(fp==NULL){
                printf("Problems opening the output file c_source_benchmark_output.csv\\n");
            }else{
                fprintf(fp,"Vector size(64bits elements),Initialization Bytes(B),Initialization AVG(s),Initialization Min(s),Initialization Max(s),Finalization Bytes(B),Finalization AVG(s),Finalization Min(s),Finalization Max(s),Kernel Bytes(B),Kernel AVG(s),Kernel Min(s),Kernel Max(s),Kernel MBytes,Kernel GB/s\\n");
            }    
        }
        
        #pragma polymem begin_benchmark
       '''

instrumenter.insert_beginning_of_main(string)
start_init_timer="times[0][k] = mysecond();"
instrumenter.insert_after_pragma("begin_benchmark",start_init_timer)
print instrumenter.generate_code()

mysecond_code='''
    double mysecond()
{

        struct timeval tp;
        int i;

        i = gettimeofday(&tp,NULL);
        return ( (double) tp.tv_sec + (double) tp.tv_usec * 1.e-6 );
}'''
instrumenter.insert_funct_outside_main(mysecond_code)
print instrumenter.generate_code()

end_load_timer='''
            times[0][k] = mysecond() - times[0][k];
'''
instrumenter.insert_before_pragma('loop',end_load_timer)


start_compute_timer='''
            times[1][k] = mysecond();
'''
kernel_loop=instrumenter.get_block_after_pragma('loop')
benchmark_for_loop='''
for(int repeat=0;repeat<num_copy;repeat++){
    #pragma to_replace
    #pragma to_replace2
}
'''
loop_node= instrumenter.wrap_and_parse_snippet(benchmark_for_loop)
loop_node[0].show()
loop_node[0].stmt.block_items=[kernel_loop]
loop_node[0].stmt.show()
instrumenter.replace_block_after_pragma("loop",loop_node)

instrumenter.insert_before_pragma('loop',start_compute_timer)
end_compute_timer='''
            times[1][k] = mysecond() - times[1][k];
            times[2][k] = mysecond();
'''
instrumenter.insert_after_pragma('loop',end_compute_timer)

end_benchmark='''
            times[2][k] = mysecond() - times[2][k];
            #pragma polymem end_benchmark
'''
instrumenter.insert_end_of_main(end_benchmark)
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
        printf("Function             Best Rate MB/s  Avg time     Min time     Max time     Bytes\\n");
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
            fprintf(fp,"%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\\n",size,bytes[0],avgtime[0],mintime[0],maxtime[0],bytes[2],avgtime[2],mintime[2],maxtime[2],bytes[1]
                ,avgtime[1],mintime[1],maxtime[1],bytes[1]/1024/1024,1.0E-09 * bytes[1]/mintime[1]);
            fclose(fp);
        }
'''
instrumenter.insert_end_of_main(compute_benchmark_results_and_write)
print instrumenter.generate_code()

with open("c_source_benchmark.c","w") as f:
    f.write(instrumenter.generate_code())

 





