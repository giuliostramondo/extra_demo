from instrumenter import CodeInstrumenter
import argparse
import json

from pycparser import c_parser, c_ast,c_generator


parser= argparse.ArgumentParser(description="Tool to generate a DFE host code from a given input c code.")
parser.add_argument('input_c_code',metavar="input_c_code",nargs=1, help='path to the file containing the c code to analyse')
parser.add_argument('polymem_cfg_file',metavar="polymem_cfg_file",nargs=1, help='path to the file containing the polymem configuration options')
parser.add_argument('vector_mapping_file',metavar="vector_mapping_file",nargs=1, help='path to the file containing the polymem configuration options')



args = parser.parse_args()

input_c_code=args.input_c_code[0]
cfg_code=args.polymem_cfg_file[0]
vector_mapping_file=args.vector_mapping_file[0]

with open(input_c_code) as f:
    input_c_code_string = f.read()

with open(vector_mapping_file) as f:
            vec_access_info = json.load(f)

#Create a vector of length len(vec_access_info)
vectors_ids = [None] * len(vec_access_info)

for key in vec_access_info[0]:
    vec_id=vec_access_info[0][key]
    vectors_ids[vec_id]=key 
#vectors_ids contains the ordered lables of the vectors
print vectors_ids

configuration={}
with open(cfg_code) as f:
    for line in f:
        conf_line = line.strip().split("=")
        configuration[conf_line[0]]=conf_line[1].replace('"','')

print input_c_code_string
instrumenter=CodeInstrumenter(input_c_code_string)

instrumenter.add_include('#include "Maxfiles.h"')
instrumenter.add_include('#include "MaxSLiCInterface.h"')
instrumenter.add_include('#include "schedule_utils.h"')
instrumenter.add_include('#define LOAD 0')
instrumenter.add_include('#define OFFLOAD 1')
instrumenter.add_include('#define COMPUTE 2')
instrumenter.add_include('#define M 512')
instrumenter.add_include('#define N 512')
instrumenter.add_include('#define p '+configuration['P'])
instrumenter.add_include('#define q '+configuration['Q'])
#initialize schedule

string= '''
        int schedule_len = 0;
        Schedule *s = NULL;
        if(argc > 1 ){
            char *scheduleFile = argv[1];
            schedule_len = getFileLenght(scheduleFile);
            s = parseSchedule(scheduleFile);
        }

        int size = 87040;
        int num_copy=1;
        int scheduleROMsize=(M*N/p*q);
        int *scheduleROM=NULL;

        if (s != FILE_NOT_FOUND)
            scheduleROM = compress_schedule_toROM(s,schedule_len,p*q,scheduleROMsize);
        else
            scheduleROM = malloc(scheduleROMsize*sizeof(int));
      '''


instrumenter.insert_beginning_of_main(string,['Schedule'])


string = '''
        PRFStream_actions_t prfStreamInput;
        prfStreamInput.param_VEC_SIZE=size;
        prfStreamInput.param_copy_repeats= num_copy;
        prfStreamInput.param_prfMode=LOAD;
        
        prfStreamInput.param_scheduleROMsize=0;
        '''
id_vec=0
for vec in vectors_ids:
    if id_vec==0:
        string+="prfStreamInput.instream_aStream="+vec+";"
        string+="prfStreamInput.outstream_aOutStream="+vec+";"
    if id_vec ==1:
        string+="prfStreamInput.instream_bStream="+vec+";"
        string+="prfStreamInput.outstream_bOutStream="+vec+";"
    if id_vec ==2:
        string+="prfStreamInput.instream_cStream="+vec+";"
        string+="prfStreamInput.outstream_cOutStream="+vec+";"
    id_vec+=1

string+= '''
        prfStreamInput.inmem_PRFStreamKernel_ScheduleROM=scheduleROM;
        
        max_file_t* StreamMaxFile =  PRFStream_init();
        max_engine_t* StreamDFE=max_load(StreamMaxFile,"*");

        #pragma polymem load
        PRFStream_run(StreamDFE,&prfStreamInput);
        '''

typedefs=['PRFStream_actions_t','max_file_t','max_engine_t']
instrumenter.insert_before_polymem_loop(string,typedefs)
print instrumenter.generate_code()
offload = '''
            prfStreamInput.param_prfMode=OFFLOAD;
            #pragma polymem offload
            PRFStream_run(StreamDFE,&prfStreamInput);
            '''

instrumenter.insert_after_polymem_loop(offload,typedefs)
print instrumenter.generate_code()
compute = '''
            prfStreamInput.param_prfMode=COMPUTE;
            #pragma polymem compute
            PRFStream_run(StreamDFE,&prfStreamInput);
        '''
instrumenter.insert_inplaceof_polymem_loop(compute,typedefs)
print instrumenter.generate_code()

with open("PRFStreamCpuCode.c","w") as f:
    f.write(instrumenter.generate_code())
    





