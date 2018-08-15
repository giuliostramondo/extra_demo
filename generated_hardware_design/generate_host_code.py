from instrumenter import CodeInstrumenter
import argparse

from pycparser import c_parser, c_ast,c_generator


parser= argparse.ArgumentParser(description="Tool to generate a DFE host code from a given input c code.")
parser.add_argument('input_c_code',metavar="input_c_code",nargs=1, help='path to the file containing the c code to analyse')
args = parser.parse_args()

input_c_code=args.input_c_code[0]

with open(input_c_code) as f:
    input_c_code_string = f.read()

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
instrumenter.add_include('#define p 2')
instrumenter.add_include('#define q 4')
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
        prfStreamInput.instream_aStream=A;
        prfStreamInput.instream_bStream=B;
        prfStreamInput.instream_cStream=C;
        prfStreamInput.outstream_aOutStream=A;
        prfStreamInput.outstream_bOutStream=B;
        prfStreamInput.outstream_cOutStream=C;
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
            PRFStream_run(StreamDFE,&prfStreamInput);
            '''

instrumenter.insert_after_polymem_loop(offload,typedefs)
print instrumenter.generate_code()
compute = '''
            prfStreamInput.param_prfMode=COMPUTE;
            #pragma polymem offload
            PRFStream_run(StreamDFE,&prfStreamInput);
        '''
instrumenter.insert_inplaceof_polymem_loop(compute,typedefs)
print instrumenter.generate_code()

with open("PRFStreamCpuCode.c","w") as f:
    f.write(instrumenter.generate_code())
    





