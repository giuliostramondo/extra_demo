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

function create_inner_card( title, content )
{
    var card_html_code=`
                    <div class="container">
                      <h3>`+title+`</h3>
                      <div class="card">
                        <div class="card-body">
                    `+content+`
                        </div>
                      </div>
                    </div>
                    `;
             
   return card_html_code;
}

function create_loop_info_string( loop_info )
{
            var loop_info_string="<div>Polymem's loop contains "+
                        loop_info.length+" nested loops.</div>";
            loop_info_string+='<table style="width:100%;">';
                loop_info_string+='<tr>';
                loop_info_string+='<th>Iterator Name</th>';
                loop_info_string+='<th>Start</th>';
                loop_info_string+='<th>End</th>';
                loop_info_string+='<th>Stride</th>';
                loop_info_string+='</tr>';
            for ( var i in loop_info){
                loop_info_string+='<tr>';
                loop_info_string+='<td>'+loop_info[i][0]+'</td>';
                loop_info_string+='<td>'+loop_info[i][1]+'</td>';
                loop_info_string+='<td>'+loop_info[i][2]+'</td>';
                loop_info_string+='<td>'+loop_info[i][3]+'</td>';
                loop_info_string+='</tr>';
            }
            loop_info_string+='</table>';
     return create_inner_card( "Loop Analysis",loop_info_string); 
}
function create_vec_accesses_info_string( vec_access_info )
{
                        var vec_access_info_string="<div>There are "+vec_access_info[1].length+" read accesses and "+vec_access_info[2].length+" write accesses.</div>";
                        vec_access_info_string+="<b>Read Accesses</b>";
                        vec_access_info_string+='<table style="width:100%;">';
                        var first_row=true;
                        var read_accesses=vec_access_info[1];
                       for (var i in read_accesses) {
                            if( first_row ){
                            
                            vec_access_info_string+='<tr>';
                            vec_access_info_string+='<th>Access To</th>';
                            for ( var j=0; j<read_accesses[i][2].length;j++ ){
                            
                                vec_access_info_string+='<th>Offset '+j+'</th>';
                            }
                            vec_access_info_string+='</tr>';
                            first_row=false;
                            }
                            vec_access_info_string+='<tr>';
                                vec_access_info_string+='<td>'+read_accesses[i][1]+'</td>';
                            for ( var j=0; j<read_accesses[i][2].length;j++ ){
                                vec_access_info_string+='<td>'+read_accesses[i][2][j]+'</td>';
                            }
                            vec_access_info_string+='</tr>';
                        } 
                        vec_access_info_string+='</table>';
                        vec_access_info_string+="<b>Write Accesses</b>";
                        vec_access_info_string+='<table style="width:100%;">';
                        first_row=true;
                        var write_accesses=vec_access_info[2];
                       for (var i in write_accesses) {
                            if( first_row ){
                            
                            vec_access_info_string+='<tr>';
                            vec_access_info_string+='<th>Access To</th>';
                            for ( var j=0; j<write_accesses[i][2].length;j++ ){
                            
                                vec_access_info_string+='<th>Offset '+j+'</th>';
                            }
                            vec_access_info_string+='</tr>';
                            first_row=false;
                            }
                            vec_access_info_string+='<tr>';
                                vec_access_info_string+='<td>'+write_accesses[i][1]+'</td>';
                            for ( var j=0; j<read_accesses[i][2].length;j++ ){
                                vec_access_info_string+='<td>'+write_accesses[i][2][j]+'</td>';
                            }
                            vec_access_info_string+='</tr>';
                        } 
                        vec_access_info_string+='</table>';
         return create_inner_card( "Memory Accesses Analysis",vec_access_info_string); 
}
function create_vec_size_info_string( vec_size_info )
{
            var vector_info_string="<div>There are "+Object.keys(vec_size_info).length+" vectors.</div>";
            vector_info_string+='<table style="width:100%;">';
            var first_row=true;
           for (var key in vec_size_info) {
                // check if the property/key is defined in the object itself, not in parent
                if (vec_size_info.hasOwnProperty(key)) {
                    var sizes = vec_size_info[key];
                    console.log(key, vec_size_info[key]);
                    if( first_row ){
                    
                    vector_info_string+='<tr>';
                    vector_info_string+='<th>Name</th>';
                    for ( var i in sizes ){
                    
                        vector_info_string+='<th>Dimension '+i+'</th>';
                    }
                    vector_info_string+='</tr>';
                    first_row=false;
                    }
                    vector_info_string+='<tr>';
                    vector_info_string+='<td>'+key+'</td>';
                    for ( var i in sizes ){
                        vector_info_string+='<td>'+sizes[i]+'</td>';
                    }
                    vector_info_string+='</tr>';
                }
            } 
            vector_info_string+='</table>';
            return create_inner_card("Vector Size Analysis",vector_info_string);
}
function get_trace_plot_legend()
{
        var legend=`
                <div style="position:relative;  top: -650px;left:710px;z-index: 10;" id="legend-outer">
                    <div id="legend-inner">
                        <span id="span-outer" class="rounded-0"><span id="inner-1" class="rounded-0"></span></span> Accessed
                        <span id="span-outer" class="rounded-0"><span id="inner-2" class="rounded-1"></span></span> Not Accessed
                    </div>
                </div>`;
    return legend;
}
function get_trace_plot_layout(){
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
    return layout;
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
                        console.log('loop_info');
                        console.log(msg.loop_info);
                        console.log('vec_access_info');
                        console.log(msg.vec_access_info);
                        console.log('vec_size_info');
                        console.log(msg.vec_size_info);

                        

                        var layout = get_trace_plot_layout();
                        var title= 'Analysis Results';
                        var loop_info_string=create_loop_info_string(msg.loop_info);
                        var legend=get_trace_plot_legend();
                        var content="";
                        var vector_info_string=create_vec_size_info_string( msg.vec_size_info )
                        var vec_access_info_string="<div>There are "+msg.vec_access_info[1].length+" read accesses and "+msg.vec_access_info[2].length+" write accesses.</div>";
                        vec_access_info_string+="<b>Read Accesses</b>";
                        vec_access_info_string+='<table style="width:100%;">';
                        var first_row=true;
                        var read_accesses=msg.vec_access_info[1];
                       for (var i in read_accesses) {
                            if( first_row ){
                            
                            vec_access_info_string+='<tr>';
                            vec_access_info_string+='<th>Access To</th>';
                            for ( var j=0; j<read_accesses[i][2].length;j++ ){
                            
                                vec_access_info_string+='<th>Offset '+j+'</th>';
                            }
                            vec_access_info_string+='</tr>';
                            first_row=false;
                            }
                            vec_access_info_string+='<tr>';
                                vec_access_info_string+='<td>'+read_accesses[i][1]+'</td>';
                            for ( var j=0; j<read_accesses[i][2].length;j++ ){
                                vec_access_info_string+='<td>'+read_accesses[i][2][j]+'</td>';
                            }
                            vec_access_info_string+='</tr>';
                        } 
                        vec_access_info_string+='</table>';
                        vec_access_info_string+="<b>Write Accesses</b>";
                        vec_access_info_string+='<table style="width:100%;">';
                        first_row=true;
                        var write_accesses=msg.vec_access_info[2];
                       for (var i in write_accesses) {
                            if( first_row ){
                            
                            vec_access_info_string+='<tr>';
                            vec_access_info_string+='<th>Access To</th>';
                            for ( var j=0; j<write_accesses[i][2].length;j++ ){
                            
                                vec_access_info_string+='<th>Offset '+j+'</th>';
                            }
                            vec_access_info_string+='</tr>';
                            first_row=false;
                            }
                            vec_access_info_string+='<tr>';
                                vec_access_info_string+='<td>'+write_accesses[i][1]+'</td>';
                            for ( var j=0; j<read_accesses[i][2].length;j++ ){
                                vec_access_info_string+='<td>'+write_accesses[i][2][j]+'</td>';
                            }
                            vec_access_info_string+='</tr>';
                        } 
                        vec_access_info_string+='</table>';
vec_access_info_string=create_vec_accesses_info_string( msg.vec_access_info );
                        content+=loop_info_string;
                        content+=vector_info_string;
                        content+=vec_access_info_string;
                        content+='<div id="trace_plot">'+legend+'</div>';
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
