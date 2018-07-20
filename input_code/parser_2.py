import sys
from pycparser import c_parser, c_ast,c_generator
import re
import argparse
import itertools
import datetime
import inspect
import json

error_log_file="parser_error.log"

def error_log(error_string):
    error_file= open(error_log_file,"a")
    print "Error "+str(datetime.datetime.now())+"\t"+inspect.stack()[1][3]+":\t"+error_string+"\n"
    error_file.write("Error "+str(datetime.datetime.now())+"\t"+inspect.stack()[1][3]+":\t"+error_string+"\n")
    error_file.close()

def extract_variable_info_for(for_node):
    variable=for_node.init.decls[0].type.declname
    start=for_node.init.decls[0].init.value
    end=for_node.cond.right.value
    step = for_node.next.rvalue.value 
    return (variable,start,end,step)

def extract_inner_for(outer_for_loop_node):
    inner_block =  outer_for_loop_node.stmt.block_items[0]
    block_type = type(inner_block)
    if block_type == c_ast.For:
        return inner_block
    else:
        return None

def extract_nesting_depth_for(outer_for_loop_node):
     type_outer_for = type(outer_for_loop_node)
     depth =0 
     if type_outer_for == c_ast.For:
        depth+=1
        current_block =outer_for_loop_node
        current_block = extract_inner_for(current_block)
        while current_block is not None:
            depth+=1
            current_block = extract_inner_for(current_block)
     return depth

def extract_polymem_loop(ast):
    index=0
    for i in ast.ext[0].body.block_items:
        typ = type(i)
        if typ == c_ast.Pragma:
            content =i.string
            content = re.sub(' +',' ',content)
            content_list = content.split(" ")
            if content_list[0] == "polymem" and content_list[1]=="loop":
                return ast.ext[0].body.block_items[index+1]
        index+=1
    return none

def extract_array_and_scalar_informations(ast):
    scalar_dict={}
    array_dict={}
    for i in ast.ext[0].body.block_items:
        typ = type(i)
        if typ == c_ast.Decl:
            decl_typ=type(i.type)
            if decl_typ == c_ast.TypeDecl:
                name= i.type.declname
                vartype= i.type.type.names[0]
                val=i.init.value
                scalar_dict[name]=(vartype,val)
            if decl_typ == c_ast.ArrayDecl:
                array_name = i.type.type.type.declname
                size_x = i.type.dim.value
                size_y = i.type.type.dim.value
                array_dict[array_name]=(size_x,size_y)
    return (scalar_dict,array_dict)

def extract_if_condition(inner_for_node,loop_iterators,scalar_dict):
    if_stmt=inner_for_node.stmt.block_items[0]
    generator = c_generator.CGenerator()
    #if_stmt.iftrue.block_items[0].show()
    #check if the only ID used are loop iterators and scalars

    condition=generator.visit(if_stmt.cond)
    condition = re.sub("&&"," and ",condition)
    condition = re.sub("\|\|"," or ",condition)
    function=""
    function+="def filter("
    first=True
    for it in loop_iterators:
        if not first:
            function+=","
        function+=it[0]
        first=False
    function+="): "
    first=True
    for name in scalar_dict:
        if not first:
            function+="; "
        function+= name
        function+=" = "
        function+=scalar_dict[name][1]
        first=False
    function+="; "
    function+="return "+condition
    return function

def parse_array_subscript(array_subscript):
    sub_typ = type(array_subscript)
    if sub_typ == c_ast.ID:
        return array_subscript.name
    else:
        if sub_typ == c_ast.BinaryOp:
            bin_op = array_subscript
            string_op=""
            if bin_op.op == '+':
                if type(bin_op.left) == c_ast.ID:
                    string_op+=bin_op.left.name+bin_op.op 
                elif type(bin_op.left) == c_ast.Constant:
                    string_op+=bin_op.left.value+bin_op.op
                else:
                    error_log("parsing subscript at "+bin_op.left.coord)
                if type(bin_op.right) == c_ast.ID:
                    string_op+=bin_op.right.name 
                elif type(bin_op.right) == c_ast.Constant:
                    string_op+=bin_op.right.value
                else:
                    error_log("parsing subscript at "+bin_op.right.coord)
            elif bin_op.op == '-':
                if type(bin_op.left) == c_ast.ID:
                    string_op+=bin_op.left.name+bin_op.op 
                elif type(bin_op.left) == c_ast.Constant:
                    string_op+=bin_op.left.value+bin_op.op
                else:
                    error_log("parsing subscript at "+bin_op.left.coord)
                if type(bin_op.right) == c_ast.ID:
                    string_op+=bin_op.right.name 
                elif type(bin_op.right) == c_ast.Constant:
                    string_op+=bin_op.right.value
                else:
                    error_log("Error parsing subscript at "+bin_op.right.coord)
            else:
                    error_log("parsing subscript at "+bin_op.right.coord)
            
            return string_op

def parse_array_ref(array_ref):
    typ = type(array_ref.name)
    if typ == c_ast.ID:
        current_ref= [array_ref.name.name]
        subscript=parse_array_subscript(array_ref.subscript)
        current_ref.append(subscript)
    else:
        current_ref=parse_array_ref(array_ref.name)
        sub_typ = type(array_ref.subscript)
        if sub_typ == c_ast.ID:
            current_ref.append(array_ref.subscript.name)
        else:
            if sub_typ == c_ast.BinaryOp:
                bin_op = array_ref.subscript
                subscript=parse_array_subscript(array_ref.subscript)
                current_ref.append(subscript)
    return current_ref



def extract_array_ref_from_binop(binop, array_refs):
    typ = type(binop)
    if typ != c_ast.BinaryOp:
        return
    left = binop.left
    l_typ = type(left)
    if l_typ == c_ast.ArrayRef:
        #array_ref.append(parse_array_ref(left))
        l_array_ref=parse_array_ref(left)
        array_refs.append(l_array_ref)
    elif l_typ == c_ast.BinaryOp:
        extract_array_ref_from_binop(left,array_refs)
    else:
        if l_typ != c_ast.Constant:
            error_log("only array accesses and constants available in the Computation loop")

    right = binop.right
    r_typ = type(right)
    if r_typ == c_ast.ArrayRef:
        #array_ref.append(parse_array_ref(right))
        r_array_ref=parse_array_ref(right)
        array_refs.append(r_array_ref)
    elif r_typ == c_ast.BinaryOp:
        extract_array_ref_from_binop(right,array_refs)
    else:
        if r_typ != c_ast.Constant:
            error_log("only array accesses and constants available in the Computation loop")


def get_access_offset(access):
    offset_x = 0
    if "+" in access[1]:
        offset_x=access[1].split('+')[1]
    elif "-" in access[1]:
        offset_x="-"+access[1].split('-')[1]
    offset_y = 0
    if "+" in access[2]:
        offset_y=access[2].split('+')[1]
    elif "-" in access[2]:
        offset_y="-"+access[2].split('-')[1]
    return (offset_x,offset_y)


def extract_compute_infos(if_stmt,scalar_dict):
    read_accesses=[]
    write_accesses=[]
    for i in if_stmt.iftrue.block_items:
        typ = type(i)
        if typ == c_ast.Assignment:
            l_array_ref=parse_array_ref(i.lvalue)
            write_accesses.append(l_array_ref)
            extract_array_ref_from_binop(i.rvalue,read_accesses)
        else:
            error_log("only Assignment allowed in compute block")
    read_accesses.sort()
    read_accesses = list( read_accesses for read_accesses, _ in itertools.groupby(read_accesses))
    #Check if same array is accessed for writing and reading
    for write in write_accesses:
        if write in read_accesses:
            error_log("it is not possible to read and write from the same array in the same code block")
            return None 
    write_id=0
    write_access_labeled=[]
    #vector mapping
    vector_mapping={}
    vector_id=0
    for read in read_accesses:
        if not read[0] in vector_mapping:
            vector_mapping[read[0]]=vector_id
            vector_id+=1
    for write in write_accesses:
        if not write[0] in vector_mapping:
            vector_mapping[write[0]]=vector_id
            vector_id+=1
    #access mapping
    read_access_mapping=[]
    read_access_id=0
    for read in read_accesses:
        offsets=get_access_offset(read) 
        read_access_mapping.append(("read_port_"+str(read_access_id),read[0],offsets,read))
        read_access_id+=1
    write_access_mapping=[]
    write_access_id=0
    for write in write_accesses:
        offsets=get_access_offset(write)
        write_access_mapping.append(("write_port_"+str(write_access_id),write[0],offsets,write))
        write_access_id+=1
    return (vector_mapping,read_access_mapping,write_access_mapping)
    


def get_access_replace_label(array_ref, read_accesses_mapping, write_access_mapping):
    for access in read_accesses_mapping:
        if set(array_ref) == set(access[3]):
            return access[0]
    for access in write_access_mapping:
        if set(array_ref) == set(access[3]):
            return access[0]
    return None 

def replace_accesses_in_binop(binop,read_accesses_mapping, write_access_mapping):
    typ = type(binop)
    if typ != c_ast.BinaryOp:
        return
    left = binop.left
    l_typ = type(left)
    if l_typ == c_ast.ArrayRef:
        l_array_ref=parse_array_ref(left)
        access_label=get_access_replace_label(l_array_ref, read_accesses_mapping,write_access_mapping)
        binop.left=c_ast.ID(access_label)
    elif l_typ == c_ast.BinaryOp:
        replace_accesses_in_binop(left,read_accesses_mapping,write_access_mapping)
    else:
        if l_typ != c_ast.Constant:
            error_log("only array accesses and constants available in the Computation loop")

    right = binop.right
    r_typ = type(right)
    if r_typ == c_ast.ArrayRef:
        r_array_ref=parse_array_ref(right)
        access_label=get_access_replace_label(r_array_ref, read_accesses_mapping,write_access_mapping)
        binop.right=c_ast.ID(access_label)
    elif r_typ == c_ast.BinaryOp:
        replace_accesses_in_binop(right,read_accesses_mapping,write_access_mapping)
    else:
        if r_typ != c_ast.Constant:
            error_log("only array accesses and constants available in the Computation loop")

def replace_array_references(if_stmt_node, read_accesses_mapping, write_access_mapping):
    for i in if_stmt_node.iftrue.block_items:
        typ = type(i)
        if typ == c_ast.Assignment:
            l_array_ref=parse_array_ref(i.lvalue)
            access_label= get_access_replace_label(l_array_ref,read_access_mapping, write_access_mapping)
            i.lvalue = c_ast.ID(access_label)
            replace_accesses_in_binop(i.rvalue,read_accesses_mapping, write_access_mapping)
        else:
            error_log("only Assignment allowed in compute block")   
    generator = c_generator.CGenerator()
    new_code_block=generator.visit(if_stmt_node.iftrue)
    return new_code_block

def wrap_codeblock_in_maxj_function(new_code_block,function_name,read_access_mapping,write_access_mapping):
    write_access_label=write_access_mapping[0][0]
    wrapped_maxj_function="public DFEVector<DFEVar> "+function_name+"("
    first=True
    for read in read_access_mapping:
        if first:
            wrapped_maxj_function+="DFEVector<DFEVar> "+read[0]
            first=False
        else:
            wrapped_maxj_function+=",DFEVector<DFEVar> "+read[0]
    wrapped_maxj_function+="){"
    wrapped_maxj_function+="\n  DFEVector<DFEVar> "+write_access_label+";\n"
    wrapped_maxj_function+=new_code_block[2:]
    wrapped_maxj_function= wrapped_maxj_function[:-2]+"  return "+write_access_label+";\n}\n"
    return wrapped_maxj_function

    

parser= argparse.ArgumentParser(description="Tool extract access traces from a given input c code.")
parser.add_argument('input_c_code',metavar="input_c_code",nargs=1, help='path to the file containing the c code to analyse')
args = parser.parse_args()

input_c_code=args.input_c_code[0]


file = open(input_c_code, "r") 

text = file.read()



parser = c_parser.CParser()
ast = parser.parse(text, filename='<none')

#ast.show(showcoord=True)
count_decl =0
count_scalar = 0
count_array = 0
count_for = 0

declarations=[]
array_declarations = [] 
arrays=[]

for_loops=[]

polymem_loop = extract_polymem_loop(ast)
if polymem_loop is None:
    print "Couldn't find polymem loop"
else:
    (scalar_dict,array_dict)=extract_array_and_scalar_informations(ast)
    depth=extract_nesting_depth_for(polymem_loop)
    print "polymem loop depth is "+str(depth)
    nested_loops=[]
    current_loop = polymem_loop
    last_loop =""
    loops_info=[]
    for i in range(0,depth):
        last_loop=current_loop
        iterator_info = extract_variable_info_for(current_loop) 
        nested_loops.append(iterator_info)
        current_loop = extract_inner_for(current_loop)
        print iterator_info
        loops_info.append(iterator_info)
    filter_function=extract_if_condition(last_loop,nested_loops,scalar_dict)
    exec filter_function
    out_file = open(input_c_code[:-2]+".atrace","w")
    if len(loops_info) >2:
        for t in xrange(loops_info[0][1],loops_info[0][2],loops_info[0][3]):
            for i in xrange(loops_info[1][1],loops_info[1][2],loops_info[1][3]):
                for j in xrange(loops_info[2][1],loops_info[2][2],loops_info[2][3]):
                    if filter(i,j):
                        print "A["+str(i)+"]"+"["+str(j)+"]"
    else:
        for i in xrange(int(loops_info[0][1]),int(loops_info[0][2]),int(loops_info[0][3])):
            for j in xrange(int(loops_info[1][1]),int(loops_info[1][2]),int(loops_info[1][3])):
                if filter(i,j):
                    #print "A["+str(i)+"]"+"["+str(j)+"]"
                    out_file.write("A["+str(i)+"]"+"["+str(j)+"],")

    # Extracting info about the computation

    if_stmt=last_loop.stmt.block_items[0]
    (vector_mapping,read_access_mapping,write_access_mapping)=extract_compute_infos(if_stmt,scalar_dict)
    print "vector mapping:" +str(vector_mapping)
    print "read_access_mapping:"+str(read_access_mapping)
    print "write_access_mapping:"+str(write_access_mapping)
    with open(input_c_code[:-2]+".vec_info","w") as vec_info_file:
        json.dump((vector_mapping,read_access_mapping,write_access_mapping),vec_info_file)
    updated_code_block= replace_array_references(if_stmt,read_access_mapping,write_access_mapping)
    maxj_compute_fnc = wrap_codeblock_in_maxj_function(updated_code_block,"compute",read_access_mapping,write_access_mapping)
    out_compute_file = open(input_c_code[:-2]+".maxj_compute","w")
    out_compute_file.write(maxj_compute_fnc)
    #dumping loop informations
    with open(input_c_code[:-2]+".loop_info","w") as loop_info_file:
        json.dump(loops_info,loop_info_file) 
    #dumping vector sizes informations
    with open(input_c_code[:-2]+".vec_size_info","w") as vec_size_info_file:
        json.dump(array_dict,vec_size_info_file) 


