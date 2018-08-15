from pycparser import c_parser, c_ast,c_generator
import re

class CodeInstrumenter:
    includes=[]
    code_no_includes=[]
    ast=[]
    def __init__(self, code):
        self.extract_includes(code)
        self.parser = c_parser.CParser()
        self.ast = self.parser.parse(self.code_no_includes,None)

    def extract_includes( self , code ):
        code_no_include_list=[]
        for line in code.splitlines():
           if not line.startswith('#include'):
               code_no_include_list.append(line) 
           else:
                self.includes.append(line)
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


    def find_polymem_loop(self):
        func_index=self.find_main_func()
        index=0
        for i in self.ast.ext[func_index].body.block_items:
            typ = type(i)
            if typ == c_ast.Pragma:
                content =i.string
                content = re.sub(' +',' ',content)
                content_list = content.split(" ")
                if content_list[0] == "polymem" and content_list[1]=="loop":
                    return index
            index+=1
        return -1

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


    def generate_code(self):
        generator = c_generator.CGenerator()
        self.code_no_includes=generator.visit(self.ast)
        includes_string="\n".join(self.includes)
        code=includes_string+"\n"+self.code_no_includes
        return code
        

