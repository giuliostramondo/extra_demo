function escapeHTML( string )
{
    var pre = document.createElement('pre');
    var text = document.createTextNode( string );
    pre.appendChild(text);
    return pre.innerHTML;
}

function init_socketio() {
            // Use a "/test" namespace.
            // An application can open a connection on multiple namespaces, and
            // Socket.IO will multiplex all those connections on a single
            // physical channel. If you don't care about multiple channels, you
            // can set the namespace to an empty string.
            namespace = '/test';

            // Connect to the Socket.IO server.
            // The connection URL has the following format:
            //     http[s]://<domain>:<port>[/<namespace>]
            var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

            // Event handler for new connections.
            // The callback function is invoked when a connection with the
            // server is established.
            socket.on('connect', function() {
                socket.emit('my_event', {data: 'I\'m connected!'});
            });

            // Event handler for server sent data.
            // The callback function is invoked whenever the server emits data
            // to the client. The data is then displayed in the "Received"
            // section of the page.
            socket.on('my_response', function(msg) {
                $('#log').append('<br>' + $('<div/>').text('Received #' + msg.count + ': ' + msg.data).html());
            });


            window.onload=function(){
                    socket.emit('load_projects');
                    };

            socket.on('my_projects',function(msg){
                $('#log').append('<br>' + $('<div/>').text('Received projects #' + msg.projects ).html());
                for ( var i in msg.projects){
                    current=msg.projects[i]
                    $('#project_list').append('<option value='+current+'>'+current+'</option>');
                    console.log(current);
                }
                console.log(msg);
                    });
            
            socket.on('analysis_output',function(msg){
                        console.log('Received Analysis output')
                        console.log(msg.parser_out);
                        console.log(msg.data);
                        var axisTemplate = {
                          range: [0, 30],
                          autorange: false,
                          showgrid: true,
                          zeroline: false,
                          linecolor: 'black',
                          showticklabels: true,
                          showscale: false,
                          ticks: ':'
                        };

                        var layout = {
                          title: 'Application Trace',
                          /*margin: {
                            t: 200,
                            r: 200,
                            b: 200,
                            l: 200
                          },*/
                          xaxis: {
                          range: [-0.5, 60.5],
                          autorange: false,
                          showgrid: true,
                          zeroline: false,
                          linecolor: 'black',
                          showticklabels: true,
                          showscale: false,
                          ticks: ':'
                        },
                          yaxis: {
                          range: [-0.5, 30.5],
                          autorange: false,
                          showgrid: true,
                          zeroline: false,
                          linecolor: 'black',
                          showticklabels: true,
                          showscale: false,
                          ticks: ':'
                        },
                          zaxis:{
                          showscale: false,
                            },
                          showlegend: false,
                          showscale: false,
                          dragmode: 'pan',
                          with: 700,
                          height: 700,
                          autosize: true
                        };
                        Plotly.newPlot('analysis_output', [msg.data],layout);
                    })
            socket.on('selected_project',function(msg){
                    console.log(msg.code);
                    $('#source_code').prepend('<div id="editor">'+escapeHTML(msg.code)+'</div>')
                    $('#source_code').append(
                    `
                    <form id='analyze' method='POST' action='#'>
                        <input type="SUBMIT" value="Analyze">
                    </form>
                    `);
                    var editor = ace.edit("editor");
                    editor.setTheme("ace/theme/monokai");
                    editor.session.setMode("ace/mode/c_cpp");
                    $('form#analyze').submit(function(event){
                        socket.emit('analyze_code',{source: editor.getValue()});
                        console.log(editor.getValue());
                        return false;
                    });
                    });


            // Handlers for the different forms in the page.
            // These accept data from the user and send it to the server in a
            // variety of ways
            $('form#broadcast').submit(function(event) {
                socket.emit('my_broadcast_event', {data: $('#broadcast_data').val()});
                return false;
            });
            $('form#join').submit(function(event) {
                socket.emit('join', {room: $('#join_room').val()});
                return false;
            });
            $('form#leave').submit(function(event) {
                socket.emit('leave', {room: $('#leave_room').val()});
                return false;
            });
            $('form#send_room').submit(function(event) {
                socket.emit('my_room_event', {room: $('#room_name').val(), data: $('#room_data').val()});
                return false;
            });
            $('form#close').submit(function(event) {
                socket.emit('close_room', {room: $('#close_room').val()});
                return false;
            });
            $('form#disconnect').submit(function(event) {
                socket.emit('disconnect_request');
                return false;
            });
            

            $('form#select_project').submit(function(event){
                socket.emit('select_project', {project: $('#project_list').val()});
                return false;
                    });
        }
