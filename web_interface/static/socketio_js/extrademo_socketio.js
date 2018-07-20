function escapeHTML( string )
{
    var pre = document.createElement('pre');
    var text = document.createTextNode( string );
    pre.appendChild(text);
    return pre.innerHTML;
}

function create_card( title, content )
{
    var card_html_code=`
                    <div class="container">
                      <h2>`+title+`</h2>
                      <div class="card">
                        <div class="card-body">
                    `+content+`
                        </div>
                      </div>
                    </div>
                    `;
             
   return card_html_code;
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
                        var title= 'Analysis Results';
                        var legend=`
                            <div style="position:relative;  top: -650px;left:710px;z-index: 10;" id="legend-outer">
                                <div id="legend-inner">
                                    <span id="span-outer" class="rounded-0"><span id="inner-1" class="rounded-0"></span></span> Accessed
                                    <span id="span-outer" class="rounded-0"><span id="inner-2" class="rounded-1"></span></span> Not Accessed
                                </div>
                            </div>`;
                        var content='<div id="trace_plot">'+legend+'</div>';
                        var card = create_card(title,content);
                        //Remove old content of source_code div
                        $('#analysis_output').html("");
                        $('#analysis_output').prepend(card);
                        Plotly.newPlot('trace_plot', [msg.data],layout);
                    })

            socket.on('selected_project',function(msg){
                    console.log(msg.code);
                    var title = 'View Code';
                    var content ='<div id="editor">'+escapeHTML(msg.code)+'</div>'+ 
                    `
                    <br>
                    <form id='analyze' method='POST' action='#'>
                        <input type="SUBMIT" value="Analyze">
                    </form>`;
                    var card = create_card(title,content); 
                    //Remove old content of source_code div
                    $('#source_code').html("");
                    $('#source_code').prepend(card);

                    //Disable page scroll when on editor
                    $('#editor').mouseenter(function() {
                            $("body").addClass("editor-active");}
                        ).mouseleave(function() {
                            $("body").removeClass("editor-active");});


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
            

            $('form#select_project').submit(function(event){
                socket.emit('select_project', {project: $('#project_list').val()});
                return false;
                    });
        }
