#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import os
from prf_utils import parseATrace, find_plot_dimension 

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
    emit('my_projects', { 'projects': dirs})


@socketio.on('select_project', namespace='/test')
def select_project(message):
    with open("projects/"+message['project']+"/current_input.c") as f: 
        s = f.read() 
    session['selected_project']=message['project']
    emit('selected_project',
            {'selected_project': session.get('selected_project','not set'),'code':s})


@socketio.on('analyze_code', namespace='/test')
def analyze_code(message):
    print "called analyze_code"
    code=message['source']
    project=session.get('selected_project','not set')
    print "currently selected project "+project
    project_path="projects/"+project
    source_filename=project_path+'/current_input.c'
    source_filename_no_includes=project_path+'/current_input_no_includes.c'

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

    os.remove(project_path+'/parser_out')
    x=[]
    y=[]
    z=[]
    print "parsing atrace"
    concurrentAccessList=parseATrace(project_path+'/current_input_no_includes.atrace')
    print "checking plot dimensions"
    dimensions = find_plot_dimension(concurrentAccessList)
    #TODO create data structure with x y z of the heatmap to send back to the Client
    # The client will display the heatmap using the info at this page
    # https://plot.ly/javascript/heatmaps/
    # The library is already loaded
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

    
    print "emitting data"
    emit('analysis_output',
            {'parser_out': parser_out, 
                'data':{'x': x, 'y':y,'z':z,
                'showscale' :True,'type':'heatmap','xgap':1,'ygap':1,
                'colorscale': [
                    [0, 'rgb(0, 0, 0)'],
                    [1, 'rgb(255, 255, 255)']],
                'colorbar': {
                    'tick0':0,
                    'dtick':1,
                    'tickvals':[0,1],
                    'ticktext':['Not accessed','Accessed']
                    }}
            })
  

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
