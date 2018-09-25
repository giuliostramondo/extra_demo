from pycparser import c_parser, c_ast,c_generator
import re

class CodeInstrumenter:
    includes=[]
    code_no_includes=[]
    ast=[]
    added_typedefs=0
    def __init__(self, code,typedefs=[]):
        self.added_typedefs=len(typedefs)
        print self.added_typedefs
        self.extract_includes(code,typedefs)
        self.parser = c_parser.CParser()
        self.ast = self.parser.parse(self.code_no_includes,None)

    def extract_includes( self , code,typedefs=[] ):
        code_no_include_list=[]
        for line in code.splitlines():
           if not line.startswith('#include') and not line.startswith('#define'):
               code_no_include_list.append(line) 
           else:
                self.includes.append(line)
        for typ in typedefs:
            code_no_include_list=["typedef int "+typ+";"]+code_no_include_list 
        self.code_no_includes = "\n".join(code_no_include_list)

    def add_include( self, string ):
        self.includes.append( string )

    def wrap_and_parse_snippet(self,code,typedefs=[]):
        code="int main(int argc, char* argv[]){\n"+code+"\n}\n"
        for t in typedefs:
            code="typedef int "+t+";\n"+code 
        print code
        node_ast = self.parser.parse(code)
        return node_ast.ext[len(typedefs)].body.block_items

    def find_main_func(self):
        index=0
        for i in self.ast.ext:
            typ = type(i)
            if typ == c_ast.FuncDef:
                if i.decl.name == 'main':
                    return index
            index+=1
        return -1

    def insert_funct_outside_main(self,function_code,typedefs=[]):
        for t in typedefs:
            code="typedef int "+t+";\n"+function_code 
        node_ast = self.parser.parse(function_code)
        funct_node= node_ast.ext[len(typedefs)]
        main_index=self.find_main_func()
        print "AST EXT"
        print self.ast.ext
        print "AST FUNCTION"
        print funct_node
        self.ast.ext[main_index:main_index]=[funct_node]


#    def find_polymem_loop(self):
#        func_index=self.find_main_func()
#        index=0
#        for i in self.ast.ext[func_index].body.block_items:
#            typ = type(i)
#            if typ == c_ast.Pragma:
#                content =i.string
#                content = re.sub(' +',' ',content)
#                content_list = content.split(" ")
#                if content_list[0] == "polymem" and content_list[1]=="loop":
#                    return index
#            index+=1
#        return -1

    def find_polymem_pragma(self,pragma_name):
        func_index=self.find_main_func()
        index=0
        for i in self.ast.ext[func_index].body.block_items:
            typ = type(i)
            if typ == c_ast.Pragma:
                content =i.string
                content = re.sub(' +',' ',content)
                content_list = content.split(" ")
                if content_list[0] == "polymem" and content_list[1]==pragma_name:
                    return index
            index+=1
        return -1

    def find_polymem_loop(self):
        block_id=self.find_polymem_pragma("loop")
        return block_id

    def find_polymem_offload(self):
        block_id = self.find_polymem_pragma("offload")
        return block_id

    def insert_after_polymem_offload(self, string,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(string,typedefs)
        index_polymem=self.find_polymem_offload()
        if index_polymem == -1:
            print "Error: Could not find Polymem offload"
        func_index=self.find_main_func()
        self.ast.ext[func_index].body.block_items[index_polymem+2:index_polymem+2]=node_ast

    def insert_before_pragma(self,pragma_name,code,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(code,typedefs)
        block_index= self.find_polymem_pragma(pragma_name)
        if block_index == -1:
            print "Error: Could not find pragma "+pragma_name
        func_index=self.find_main_func()
        self.ast.ext[func_index].body.block_items[block_index:block_index]=node_ast

    def insert_after_pragma(self,pragma_name,code,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(code,typedefs)
        block_index= self.find_polymem_pragma(pragma_name)
        if block_index == -1:
            print "Error: Could not find pragma "+pragma_name
        func_index=self.find_main_func()
        self.ast.ext[func_index].body.block_items[block_index+2:block_index+2]=node_ast

    def insert_node_right_after_pragma(self,pragma_name,node_ast,typedefs=[]):
        block_index= self.find_polymem_pragma(pragma_name)
        if block_index == -1:
            print "Error: Could not find pragma "+pragma_name
        func_index=self.find_main_func()
        self.ast.ext[func_index].body.block_items[block_index+1:block_index+1]=node_ast

    def insert_before_polymem_loop(self, string,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(string,typedefs)
        index_polymem=self.find_polymem_loop()
        if index_polymem == -1:
            print "Error: Could not find Polymem loop"
        func_index=self.find_main_func()
        self.ast.ext[func_index].body.block_items[index_polymem:index_polymem]=node_ast
 
    def insert_after_polymem_loop(self, string,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(string,typedefs)
        index_polymem=self.find_polymem_loop()
        if index_polymem == -1:
            print "Error: Could not find Polymem loop"
        func_index=self.find_main_func()
        self.ast.ext[func_index].body.block_items[index_polymem+2:index_polymem+2]=node_ast

    def extract_nodes_between_pragmas(self,pragma1,pragma2):
        block_index1= self.find_polymem_pragma(pragma1)
        block_index2= self.find_polymem_pragma(pragma2)
        func_index=self.find_main_func()
        selected_blocks=[]
        for i in range(block_index1+1,block_index2):
            selected_blocks.append(self.ast.ext[func_index].body.block_items[i])
        return selected_blocks

    def remove_nodes_between_pragmas(self,pragma1,pragma2):
        block_index1= self.find_polymem_pragma(pragma1)
        block_index2= self.find_polymem_pragma(pragma2)
        func_index=self.find_main_func()
        selected_blocks=[]
        for i in range(block_index1+1,block_index2):
            del self.ast.ext[func_index].body.block_items[block_index1+1]

    def insert_inplaceof_polymem_loop(self, string, typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(string,typedefs)
        index_polymem=self.find_polymem_loop()
        if index_polymem == -1:
            print "Error: Could not find Polymem loop"
        func_index=self.find_main_func()
        del self.ast.ext[func_index].body.block_items[index_polymem+1]
        self.ast.ext[func_index].body.block_items[index_polymem+1:index_polymem+1]=node_ast       
    
    def insert_beginning_of_main(self,string,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(string,typedefs)
        func_index=self.find_main_func()
        curr_ast=self.ast.ext[func_index].body.block_items
        self.ast.ext[func_index].body.block_items=node_ast+curr_ast


    def insert_end_of_main(self,string,typedefs=[]):
        node_ast=self.wrap_and_parse_snippet(string,typedefs)
        func_index=self.find_main_func()
        len_body=len(self.ast.ext[func_index].body.block_items)
        self.ast.ext[func_index].body.block_items+=node_ast

    def show_ast(self):
        self.ast.show()

    def generate_code(self):
        generator = c_generator.CGenerator()
        self.code_no_includes=generator.visit(self.ast)
        code_no_include_list=self.code_no_includes.splitlines()
        for _ in range(self.added_typedefs):
            del code_no_include_list[0]
        self.code_no_includes="\n".join(code_no_include_list)
        includes_string="\n".join(self.includes)
        code=includes_string+"\n"+self.code_no_includes
        return code
        

