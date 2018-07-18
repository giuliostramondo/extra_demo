#!/bin/python

import time
from prf_utils import parseATrace, solveEuristically_getParallelAccesses, Shape
from os import listdir
from os.path import isfile, join
import argparse
from sys import exit


parser= argparse.ArgumentParser(description="Tool to schedule a given access trace.")
parser.add_argument('input_atrace',metavar="atrace",nargs=1, help='path to the file containing the access trace to schedule')
parser.add_argument('scheme',metavar="scheme",nargs=1, help='PolyMem scheme to use for scheduling the access trace (ReRo, ReCo, RoCo, ReTr)')
parser.add_argument('memory_x',metavar="memory_x",nargs=1, help='X dimension of PolyMem memory banks array')
parser.add_argument('memory_y',metavar="memory_x",nargs=1, help='Y dimension of PolyMem memory banks array')

args = parser.parse_args()

input_atrace=args.input_atrace[0]
scheme=args.scheme[0]
memory_x=int(args.memory_x[0])
memory_y=int(args.memory_y[0])

RoCo=([Shape.ROW, Shape.RECTANGLE,Shape.COLUMN],"RoCo")
ReRo=([Shape.ROW,Shape.RECTANGLE,Shape.MAIN_DIAGONAL,Shape.SECONDARY_DIAGONAL],"ReRo")
ReCo=([Shape.COLUMN,Shape.RECTANGLE,Shape.MAIN_DIAGONAL,Shape.SECONDARY_DIAGONAL],"ReCo")
ReTr=([Shape.RECTANGLE,Shape.TRANSPOSED_RECTANGLE],"ReTr")

access_schemes=[ReRo,ReCo,RoCo,ReTr]

scheme_to_use=0
for s in access_schemes:
    if s[1]==scheme:
        scheme_to_use=s
if scheme_to_use==0:
    print "invalid scheme"
    exit()

def write_sol(solFile,sol):
    f=open(solFile,"w")
    for s in sol:
        f.write(str(s)+"\n")
    f.close()

atrace_string = parseATrace(input_atrace)
print "Solving : "+input_atrace+" with "+scheme_to_use[1]+" scheme..."
outfile=input_atrace[:-7]+"_"+scheme_to_use[1]+"_"+str(memory_x*memory_y)+"mems_p"+str(memory_x)+"_q"+str(memory_y)+".schedule"
start_time=time.time()
sol=solveEuristically_getParallelAccesses(atrace_string[0],memory_x,memory_y,scheme_to_use[0])
time_taken=time.time()-start_time

print "Total number of points:"+str(len(atrace_string[0]))
print "Total number of parallel accesses:"+str(len(sol))
print "Time taken: "+str(time_taken/60)+" minutes"
write_sol(outfile,sol);
