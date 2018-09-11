from instrumenter  import CodeInstrumenter
import argparse
import json
from pycparser import c_parser, c_ast,c_generator


parser= argparse.ArgumentParser(description="Tool to instrument a source c code and dumps the arrays values after the computation loop to file.")
parser.add_argument('input_c_code',metavar="input_c_code",nargs=1, help='path to the file containing the c code to analyse')
parser.add_argument('dfe_host_code',metavar="dfe_host_code",nargs=1, help='path to the file containing the DFE host code to analyse')
parser.add_argument('vector_mapping_file',metavar="vector_mapping_file",nargs=1, help='path to the file containing the vectors accesses information')
parser.add_argument('vector_size_file',metavar="vector_size_file",nargs=1, help='path to the file containing the vector sizes informations')


args = parser.parse_args()

input_c_code=args.input_c_code[0]
dfe_host_code=args.dfe_host_code[0]
vector_size_file=args.vector_size_file[0]
vector_mapping_file=args.vector_mapping_file[0]

with open(input_c_code) as f:
    input_c_code_string = f.read()

with open(dfe_host_code) as f:
    input_dfe_host_code_string = f.read()

with open(vector_mapping_file) as f:
            vec_access_info = json.load(f)

with open(vector_size_file) as f:
            vec_size_info = json.load(f)
#Create a vector of length len(vec_access_info)
vectors_ids = [None] * len(vec_access_info)

for key in vec_access_info[0]:
    vec_id=vec_access_info[0][key]
    vectors_ids[vec_id]=key

print vec_size_info
print vec_access_info 
print vectors_ids 
print input_c_code_string


string = 'FILE *sim_out_file;\nsim_out_file=fopen("c_source_vec.dump","w");\n'
# assume vectors have the same size
dimensions=[]
for key in vec_size_info:
    dimensions.append(vec_size_info[key][0])
    dimensions.append(vec_size_info[key][1])
    break

print dimensions

loop_id=0
for dim in dimensions:
    string += "for ( int i"+str(loop_id)+"=0;i"+str(loop_id)+"<"+str(dim)+";i"+str(loop_id)+"++){\n"
    loop_id+=1

string += 'fprintf(sim_out_file,"'
for key in vec_size_info:
    string +=key
    for dim in dimensions:
        string +="[%d]"
    string+="=%f\t"
string +='\\n"'
for key in vec_size_info:
    string +=','
    loop_id=0
    for dim in dimensions:
        string +="i"+str(loop_id)+","
        loop_id+=1
    string+=key 
    loop_id=0
    for dim in dimensions:
        string +="[i"+str(loop_id)+"]"
        loop_id+=1
string+=");\n"
for dim in dimensions:
    string+="}\n"


print string

instrumenter_c_source = CodeInstrumenter(input_c_code_string)

instrumenter_c_source.insert_after_polymem_loop(string)
with open("current_input_dump_instr.c","w") as f:
    f.write(instrumenter_c_source.generate_code())
typedefs=["Schedule","PRFStream_actions_t","max_file_t","max_engine_t"]
instrumenter_dfe_host_source = CodeInstrumenter(input_dfe_host_code_string,typedefs)
instrumenter_dfe_host_source.insert_after_polymem_offload(string.replace("c_source_vec.dump","dfe_host_vec.dump"))
with open("PRFStreamCpuCode_dump_instr.c","w") as f:
    f.write(instrumenter_dfe_host_source.generate_code())

