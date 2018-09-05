#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request,url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from shutil import copyfile, rmtree
import os
from prf_utils import parseATrace, find_plot_dimension 
import json
import subprocess
import threading
import csv

#if this is set to true the performance prediction will show cached Results
#useful for speeding up test, set to false in production
debug_perf_prediction=False

def popenAndCall(socketio_,onExit,stdout_file, popenArgs):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    onExit when the subprocess completes.
    onExit is a callable object, and popenArgs is a list/tuple of args that 
    would give to subprocess.Popen.
    """
    def runInThread(socketio_,onExit, stdout_file, popenArgs):
        print " ===== thread args"+str(popenArgs)+"+++++++"
        if not debug_perf_prediction:
            proc = subprocess.Popen(*popenArgs, shell=True, bufsize=0, stdout=stdout_file)
            proc.wait()
        else: 
            socketio_.sleep(3)
        onExit(socketio_)
        stdout_file.close()
        return
    #thread = threading.Thread(target=runInThread, args=(onExit,stdout_file , popenArgs))
    #thread.start()
    socketio.start_background_task(runInThread,*(socketio_,onExit,stdout_file,popenArgs))
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
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('load_projects', namespace='/test')
def load_project():
    dirs=os.listdir('./projects')
    emit('my_projects', { 'projects': dirs,'selected_project': session.get('selected_project','not set')})

def send_analysis_results(project_path):
    x=[]
    y=[]
    z=[]
    concurrentAccessList=parseATrace(project_path+'/current_input_no_includes.atrace')
    print "checking plot dimensions"
    dimensions = find_plot_dimension(concurrentAccessList)
    
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

    with open(project_path+'/parser_out','r') as f:
        parser_out = f.read()

    with open(project_path+'/current_input_no_includes.loop_info') as f:
        loop_info = json.load(f) 

    with open(project_path+'/current_input_no_includes.vec_info') as f:
        vec_access_info = json.load(f)    

    with open(project_path+'/current_input_no_includes.vec_size_info') as f:
        vec_size_info = json.load(f)       
    
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
                'loop_info':loop_info,
                'vec_access_info':vec_access_info,
                'vec_size_info': vec_size_info
            })

def send_performance_results( project_path ):    
    with open(project_path+"/schedule_analysis_out") as f:
        schedule_analysis_out = f.read()
    with open(project_path+"/current_input_no_includes_noschedule_col.analysis") as f:
    #with open(project_path+"/current_input_no_includes.analysis") as f:
        schedule_analysis = f.read()
    emit('gen_schedule_analysis_done',{'data': schedule_analysis_out,'analysis':schedule_analysis})

def send_design_generation_results(project_path):
    with open(project_path+"/PolyMemStream_out_no_synth/CPUCode/PRFStreamCpuCode.c",'r') as f:
        generated_host_c=f.read()

    abs_path_to_project_zip=project_path+"/PolyMemStream_out_no_synth.zip"
    project_zip_url=url_for('static',
                            filename=abs_path_to_project_zip)
    emit('generate_design_done',{'generated_host_c': generated_host_c,'project_no_sinth_zip':project_zip_url})

#ordered list of phases
phase_list = ['analysis','performance_pred','design_generation']
#for each phase a tuple containing the list of required files and function to call to update
#the respective client "card"
phases_data={'analysis':(['/current_input_no_includes.atrace',
                   '/current_input_no_includes.loop_info',
                   '/current_input_no_includes.vec_info',
                   '/current_input_no_includes.vec_size_info'
                    ],send_analysis_results),
             'performance_pred':(["/current_input_no_includes_noschedule_col.analysis",
                    "/schedule_analysis_out"],
                      send_performance_results),
             'design_generation':(["/PolyMemStream_out_no_synth/CPUCode/PRFStreamCpuCode.c",
                "/PolyMemStream_out_no_synth.zip"],
                send_design_generation_results)
            }

def remove_stale_data( project_path, upgraded_card ):
    remove_current=False
    for phase in phase_list:
        if phase == upgraded_card:
            remove_current=True  
        if remove_current:
            for file_to_remove in phases_data[phase][0]:
                if os.path.exists(project_path+file_to_remove):
                    os.remove(project_path+file_to_remove) 
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
            if not os.path.isfile(project_path+required_file):
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
    

def perf_prediction_done(socketio_):
    print "++++++ Performance prediction over ++++++"

    socketio_.emit('done_performance_prediction',{'threads': 4},
                      namespace='/test')

@socketio.on('gen_schedule_analysis', namespace='/test')
def gen_schedule_analysis():
    print "generating schedule analysis"
    project=session.get('selected_project','not set')
    project_path="projects/"+project
    os.system("cd "+project_path+"; ../../../performance_prediction/generate_analysis_webapp.sh  current_input_no_includes > schedule_analysis_out")

    
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
    remove_stale_data( project_path, 'performance_pred')
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
    
    



@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True,host='0.0.0.0')
