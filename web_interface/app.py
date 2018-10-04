#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request,url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from shutil import copyfile, rmtree
import os
import io
from prf_utils import parseATrace, find_plot_dimension 
import json
import subprocess
import threading
import csv

#if this is set to true the performance prediction will show cached Results
#useful for speeding up test, set to false in production
debug_perf_prediction=False

def popenAndCall(socketio_,onExit,stdout_file, popenArgs, session_=[]):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    onExit when the subprocess completes.
    onExit is a callable object, and popenArgs is a list/tuple of args that 
    would give to subprocess.Popen.
    """
    def runInThread(socketio_,onExit, stdout_file, popenArgs,session_=[]):
        print " ===== thread args"+str(popenArgs)+"+++++++"
        if not debug_perf_prediction:
            proc = subprocess.Popen(*popenArgs, shell=True, bufsize=0, stdout=stdout_file)
            proc.wait()
        else: 
            socketio_.sleep(3)
        onExit(socketio_,session_)
        stdout_file.close()
        return
    #thread = threading.Thread(target=runInThread, args=(onExit,stdout_file , popenArgs))
    #thread.start()
    socketio.start_background_task(runInThread,*(socketio_,onExit,stdout_file,popenArgs,session_))
    # returns immediately after the thread starts
    return thread

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    #global thread
    #with thread_lock:
    #    if thread is None:
    #        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('load_projects', namespace='/test')
def load_project():
    dirs=[]
    contents=os.listdir('./projects')
    for c in contents:
        if os.path.isdir('./projects/'+c):
            dirs.append(c)
    emit('my_projects', { 'projects': dirs,'selected_project': session.get('selected_project','not set')})

def send_analysis_results(project_path):
    x=[]
    y=[]
    z=[]
    concurrentAccessList=parseATrace(project_path+'/current_input_no_includes.atrace')
    print "checking plot dimensions"
    dimensions = find_plot_dimension(concurrentAccessList)

    with open(project_path+'/current_input_no_includes.vec_info') as f:
        vec_access_info = json.load(f)       
   
    accesses_rw=[]
    for acc in vec_access_info[1]:
        accesses_rw.append(acc)
    for acc in vec_access_info[2]:
        accesses_rw.append(acc)

    
    # The conversion to set makes the for loop way faster 
    concurrentAccessSet=set(concurrentAccessList[0])
    print "generating heatmap data to plot"
    for i in range(0,dimensions[0]):
        for j in range(0,dimensions[1]):
            x.append(i);
            y.append(j);
            if (i,j) in concurrentAccessSet:
                z.append(1);
            else:
                z.append(0);
    
    traces=[]
    for acc in accesses_rw:
        name=acc[3][0]+"["+acc[3][1]+"]["+acc[3][2]+"]"
        z_1=[0 for i in range(0,dimensions[0]*dimensions[1])]
        for i in range(0,dimensions[0]):
            for j in range(0,dimensions[1]):
                if z[i*dimensions[1]+j] == 1  :
                    if (i+int(acc[2][0])< dimensions[0]) and (j+int(acc[2][1])<dimensions[1]) and (i+int(acc[2][0])>=0 )and (j+int(acc[2][1])>=0):
                        z_1[(i+int(acc[2][0]))*dimensions[1]+(j+int(acc[2][1]))]=1
        traces.append((name,z_1))

    with open(project_path+'/parser_out','r') as f:
        parser_out = f.read()

    with open(project_path+'/current_input_no_includes.loop_info') as f:
        loop_info = json.load(f) 



    with open(project_path+'/current_input_no_includes.vec_size_info') as f:
        vec_size_info = json.load(f)       
    
    heatmaps=[]
    for trace in traces:
        data={'x': y, 'y':x,'z':trace[1],
                'showscale' :False,'type':'heatmap','xgap':1,'ygap':1,
                'colorscale': [
                    [0, 'rgb(0, 0, 0)'],
                    [1, 'rgb(255, 255, 255)']],
                'colorbar': {
                    'tick0':0,
                    'dtick':1,
                    'tickvals':[0,1],
                    'ticktext':['Not accessed','Accessed']
                    }}
        heatmaps.append((trace[0],data))

    print "emitting data"
    emit('analysis_output',
            {'parser_out': parser_out, 
                'data':{'x': y, 'y':x,'z':z,
                'showscale' :False,'type':'heatmap','xgap':1,'ygap':1,
                'colorscale': [
                    [0, 'rgb(0, 0, 0)'],
                    [1, 'rgb(255, 255, 255)']],
                'colorbar': {
                    'tick0':0,
                    'dtick':1,
                    'tickvals':[0,1],
                    'ticktext':['Not accessed','Accessed']
                    }},
                'plots':heatmaps,
                'loop_info':loop_info,
                'vec_access_info':vec_access_info,
                'vec_size_info': vec_size_info
            })

def send_performance_results( project_path ):    
    with open(project_path+"/schedule_analysis_out") as f:
        schedule_analysis_out = f.read()
    with open(project_path+"/current_input_no_includes_noschedule_col.analysis") as f:
        schedule_analysis = f.read()
        schedule_analysis_row = schedule_analysis.splitlines()
        schedule_analysis_row_cols = []
        for row in schedule_analysis_row:
            schedule_analysis_row_cols.append(row.split(','))
        i=0
        print schedule_analysis_row_cols
        reader = csv.reader(f,delimiter=',')
        print " printing reader"
        for row in reader:
            print row[0]
        sortedlist =[schedule_analysis_row_cols[0]] + sorted(schedule_analysis_row_cols[1:], key=lambda row: float(row[8]), reverse=True)
        print "sorted_list"
        print sortedlist
        sorted_list_rows=[]
        for row in sortedlist:
            sorted_list_rows.append(','.join(row))
        csv_sorted_list='\n'.join(sorted_list_rows)
        print csv_sorted_list
    with open(project_path+"/c_source_benchmark_output.csv") as f:
        reader = csv.reader(f)
        first_row=True
        for r in reader:
            if first_row:
                first_row=False
                continue
            else:
                init_runtime=float(r[3])
                final_runtime=float(r[7])
                kernel_runtime=float(r[11])
                break
    #Extract throughput extimation
    throughputs=[]
    first_row=True
    elements_accessed=[]
    with open(project_path+"/current_input_no_includes.analysis") as f:
        reader = csv.reader(f)
        for r in reader:
            if first_row:
                first_row=False
            else:
                throughputs.append(float(r[8]))
                elements_accessed.append(int(r[4]))
    extimation=max(throughputs[1:])*10**3
    elements=elements_accessed[0]
    # 3 takes into account 2 reads and 1 write
    # 8 takes into account elements with datatype *double* (64bits)
    print "elements"+str(elements)
    processed_Mbytes=3*float(elements)*8/(10**6)
    time_extimation_microsecond=(processed_Mbytes/extimation)*10**6
    c_source_benchmark={'init':init_runtime*10**6,'final':final_runtime*10**6,'kernel':kernel_runtime*10**6}
    emit('gen_schedule_analysis_done',{'data': schedule_analysis_out,'analysis':csv_sorted_list,'c_source_benchmark':c_source_benchmark,'dfe_extimation':{'throughput_extimation':extimation,'processed_Mbytes':processed_Mbytes,'time_extimation_microsecond':time_extimation_microsecond}})

def send_design_generation_results(project_path):
    with open(project_path+"/PolyMemStream_out_no_synth/CPUCode/PRFStreamCpuCode.c",'r') as f:
        generated_host_c=f.read()

    abs_path_to_project_zip=project_path+"/PolyMemStream_out_no_synth.zip"
    project_zip_url=url_for('static',
                            filename=abs_path_to_project_zip)
    emit('generate_design_done',{'generated_host_c': generated_host_c,'project_no_sinth_zip':project_zip_url})

@socketio.on('send_sim_data', namespace='/test')
def send_sim_data( project_path="" ):
    print "Called send_sim_data"
    if project_path=="":
        project=session.get('selected_project','not set')
        project_path="projects/"+project 
    print project_path
    num_diff_lines=sum(1 for line in open(project_path+"/c_source_vs_dfe_host_dump.diff"))
    c_source_dump_path=project_path+"/c_source_vec.dump"
    c_source_dump_url=url_for('static',
                            filename=c_source_dump_path)
    dfe_host_dump_path=project_path+"/dfe_host_vec.dump"
    dfe_host_dump_url=url_for('static',
                            filename=dfe_host_dump_path)
    diff_dump_path=project_path+"/c_source_vs_dfe_host_dump.diff"
    diff_dump_url=url_for('static',
                            filename=diff_dump_path)
    print "emitting"
    emit('sim_verification',{'validation_result':num_diff_lines,'c_source_dump':c_source_dump_url,'dfe_host_dump':dfe_host_dump_url,'c_source_vs_dfe_host_dump':diff_dump_url});

@socketio.on('send_synthesis_results', namespace='/test')
def send_synthesis_results(project_path=""):
    print "Called send_synthesis_results"
    if project_path=="":
        project=session.get('selected_project','not set')
        project_path="projects/"+project 
    build_log=project_path+"/PolyMemStream_out_synth/RunRules/DFE/maxfiles/PRFStream_VECTIS_DFE/_build.log"
    project_zip=project_path+"/PolyMemStream_out_synth.zip"
    build_log_url=url_for('static',
                            filename=build_log)
    project_zip_url=url_for('static',
                            filename=project_zip)
    #TODO send resource usage in csv format.
    # Extract the time taken for the synthesis and send to client 

    synthesis_outcome='Fail'
    final_resource_usage=False
    time=""
    resources=[]
    frequency=""
    with open(project_path+"/current_input_no_includes.cfg") as f:
        for line in f:
            if line.find("FREQUENCY")!=-1:
                frequency=line.split('"')[1]
    with open(build_log) as f:
        for line in f:
            if line.find("met timing with score 0 (best score 0)") != -1:
                synthesis_outcome='Success'
            if line.find("FINAL RESOURCE USAGE") != -1:
                final_resource_usage=True 
            if final_resource_usage and line.find("FINAL RESOURCE USAGE") == -1:
                logic_utilization=line
                print line
                resource={}
                resource_type = line.split(':')[3].strip()
                resource["type"]=resource_type
                usage_general=line.split(':')[4].strip()
                used_items=usage_general.split('/')[0].strip()
                resource["used"]=used_items
                rest=usage_general.split('/')[1].strip()
                total_items=rest.split('(')[0].strip()
                resource["total"]=total_items
                rest_1=rest.split('(')[1].strip()
                percentage=rest_1.split('%')[0].strip()
                resource["percentage"]=percentage
                print resource 
                resources.append(resource)

            if final_resource_usage and line.find("Block memory") != -1:
                final_resource_usage=False
            if line.find("PROGRESS: Build completed") != -1:
                time=line
                time=time.split('(')[1].split(')')[0]
                time=time.replace('took ','')
    
    resources_csv="Resource,Used,Total,Use Percentage (%) \n"
    for res in resources:
        resources_csv+=res["type"]+","+res["used"]+","+res["total"]+","+res["percentage"]+"\n"
    print resources_csv

    print time

    print "emitting results"
    emit('synthesis_results',{'result': 'Success','resource_usage':resources_csv,'build_log':build_log_url,'project_zip':project_zip_url,'time_taken':time,'frequency':frequency})   

@socketio.on('send_benchmark_results', namespace='/test')
def send_benchmark_results(project_path=""):
    print "Called send_benchmark_results"
    if project_path=="":
        project=session.get('selected_project','not set')
        project_path="projects/"+project 
    benchmark_csv=project_path+"/benchmark_output.csv"
    benchmark_cpu_csv=project_path+"/c_source_benchmark_output.csv"
    benchmark_csv_url=url_for('static',
                            filename=benchmark_csv)
    benchmark_cpu_csv_url=url_for('static',
                            filename=benchmark_cpu_csv)

    benchmark_stdout=project_path+"/benchmark.out"
    benchmark_stdout_url=url_for('static',
                            filename=benchmark_stdout)
    #Extract throughput extimation
    throughputs=[]
    first_row=True
    with open(project_path+"/current_input_no_includes.analysis") as f:
        reader = csv.reader(f)
        for r in reader:
            if first_row:
                first_row=False
            else:
                throughputs.append(float(r[8]))
    extimation=max(throughputs[1:])
    first_row=True
    y_cpu=[]
    with open(benchmark_csv) as f:
        reader = csv.reader(f)
        x=[]
        y=[]
        y_ref=[]
        for r in reader:
            if first_row:
                #x.append(r[13])
                #y.append(r[14])
                #y_ref.append('Extimated GB/s')
                first_row=False
            else:
                x.append(float(r[13]))
                y.append(float(r[14]))
                y_ref.append(extimation)
    first_row=True
    with open(benchmark_cpu_csv) as f:
        reader = csv.reader(f)
        for r in reader:
            if first_row:
                #x.append(r[13])
                #y.append(r[14])
                #y_ref.append('Extimated GB/s')
                first_row=False
            else:
                y_cpu.append(float(r[14]))

    emit('benchmark_results',{'benchmark_data': benchmark_csv_url,'cpu_benchmark_data':benchmark_cpu_csv_url,'benchmark_plot_data':{'x':x,'y':y,'mode':'markers','type':'skatter','name':'Measured','marker': { 'size': 10 }},'benchmark_plot_extimation':{'x':x,'y':y_ref,'mode':'lines','type':'skatter','name':'Extimated'},'benchmark_cpu_plot_data':{'x':x,'y':y_cpu,'mode':'markers','type':'skatter','name':'Measured CPU','marker': { 'size': 10 }},'benchmark_stdout':benchmark_stdout_url})   

#ordered list of phases
phase_list = ['analysis','performance_prediction','design_generation',"simulation","synthesis","benchmark"]
#for each phase a tuple containing the list of required files and function to call to update
#the respective client "card"
phases_data={'analysis':(['/current_input_no_includes.atrace',
                   '/current_input_no_includes.loop_info',
                   '/current_input_no_includes.vec_info',
                   '/current_input_no_includes.vec_size_info'
                    ],send_analysis_results),
             'performance_prediction':(["/current_input_no_includes_noschedule_col.analysis",
                    "/c_source_benchmark_output.csv",
                    "/schedule_analysis_out"],
                      send_performance_results),
             'design_generation':(["/PolyMemStream_out_no_synth/CPUCode/PRFStreamCpuCode.c",
                "/PolyMemStream_out_no_synth",
                "/PolyMemStream_out_no_synth.zip"],
                send_design_generation_results),
             'simulation':(["/c_source_vs_dfe_host_dump.diff",
                 "/c_source_vec.dump",
                 "/dfe_host_vec.dump",
                 "/current_input_dump_instr.c",
                 "/current_input_dump_instr",
                 "/PolyMemStream_out_no_synth_verify_sim"],
                send_sim_data),
             'synthesis':(["/PolyMemStream_out_synth/RunRules/DFE/maxfiles/PRFStream_VECTIS_DFE/_build.log",
                 "/PolyMemStream_out_synth/RunRules/DFE/binaries/PRFStream",
                 "/PolyMemStream_out_synth"],send_synthesis_results),
             'benchmark':(["/benchmark_output.csv","/benchmark.out","/PolyMemStream_out_synth_benchmark"],send_benchmark_results)
            }

def remove_stale_data( project_path, upgraded_card ):
    remove_current=False
    for phase in phase_list:
        if phase == upgraded_card:
            remove_current=True  
        if remove_current:
            print "flushing "+phase
            for to_remove in phases_data[phase][0]:
                if os.path.isfile(project_path+to_remove):
                    os.remove(project_path+to_remove) 
                if os.path.isdir(project_path+to_remove):
                    rmtree(project_path+to_remove)
            emit('flush_card',{'card':phase})
   

@socketio.on('select_project', namespace='/test')
def select_project(message):
    with open("projects/"+message['project']+"/current_input.c") as f: 
        s = f.read() 
    session['selected_project']=message['project']
    emit('selected_project',
            {'selected_project': session.get('selected_project','not set'),'code':s})
    #check if analysis data are available
    project_path="projects/"+message['project']
    for phase in phase_list:
        print "Checking if data for "+phase+" are available"
        for required_file in phases_data[phase][0]:
            if not os.path.exists(project_path+required_file):
                print required_file+" is NOT available, not loading "+phase
                return
            print required_file+" is available"
        print "Data available,sending data over"
        phases_data[phase][1](project_path)
            
@socketio.on('delete_project', namespace='/test')
def delete_project(message):
    print "Called delete_project with arg "+message['project_name']
    project_name=message['project_name']
    if os.path.exists("projects/"+project_name) and not project_name=="":
        rmtree("projects/"+project_name)
    session['selected_project']=""
    load_project() 

@socketio.on('create_project', namespace='/test')
def create_project(message):
    project_name=message['project_name']
    session['selected_project']=project_name
    if not os.path.exists("projects/"+project_name):
        os.makedirs("projects/"+project_name)
        copyfile("../current_input.c","projects/"+project_name+"/current_input.c")
        emit('created_project',{'error':'none'});
        with open("projects/"+project_name+"/current_input.c") as f: 
            s = f.read()
        emit('selected_project',
            {'selected_project': session.get('selected_project','not set'),'code':s})
    else:
        emit('created_project',{'error':'A project named '+project_name+' already_exists'});
    

def perf_prediction_done(socketio_,session_):
    print "++++++ Performance prediction over ++++++"

    socketio_.emit('done_performance_prediction',{'threads': 4},
                      namespace='/test')

@socketio.on('gen_schedule_analysis', namespace='/test')
def gen_schedule_analysis():
    print "generating schedule analysis"
    project=session.get('selected_project','not set')
    project_path="projects/"+project
    os.system("cd "+project_path+"; ../../../performance_prediction/generate_analysis_webapp.sh  current_input_no_includes > schedule_analysis_out")
    os.system("cd "+project_path+";python ../../../performance_prediction/generate_benchmark_source.py current_input_no_includes.c current_input_no_includes.atrace > source_benchmark_generation_out")
    os.system("cd "+project_path+";gcc -o c_source_benchmark -std=c99 c_source_benchmark.c")
    if os.path.isfile(project_path+"/c_source_benchmark"):
        os.system("cd "+project_path+";./c_source_benchmark > benchmark_out")
    else:
        print "ERROR: problem during generation/compilation of the c source benchmark"
        

    
    with open(project_path+"/current_input_no_includes.analysis","rb") as f:
        reader = csv.reader(f)
       #Update schedule file column
        with open(project_path+"/current_input_no_includes_noschedule_col.analysis","wb") as result:
            writer = csv.writer(result)
            first_row=True
            for r in reader:

                if first_row:
                    writer.writerow( ( r[0], r[1], r[2], r[3], r[4],r[5],r[6],r[7],
                        r[8], r[9], r[10]) )
                    first_row=False
                else:
                    schedule_file = r[10].split('/')[-1]
                    abs_path_to_schedule_file=project_path+"/"+schedule_file
                    url_to_schedule_file="<a href="+url_for('static',
                            filename=abs_path_to_schedule_file) +">"+"get schedule</a>"
                    writer.writerow( ( r[0], r[1], r[2], r[3], r[4],r[5],r[6],r[7],
                        r[8],r[9], url_to_schedule_file) )

    send_performance_results( project_path )
 
@socketio.on('performance_prediction', namespace='/test')
def performance_prediction(message):
    print "called performance_prediction"
    project=session.get('selected_project','not set')
    project_path="projects/"+project
    remove_stale_data( project_path, 'performance_prediction')
    outfile = open(project_path+'/scheduler_out', 'w');

    popenAndCall(socketio,perf_prediction_done,outfile, ["cd "+project_path+"; python ../../../performance_prediction/schedule_atrace.py current_input_no_includes.atrace ReRo 2 4"])
    popenAndCall(socketio,perf_prediction_done,outfile, ["cd "+project_path+"; python ../../../performance_prediction/schedule_atrace.py current_input_no_includes.atrace ReCo 2 4"])
    popenAndCall(socketio,perf_prediction_done,outfile, ["cd "+project_path+"; python ../../../performance_prediction/schedule_atrace.py current_input_no_includes.atrace RoCo 2 4"])
    popenAndCall(socketio,perf_prediction_done,outfile, ["cd "+project_path+"; python ../../../performance_prediction/schedule_atrace.py current_input_no_includes.atrace ReTr 2 4"])

    emit('started_performance_prediction',{'threads': 4})



@socketio.on('analyze_code', namespace='/test')
def analyze_code(message):
    print "called analyze_code"
    
    code=message['source']
    project=session.get('selected_project','not set')
    print "currently selected project "+project
    project_path="projects/"+project
    source_filename=project_path+'/current_input.c'
    source_filename_no_includes=project_path+'/current_input_no_includes.c'

    remove_stale_data( project_path, 'analysis' )
    with open(source_filename,"w") as f:
        f.write(code)

    if os.path.exists(source_filename_no_includes):
        os.remove(source_filename_no_includes)

    with open(source_filename_no_includes,'a') as f:
        for line in code.splitlines():
           if not line.startswith('#include'):
               f.write(line) 
               f.write('\n') 
    
    print "starting parser"
    os.system("cd "+project_path+
            "; python ../../../input_code/parser_2.py  current_input_no_includes.c > parser_out")
    with open(project_path+'/parser_out','r') as f:
        parser_out = f.read()
    print "parser_done"
    send_analysis_results(project_path)

  
@socketio.on('generate_design', namespace='/test')
def generate_design():
    project=session.get('selected_project','not set')
    project_path="projects/"+project
    remove_stale_data( project_path, 'design_generation')
    #generate current_input_no_includes.cfg
    os.system("cd "+project_path+
            ";../../../generated_hardware_design/generate_cfg_webapp.sh current_input_no_includes.analysis")
    os.system("cd "+project_path+
            ";cp ../../../generated_hardware_design/PolyMemStream_ref.zip .;unzip -o PolyMemStream_ref.zip;cp -r ./PolyMemStream_ref/ ./PolyMemStream_out;")
    os.system("cd "+project_path+
            ";../../../generated_hardware_design/generate_prf_constants_webapp.sh current_input_no_includes.cfg")
    os.system("cd "+project_path+
            ";python ../../../generated_hardware_design/generate_kernel.py current_input_no_includes;mv PRFStreamKernel.maxj PolyMemStream_out/EngineCode/src/prfstream/")

    os.system("cd "+project_path+
            ";python ../../../generated_hardware_design/generate_host_code.py current_input_no_includes.c current_input_no_includes.cfg current_input_no_includes.vec_info;mv PRFStreamCpuCode.c PolyMemStream_out/CPUCode")
    os.system("cd "+project_path+
            ";mv PolyMemStream_out PolyMemStream_out_no_synth; zip -r PolyMemStream_out_no_synth.zip PolyMemStream_out_no_synth")

    os.system("cd "+project_path+
            ";rm -rf PolyMemStream_ref;rm PolyMemStream_ref.zip")
    send_design_generation_results(project_path)
    



def simulation_done(socketio_,project_path):
    print "Called simulation done"
    print "Current session project path: "+project_path
    if not os.path.isfile(project_path+"/dfe_host_vec.dump"):
        os.system("cd "+project_path+";mv ./PolyMemStream_out_no_synth_verify_sim/CPUCode/dfe_host_vec.dump .");
    if not os.path.isfile(project_path+"/c_source_vs_dfe_host_dump.diff"):
        os.system("cd "+project_path+";diff c_source_vec.dump dfe_host_vec.dump > c_source_vs_dfe_host_dump.diff")
    socketio_.emit('sim_verification_done',namespace='/test');

@socketio.on('simulate_design', namespace='/test')
def simulate_design():
    print "called simulate design"
    project=session.get('selected_project','not set')
    project_path="projects/"+project 
    remove_stale_data( project_path, 'simulation')
    print "running code instrumenter"
    os.system("cd "+project_path+
            ";python ../../../simulate_design/instrument_original_c_source.py current_input.c ./PolyMemStream_out_no_synth/CPUCode/PRFStreamCpuCode.c current_input_no_includes.vec_info current_input_no_includes.vec_size_info;")
    if os.path.isfile(project_path+"/current_input_dump_instr.c") and os.path.isfile(project_path+"/PRFStreamCpuCode_dump_instr.c"):
        print "code instrumenter generated source correctly"
    print "cloning maxeler project to _verify_sim"
    os.system("cd "+project_path+";cp -r  PolyMemStream_out_no_synth PolyMemStream_out_no_synth_verify_sim;")

    print "compiling c source code"
    os.system("cd "+project_path+";gcc -std=c99 current_input_dump_instr.c -o current_input_dump_instr;./current_input_dump_instr > out;")
    if os.path.isfile(project_path+"/current_input_dump_instr"):
        print "Executable successfully generated"
    else:
        print "Problems during executable compilation"
    if os.path.isfile(project_path+"/c_source_vec.dump"):
        print "Original dump successfully generated"
    else:
        print "Problems during the generation of the dump"
    outfile = open(project_path+'/max_sim_ver.out', 'w');
    popenAndCall(socketio,simulation_done,outfile, ["cd "+project_path+"; mv PRFStreamCpuCode_dump_instr.c ./PolyMemStream_out_no_synth_verify_sim/CPUCode/PRFStreamCpuCode.c; cd ./PolyMemStream_out_no_synth_verify_sim/CPUCode;make RUNRULE=Simulation runsim "],project_path)
    emit("starting_simulation")

    



def synthesis_done(socketio_,project_path):
    print "+++++ Synthesis DONE"
    socketio_.emit('done_synthesis',namespace='/test')
    
@socketio.on('synthesize_design',namespace='/test')
def synthesize_design():
    print "Called synthesize design"
    project=session.get('selected_project','not set')
    project_path="projects/"+project 
    remove_stale_data( project_path, 'synthesis')
    print "Generating compilation folder"
    outfile = open(project_path+'/max_synth.out', 'w');
    os.system("cd "+project_path+
            ";cp -r PolyMemStream_out_no_synth PolyMemStream_out_synth;");
    popenAndCall(socketio,synthesis_done,outfile, ["cd "+project_path+"; cd ./PolyMemStream_out_synth/CPUCode;make RUNRULE=DFE build;cd ../..;zip -r PolyMemStream_out_synth.zip PolyMemStream_out_synth"],project_path)
    print "Started to build"

def benchmark_done(socketio_,project_path):
    print "+++++ Benchmark DONE"
    socketio_.emit('done_benchmark',namespace='/test')

@socketio.on('benchmark_design',namespace='/test')
def benckmark_design():
    print "Called benkmark design"
    project=session.get('selected_project','not set')
    project_path="projects/"+project 
    remove_stale_data( project_path, 'benchmark')
    print "Generating benckmark folder"
    if os.path.isdir(project_path+"/PolyMemStream_out_synth_benchmark"):
        print "Removing old benchmark directory"
        os.system("cd "+project_path+";rm -rf PolyMemStream_out_synth_benchmark")
    os.system("cd "+project_path+
            ";cp -r PolyMemStream_out_synth PolyMemStream_out_synth_benchmark;")
    print "Generating benckmark DFE host source"
    os.system("cd "+project_path+
            ";python ../../../benchmark_hardware_design/generate_host_code.py PolyMemStream_out_synth_benchmark/CPUCode/PRFStreamCpuCode.c current_input_no_includes.atrace;mv PRFStreamCpuCode_benchmark.c PolyMemStream_out_synth_benchmark/CPUCode; mv PolyMemStream_out_synth_benchmark/CPUCode/PRFStreamCpuCode.c PolyMemStream_out_synth_benchmark/CPUCode/PRFStreamCpuCode_orig.c;mv PolyMemStream_out_synth_benchmark/CPUCode/PRFStreamCpuCode_benchmark.c PolyMemStream_out_synth_benchmark/CPUCode/PRFStreamCpuCode.c")
    print "Compiling benchmark"
    os.system("cd "+project_path+"/PolyMemStream_out_synth_benchmark/CPUCode;"+
            "make RUNRULE=DFE build")
    print "Running benchmark"
    outfile = open(project_path+'/benchmark_script.out', 'w');
    popenAndCall(socketio,benchmark_done,outfile, ["cd "+project_path+";../../../benchmark_hardware_design/run_benchmark.sh" ],project_path)




@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True,host='0.0.0.0')
