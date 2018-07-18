import json

#Read analysis data 
vector_informations = json.load(open("current_input.vec_info","r"))
print vector_informations

vector_mapping = vector_informations[0]
read_access_mapping = vector_informations[1]
write_access_mapping = vector_informations[2] 
print vector_mapping
print read_access_mapping
print write_access_mapping


configuration={}
with open("current_input.cfg") as f:
    for line in f:
        conf_line = line.strip().split("=")
        configuration[conf_line[0]]=conf_line[1].replace('"','')


print configuration

maxj_compute=""

with open("current_input.maxj_compute")  as f:
    maxj_compute=f.read()
print maxj_compute

#Generate kernel 

kernel_maxj_code=""

#Adding package and libraries
kernel_maxj_code+="""package prfstream;
 
 import com.maxeler.maxcompiler.v2.kernelcompiler.Kernel;
 import com.maxeler.maxcompiler.v2.kernelcompiler.RoundingMode ;
 import com.maxeler.maxcompiler.v2.kernelcompiler.KernelParameters;
 import com.maxeler.maxcompiler.v2.kernelcompiler.types.base.DFEType;
 import com.maxeler.maxcompiler.v2.kernelcompiler.types.composite.DFEVectorType;
 import com.maxeler.maxcompiler.v2.kernelcompiler.types.base.DFEVar;
 import com.maxeler.maxcompiler.v2.kernelcompiler.stdlib.KernelMath ;
 import com.maxeler.maxcompiler.v2.kernelcompiler.stdlib.core.CounterChain ;
 import com.maxeler.maxcompiler.v2.kernelcompiler.types.composite.DFEVector ;
 import com.maxeler.maxcompiler.v2.kernelcompiler.types.composite.DFEStruct;
 import com.maxeler.maxcompiler.v2.kernelcompiler.types.composite.DFEStructType;
 import com.maxeler.maxcompiler.v2.kernelcompiler.stdlib.memory.Memory;
 import java.util.*;
 """

#Adding class definition and class variables
kernel_maxj_code+="""class PRFStreamKernel extends Kernel {
 
    //static public final DFEType type = dfeInt(64);
    static public final DFEType type = dfeFloat(11,53);
    static public final DFEType prf_input_type = dfeUInt(64);
     static public DFEVectorType<DFEVar> interleavedFloatType = new DFEVectorType<DFEVar>( type, PRFConstants.p*PRFConstants.q ) ;
     static final    int p = PRFConstants.p;
     static final    int q = PRFConstants.q;
     static int MEMORY_ADDRESS_SIZE = PRFConstants.MEMORY_ADDRESS_SIZE; //log_2 of MEMORY_DEPTH;
 
     static final int loop_delay=43;
      public DFEStructType prf_inputs,prf_outputs;
"""

#Adding Kernel Modes 
#TODO if multiple compute allowed, add here respective modes 
kernel_maxj_code+="""     public enum PRFMode {
         LOAD, OFFLOAD, COMPUTE
     }

"""

#Adding Control Class 
kernel_maxj_code+="""     protected class Controls {
         private final DFEVar prfMode;
         private final DFEVar vectorSize;
         private final DFEVar isTrue, isFalse ;
         private final DFEVar iterationCounter;
         private final DFEVar copyRepeats;
         private final DFEVar scheduleSize;
         private final int lanes= PRFConstants.p*PRFConstants.q;
         Controls (Kernel kernel, DFEVar _prfMode, DFEVar _vectorSize, DFEVar _copyRepeats, DFEVar _scheduleSize){
             this.isTrue = kernel.constant.var( dfeUInt(1), 1 ) ;
             this.isFalse = kernel.constant.var( dfeUInt(1), 0 ) ;
 
             this.prfMode = _prfMode;
             this.vectorSize = _vectorSize;
             this.copyRepeats=_copyRepeats;
             this.scheduleSize=_scheduleSize;
 
             DFEVar total_iterations;
             DFEVar load_or_offload=((this.prfMode === PRFMode.LOAD.ordinal()) | (this.prfMode === PRFMode.OFFLOAD.ordinal()));
             total_iterations= load_or_offload ? (3*this.vectorSize)/this.lanes : kernel.constant.var(0);//constant var 0 is a place older for the computations case
             total_iterations = ~(prfMode === PRFMode.LOAD.ordinal() |prfMode === PRFMode.OFFLOAD.ordinal() ) ? this.copyRepeats*(this.vectorSize/this.lanes)+loop_delay: total_iterations;
                 this.iterationCounter= kernel.control.count.simpleCounter(64,total_iterations.cast(dfeUInt(64)));
         

"""


#Defining prf input and output in Control class
kernel_maxj_code+="""             prf_inputs = new DFEStructType(
                                     DFEStructType.sft("RowIndex",prf_input_type),
                                     DFEStructType.sft("ColumnIndex",prf_input_type),
                                     DFEStructType.sft("WriteEnable",dfeUInt(p*q)),
                                     DFEStructType.sft("AccType",prf_input_type),
                                     DFEStructType.sft("Mask",dfeUInt(p*q)),
"""
for i in range(0,len(read_access_mapping)):
    kernel_maxj_code+="""                                     DFEStructType.sft("index_i_read_0",prf_input_type),
                                     DFEStructType.sft("index_j_read_0",prf_input_type),
                                     DFEStructType.sft("acc_type_read_0",prf_input_type)""".replace("0",str(i))
    if i == (len(write_access_mapping)):
        kernel_maxj_code+="\n\n\t\t\t);"
    else:
        kernel_maxj_code+=",\n"

kernel_maxj_code+= """             prf_outputs = new DFEStructType(\n\n"""

for i in range(0,len(read_access_mapping)):
    kernel_maxj_code+="""                                     DFEStructType.sft("o_P_0",interleavedFloatType)""".replace("0",str(i))
    if i == (len(write_access_mapping)):
        kernel_maxj_code+="""\n\n\t\t\t);\n\t}
        """
    else:
        kernel_maxj_code+=",\n"

#Input and output port enable signal
kernel_maxj_code+="""         public DFEVar readingA(){
             DFEVar readingA_ifLoad = this.iterationCounter< (this.vectorSize/(p*q))? this.isTrue:this.isFalse;
             return ((this.prfMode === PRFMode.LOAD.ordinal()) ? readingA_ifLoad : this.isFalse);
         }
 
         public DFEVar readingB(){
             DFEVar readingB_ifLoad = 
                 (this.iterationCounter< 2*(this.vectorSize/(p*q)) & (~this.readingA()))
                 ? this.isTrue:this.isFalse;
             return ((this.prfMode === PRFMode.LOAD.ordinal())  ? readingB_ifLoad : this.isFalse);
         }
 
        public DFEVar readingC(){
             DFEVar readingC_ifLoad = 
                 ((~this.readingB()) & (~this.readingA()) & (this.iterationCounter< 3*(this.vectorSize/(p*q))))
                 ? this.isTrue:this.isFalse;
             return ((this.prfMode === PRFMode.LOAD.ordinal()) ? readingC_ifLoad : this.isFalse);
         }   
         public DFEVar outputA(){
             DFEVar outputA_ifOffload = this.iterationCounter< (this.vectorSize/(p*q))? this.isTrue:this.isFalse;
             DFEVar outputA_ifLoad = (this.iterationCounter > ((3 *this.vectorSize/(p*q)) - 3));
             DFEVar outputA_ifCompute = (this.iterationCounter > (this.copyRepeats*(this.vectorSize/(p*q)))+loop_delay-3);
             outputA_ifCompute =(this.scheduleSize>0)? (this.iterationCounter > (this.copyRepeats*((this.scheduleSize))+loop_delay)-3):outputA_ifCompute;
             DFEVar outputA_flag = outputA_ifLoad;
             outputA_flag = ((this.prfMode === PRFMode.OFFLOAD.ordinal()) ? outputA_ifOffload : outputA_flag);
             //outputA_flag = ((this.prfMode === PRFMode.COPY.ordinal()) ? outputA_ifCompute : outputA_flag);
             outputA_flag = (~(prfMode === PRFMode.LOAD.ordinal() |prfMode === PRFMode.OFFLOAD.ordinal() ) ? outputA_ifCompute : outputA_flag);
             return outputA_flag;
         }
 
        public DFEVar outputB(){
             DFEVar outputB_ifOffload = 
                 (this.iterationCounter< 2*(this.vectorSize/(p*q)) & (~this.outputA()))
                 ? this.isTrue:this.isFalse;
             DFEVar outputB_ifLoad = (this.iterationCounter > ((3 *this.vectorSize/(p*q)) - 3));
             DFEVar outputB_ifCompute = (this.iterationCounter > (this.copyRepeats*(this.vectorSize/(p*q)))+loop_delay-3);
             outputB_ifCompute =(this.scheduleSize>0)? (this.iterationCounter > (this.copyRepeats*((this.scheduleSize))+loop_delay)-3):outputB_ifCompute;
             DFEVar outputB_flag = outputB_ifLoad;
             outputB_flag = ((this.prfMode === PRFMode.OFFLOAD.ordinal()) ? outputB_ifOffload : outputB_flag);
             //outputB_flag = ((this.prfMode === PRFMode.COPY.ordinal()) ? outputB_ifCompute : outputB_flag);
            outputB_flag = (~(prfMode === PRFMode.LOAD.ordinal() |prfMode === PRFMode.OFFLOAD.ordinal() ) ? outputB_ifCompute : outputB_flag);
             return outputB_flag;
         }
 
        public DFEVar outputC(){
             DFEVar outputC_ifOffload = 
                 ((~this.outputB()) & (~this.outputA()))
                 ? this.isTrue:this.isFalse;
             DFEVar outputC_ifLoad = (this.iterationCounter > ((3 *this.vectorSize/(p*q)) - 3));
             DFEVar outputC_ifCompute = (this.iterationCounter > (this.copyRepeats*((this.vectorSize/(p*q)))+loop_delay)-3);
             outputC_ifCompute =(this.scheduleSize>0)? (this.iterationCounter > (this.copyRepeats*((this.scheduleSize))+loop_delay)-3):outputC_ifCompute;
             DFEVar outputC_flag = outputC_ifLoad;
             outputC_flag = ((this.prfMode === PRFMode.OFFLOAD.ordinal()) ? outputC_ifOffload : outputC_flag);
             //outputC_flag = ((this.prfMode === PRFMode.COPY.ordinal()) ? outputC_ifCompute: outputC_flag);
            outputC_flag = (~(prfMode === PRFMode.LOAD.ordinal() |prfMode === PRFMode.OFFLOAD.ordinal() ) ? outputC_ifCompute: outputC_flag);

             return outputC_flag;
         }
         """
kernel_maxj_code+="""         public DFEStruct getPRFInputs(Kernel kernel){
 
             List<DFEStruct> PRFInputs_list = new ArrayList<DFEStruct>();
             
             // Prepare the inputs for the loading mode
             DFEStruct PRFInputs_load = prf_inputs.newInstance(kernel);
             CounterChain load_offload_counter_chain = kernel.control.count.makeCounterChain( (this.prfMode === PRFMode.LOAD.ordinal()) | (this.prfMode === PRFMode.OFFLOAD.ordinal()) );
             DFEVar vector_id = load_offload_counter_chain.addCounter(3,1).cast(dfeUInt(64));
             DFEVar elementCounter = load_offload_counter_chain.addCounter(this.vectorSize/this.lanes,1);
             debug.simPrintf("vectorid: %d\\n",vector_id);
             DFEVar rowIndex_loadoffload=(elementCounter*this.lanes/PRFConstants.M)+(vector_id*170);
             DFEVar columnIndex_loadoffload=KernelMath.modulo(elementCounter*this.lanes,PRFConstants.M).cast(dfeUInt(64));
             DFEVar accType = kernel.constant.var(1).cast(dfeUInt(64));//ROW shape
             DFEVar writeEn =  kernel.constant.var(0xFFFFFFF).cast(dfeUInt(p*q));
             DFEVar zeroDfevar = kernel.constant.var(0).cast(dfeUInt(64));
             DFEVar writeDisable = kernel.constant.var(0).cast(dfeUInt(p*q));
             DFEVar oneDfevar = kernel.constant.var(1).cast(dfeUInt(64));
             DFEVar rowIndex_i_read_0 = kernel.constant.var(0);
             DFEVar rowIndex_j_read_0 = kernel.constant.var(0);
             DFEVar accType_read_0 = kernel.constant.var(1).cast(dfeUInt(64));
             DFEVar rowIndex_i_read_1 = kernel.constant.var(0);
             DFEVar rowIndex_j_read_1 = kernel.constant.var(0);
             DFEVar accType_read_1 = kernel.constant.var(1);
             
             // Load module write inputs
             PRFInputs_load["RowIndex"]<==rowIndex_loadoffload;
             PRFInputs_load["ColumnIndex"]<==columnIndex_loadoffload;
             PRFInputs_load["WriteEnable"]<==writeEn;
             PRFInputs_load["AccType"]<==accType;
             PRFInputs_load["Mask"]<==writeEn; //Set all mask bits to 1
             
             // Load module read dummy inputs
"""



for i in range(0,len(read_access_mapping)):
    kernel_maxj_code+="""
             PRFInputs_load["index_i_read_0"]<==zeroDfevar;
             PRFInputs_load["index_j_read_0"]<==zeroDfevar;
             PRFInputs_load["acc_type_read_0"]<==zeroDfevar;""".replace('0',str(i))
 
kernel_maxj_code+=""" 
             PRFInputs_list.add(PRFInputs_load);
 
             // Prepare the inputs for the offloading mode
             DFEStruct PRFInputs_offload = prf_inputs.newInstance(kernel);
 
             //Dummy write inputs
             PRFInputs_offload["RowIndex"]<==zeroDfevar;
             PRFInputs_offload["ColumnIndex"]<==zeroDfevar;
             PRFInputs_offload["WriteEnable"]<==writeDisable;
             PRFInputs_offload["AccType"]<==oneDfevar;
             PRFInputs_offload["Mask"]<==writeEn;
 
             // Useful read port 1 inputs
             PRFInputs_offload["index_i_read_0"]<==rowIndex_loadoffload;
             PRFInputs_offload["index_j_read_0"]<==columnIndex_loadoffload;
             PRFInputs_offload["acc_type_read_0"]<==oneDfevar;
"""

for i in range(1,len(read_access_mapping)):
 kernel_maxj_code+="""
         PRFInputs_offload["index_i_read_1"]<==zeroDfevar;
         PRFInputs_offload["index_j_read_1"]<==zeroDfevar;
         PRFInputs_offload["acc_type_read_1"]<==oneDfevar;
""".replace('1',str(i))
kernel_maxj_code+="""
         PRFInputs_list.add(PRFInputs_offload);
""" 

kernel_maxj_code+="""       
             //TODO Try to reduce the bitwidth of the mappedSchedule memory
             //The size of the mappedSchedule ROM is in the worst case scenario the number of memory accesses needed to read
             //all the content of PolyMem. PolyMem stores N*M elements, dividing this by the number of lanes gives the 
             //worst case scenario scheduleROM size.
             Memory<DFEVar> mappedSchedule= mem.alloc(dfeUInt(32), PRFConstants.M*PRFConstants.N/this.lanes);
             // The ScheduleROM is intialized on the CPU side.
             mappedSchedule.mapToCPU("ScheduleROM");
             // Each element in the mapped schedule is 32 bit split as follow 
             // <   4 MSB not used | accType (3 bits) | i (8 bits ) |j ( 9 bits ) |mask ( 8 bits )>
             
             CounterChain copy_counter_chain = kernel.control.count.makeCounterChain( (this.isTrue) );
             DFEVar copy_elementCounter = copy_counter_chain.addCounter(this.vectorSize/this.lanes,1);
             DFEVar schedule = mappedSchedule.read(copy_elementCounter.cast(dfeUInt(MEMORY_ADDRESS_SIZE)));
             //If schedule size is 0 default to processing the whole vector (previous STREAM implementaton ).
             DFEVar mask = (scheduleSize > 0)? schedule.slice(0,8).cast(dfeUInt(p*q)): writeEn;
             DFEVar j= schedule.slice(8,9).cast(dfeUInt(9)).cast(dfeUInt(64));
             DFEVar i= schedule.slice(17,8).cast(dfeUInt(8)).cast(dfeUInt(64));
             DFEVar accType_compute = (scheduleSize >0 ) ? schedule.slice(25,3).cast(dfeUInt(3)).cast(dfeUInt(64)) : oneDfevar;
             debug.simPrintf("schedule: %x,accType: %d, i : %d, j : %d , mask : %d\\n",schedule,accType_compute, i,j,mask);
             DFEVar rowIndex_copy_read= (scheduleSize > 0 )? i : (copy_elementCounter*this.lanes/PRFConstants.M);
             DFEVar columnIndex_copy_read=(scheduleSize>0) ? j : KernelMath.modulo(copy_elementCounter*this.lanes,PRFConstants.M).cast(dfeUInt(64));           
             //DFEVar rowIndex_copy_write= copy_elementCounter===0 ? zeroDfevar : stream.offset(rowIndex_copy_read,-1)+340;//added C vector offset
             //DFEVar columnIndex_copy_write= copy_elementCounter===0 ? zeroDfevar : stream.offset(columnIndex_copy_read,-1);
             //DFEVar writeEnable_copy = copy_elementCounter===0 ? zeroDfevar : kernel.constant.var(0xFFFFFFF).cast(dfeUInt(64));  
 
             DFEVar rowIndex_copy_write= stream.offset(rowIndex_copy_read,-loop_delay)+340;//added C vector offset
             DFEVar columnIndex_copy_write= stream.offset(columnIndex_copy_read,-loop_delay);
             DFEVar accType_copy = stream.offset(accType_compute,-loop_delay); 
             //DFEVar writeEnable_copy = kernel.constant.var(0xFFFFFFF).cast(dfeUInt(64));            
             DFEVar writeEnable_copy = stream.offset(mask,-loop_delay);            
 
"""
print str(vector_mapping)
print str(write_access_mapping)
# get write vector ID
vector_mapping[write_access_mapping[0][1]]
write_vector_id=vector_mapping[write_access_mapping[0][1]]
print "id write : "+str(vector_mapping[write_access_mapping[0][1]])

kernel_maxj_code+="""//Prepare prf inputs for Computation
            DFEStruct PRFInputs_compute = prf_inputs.newInstance(kernel);
            PRFInputs_compute["RowIndex"]<==stream.offset(rowIndex_copy_read,-loop_delay);//write in A
            PRFInputs_compute["ColumnIndex"]<==columnIndex_copy_write;
            PRFInputs_compute["WriteEnable"]<==(copy_elementCounter>=loop_delay)?mask:writeDisable;
            PRFInputs_compute["AccType"]<==accType_copy;
            PRFInputs_compute["Mask"]<==mask;

""".replace("rowIndex_copy_read","rowIndex_copy_read+"+str(write_vector_id)+"*170")
i=0
for read in read_access_mapping:
    read_vector_id=vector_mapping[read_access_mapping[i][1]]
    read_row_offset=read_access_mapping[i][2][0]
    read_column_offset=read_access_mapping[i][2][1]
    kernel_maxj_code+="""
            PRFInputs_compute["index_i_read_0"]<==rowIndex_copy_read;
            PRFInputs_compute["index_j_read_0"]<==columnIndex_copy_read;
            PRFInputs_compute["acc_type_read_0"]<==accType_compute;
""".replace("0",str(i)).replace("rowIndex_copy_read","rowIndex_copy_read+"+str(read_vector_id)+"*170+"+str(read_row_offset)).replace("columnIndex_copy_read","columnIndex_copy_read+"+str(read_column_offset))
    i+=1

kernel_maxj_code+="""
            PRFInputs_list.add(PRFInputs_compute); 
             //Select correct input based on prfmode
             DFEVar select = this.prfMode.cast(dfeUInt(2));
             DFEStruct PRFInputs=control.mux(select,PRFInputs_list);
 
             return PRFInputs;
        
         }
     }
"""

#input and output class
#TODO substitute the names of input and output streams with the one parsed from the c input
kernel_maxj_code+="""
    protected class Inputs {
         //Input stream containing the A, B and C vectors.
         private final DFEVector<DFEVar> aStream,bStream,cStream;
         private DFEVector<DFEVar> combinedStream;
 
         Inputs(Kernel kernel, Controls controls){
             this.aStream = kernel.io.input("aStream",interleavedFloatType,controls.readingA());
             this.bStream = kernel.io.input("bStream",interleavedFloatType,controls.readingB());
             this.cStream = kernel.io.input("cStream",interleavedFloatType,controls.readingC());
             this.combinedStream = this.aStream;
             this.combinedStream = (controls.readingB() )? this.bStream : this.combinedStream;
             this.combinedStream = (controls.readingC() )? this.cStream : this.combinedStream;
         }
     }
     protected class Outputs{
         private final DFEVector<DFEVar> outAStream, outBStream,outCStream;
         Outputs(Kernel kernel, Controls controls){
             this.outAStream = kernel.io.output("aOutStream",interleavedFloatType,controls.outputA());
             this.outBStream = kernel.io.output("bOutStream",interleavedFloatType,controls.outputB());
             this.outCStream = kernel.io.output("cOutStream",interleavedFloatType,controls.outputC());
         }
     }

"""

kernel_maxj_code+=maxj_compute

#Kernel 

kernel_maxj_code+="""

    protected PRFStreamKernel(KernelParameters parameters) {
        super(parameters);
        
         optimization.pushRoundingMode( RoundingMode.TRUNCATE ) ;
         //Scalar Input
         DFEVar vectorSize = io.scalarInput("vectorSize", dfeUInt(64));
         DFEVar prfMode = io.scalarInput("prfMode", type);
         DFEVar copyRepeats = io.scalarInput("copy_repeats", dfeUInt(64));
         DFEVar scheduleSize = io.scalarInput("scheduleROMsize", dfeUInt(64));

         Controls controls = new Controls( this, prfMode, vectorSize,copyRepeats, scheduleSize);
         Inputs inputs = new Inputs( this, controls);
         Outputs outputs = new Outputs(this,controls);
 
         
         DFEStruct PRFInputs = controls.getPRFInputs(this);
 
         DFEVector<DFEVar> prf_input_data = inputs.combinedStream;
         DFEVector<DFEVar> prf_input_data_loopback = interleavedFloatType.newInstance(this);
        prf_input_data = (prfMode === PRFMode.COMPUTE.ordinal() ) ? prf_input_data_loopback : prf_input_data;
        prf_input_data = (prfMode === PRFMode.LOAD.ordinal() |prfMode === PRFMode.OFFLOAD.ordinal()) ?prf_input_data: prf_input_data_loopback;
         //Debugging
          debug.simPrintf("tick %d input: %d %d %d | %d %d %d:",controls.iterationCounter, controls.readingA(),controls.readingB(),controls.readingC(), controls.outputA(), controls.outputB(),controls.outputC());
         for(int i =0;i<p*q;i++)
             debug.simPrintf("%f ",prf_input_data[i]);
         debug.simPrintf("\\n");
         debug.simPrintf("RowIndex: %d, ColumnIndex: %d, AccType:%d, WriteEnable: %d\\n",PRFInputs.get("RowIndex").cast(dfeInt(64)), PRFInputs.get("ColumnIndex").cast(dfeInt(64)), PRFInputs.get("AccType").cast(dfeInt(64)),PRFInputs.get("WriteEnable").cast(dfeInt(64)));
         debug.simPrintf("RowIndexRead0: %d, ColumnIndexRead0: %d, AccTypeRead0:%d\\n",PRFInputs.get("index_i_read_0").cast(dfeInt(64)), PRFInputs.get("index_j_read_0").cast(dfeInt(64)), PRFInputs.get("acc_type_read_0").cast(dfeInt(64)));
         debug.simPrintf("RowIndexRead1: %d, ColumnIndexRead1: %d, AccTypeRead1:%d\\n",PRFInputs.get("index_i_read_1").cast(dfeInt(64)), PRFInputs.get("index_j_read_1").cast(dfeInt(64)), PRFInputs.get("acc_type_read_1").cast(dfeInt(64)));
         //END Debugging
 
         Hashtable<String, DFEVector<DFEVar>> prfMultiportOut = Utils.polyMem_multiport(this,PRFInputs,prf_input_data);
"""
for i in range(0,len(read_access_mapping)):
    kernel_maxj_code+="""
        DFEVector<DFEVar> prfOutput0=prfMultiportOut.get("o_P_0");
        """.replace("0",str(i))

kernel_maxj_code+="DFEVector<DFEVar> output = compute("
for i in range(0,len(read_access_mapping)):
    kernel_maxj_code+="prfOutput0".replace("0",str(i))
    if i == len(read_access_mapping)-1:
        kernel_maxj_code+=");"
    else:
        kernel_maxj_code+=","

kernel_maxj_code+="prf_input_data_loopback <== stream.offset(output,-loop_delay);"

kernel_maxj_code+="""
 
         outputs.outAStream <==prfOutput0;
         outputs.outBStream <==prfOutput0;
         outputs.outCStream <==prfOutput0;
     }
 
     }
"""
with open("PRFStreamKernel.maxj","w") as f:
    f.write(kernel_maxj_code)
