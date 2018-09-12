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
                    <br>
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

function csv_to_html_table( data ){
            var lines = data.split("\n");
            var output = [];
            for (i = 0; i < lines.length; i++)
                if (!(lines[i] === "")){
                    if(i==0){
                    output.push("<tr><th>"
                    + lines[i].slice(0,-1).split(",").join("</th><th>")
                    + "</th></tr>");
                    }else{
                     output.push("<tr><td>"
                    + lines[i].slice(0,-1).split(",").join("</td><td>")
                    + "</td></tr>");                           
                    }
                }
            output = "<table>" + output.join("") + "</table>";
            return output;
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


            $(document).ready(function(){
                    socket.emit('load_projects');
                    });
            socket.on('my_projects',function(msg){
                $('#log').append('<br>' + $('<div/>').text('Received projects #' + msg.projects ).html());
                    $('#project_list').html("");
                for ( var i in msg.projects){
                    current=msg.projects[i]
                    $('#project_list').append('<option value='+current+'>'+current+'</option>');
                    console.log(current);
                }
                if  (!(msg.selected_project=='not set')){
                    $('#project_list').val(msg.selected_project);
                    if(!(msg.selected_project=="dummy_project")){
                        $('#delete_project').css("visibility", "visible");
                    }else{
                        $('#delete_project').css("visibility", "hidden");
                    }
                }else{
                        $('#delete_project').css("visibility", "hidden");

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
                       
                        var vec_access_info_string=create_vec_accesses_info_string( msg.vec_access_info );
                        content+=loop_info_string;
                        content+=vector_info_string;
                        content+=vec_access_info_string;
                        content+='<div id="trace_plot">'+legend+'</div>';
                        content+=`
                        <form id='performance' method='POST' action='#'>
                            <input type="SUBMIT" value="Performance Prediction">
                        </form>`;
                        var card = create_card(title,content);
                        //Remove old content of source_code div
                        $('#analysis_output').html("");
                        $('#analysis_output').prepend(card);
                        Plotly.newPlot('trace_plot', [msg.data],layout);

                        $('form#performance').submit(function(event){
                            socket.emit('performance_prediction',{'data':'ciao'});
                            return false;
                        });
                    });

            var perf_pred_threads=0;
            var perf_pred_done=0;
            socket.on('started_performance_prediction',function(msg){
                    console.log('=== started performance prediction with '+msg.threads+' threads.'); 
                    perf_pred_threads=msg.threads;
                    perf_pred_done=0;
            });
            
            socket.on('done_performance_prediction',function(msg){
                    console.log('=== thread over with performance prediction');
                    console.log('=== total threads:'+perf_pred_threads); 
                    perf_pred_done+=1;
                    console.log('=== done threads:'+perf_pred_done); 
                    if( perf_pred_done == perf_pred_threads){
                        console.log('=== all done emit stuff to get analysis'); 
                        socket.emit('gen_schedule_analysis'); 
                    } 
            });
            
            socket.on('gen_schedule_analysis_done',function(msg){
                    console.log('=== received schedule analysis');
                    console.log(msg);
                    title="Performance Prediction";
                    data=msg.analysis;
                    output = csv_to_html_table(data);
                    perf_table_card= 
                        create_inner_card(
                                "Speedup, Efficiency, Expected Bandwidth",
                                output);
                    var content = perf_table_card;
                    content+=`
                    <br>
                    <form id='generate_design' method='POST' action='#'>
                        <input type="SUBMIT" value="Generate Design">
                    </form>`;
                    var card = create_card(title,content);
                    $('#performance_prediction_output').html("");
                    $('#performance_prediction_output').prepend(card);
                    $('form#generate_design').submit(function(event){
                        socket.emit('generate_design');
                        return false;
                    });
            });

            socket.on('generate_design_done',function(msg){
                    console.log('=== received project generation');
                    console.log(msg)
                    console.log(msg.generated_host_c);
                    var title= "Generated Design";
                    var content= '<div id="editorGenDesign">'+
                            escapeHTML(msg.generated_host_c)+'</div>'+
                    `
                    <br>
                    <form id='simulate_design' method='POST' action='#' style='display:inline;'>
                        <input type="SUBMIT" value="Simulate Design">
                    </form>
                    <button class="btn-dl"><i class="fa fa-download"></i>`+ 
                        "<a href='"+msg.project_no_sinth_zip+
                        "' style='color: inherit;text-decoration: inherit;'> Download Maxeler Project</a>"+
                    "</button>";
                    var card = create_card(title,content); 
                    // Remove old content
                    $('#generated_design').html("");
                    $('#generated_design').prepend(card);
                     //Disable page scroll when on editor
                    $('#editorGenDesign').mouseenter(function() {
                            $("body").addClass("editor-active");}
                        ).mouseleave(function() {
                            $("body").removeClass("editor-active");});
                    var editorGenDesign = ace.edit("editorGenDesign");
                    editorGenDesign.setTheme("ace/theme/monokai");
                    editorGenDesign.setShowPrintMargin(false);
                    editorGenDesign.session.setMode("ace/mode/c_cpp");          
                    $('form#simulate_design').submit(function(event){
                        console.log(editorGenDesign.getValue());
                        socket.emit('simulate_design');
                        return false;
                    });
            });

            current_project=""
            socket.on('selected_project',function(msg){
                    
                    socket.emit('load_projects');
                    console.log(msg.code);
                    //wipe project contents
                    current_project=msg.selected_project;
                    $(".project_data").html("");
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
                    editor.setShowPrintMargin(false);
                    editor.session.setMode("ace/mode/c_cpp");
                    $('form#analyze').submit(function(event){
                        socket.emit('analyze_code',{source: editor.getValue()});
                        console.log(editor.getValue());
                        return false;
                    });
                    });
            
            socket.on('created_project',function(msg){
                if(msg.error=='none'){
                    //close modal
                    $('#exampleModalCenter').modal('hide');
                }else{
                    //display error in modal
                    $('#create_project_modal_error').html(msg.error);
                }
            });
            socket.on('flush_card',function(msg){
                if(msg.card == 'analysis'){
                    console.log('flushing analysis');
                    $('#analysis_output').html("");
                }
                if(msg.card == 'performance_pred'){
                    console.log('flushing perf pred');
                    $('#performance_prediction_output').html("");
                }
            });
            socket.on('sim_verification_done',function(){
                console.log('sim verification done, asking data');
                socket.emit('send_sim_data');
                return false;
            });
            socket.on('sim_verification',function(msg){
                console.log("data revceived");
                console.log(msg);
                var title="Validation Results";
                var validation_outcome="<font color='green'>Succeded</font>";
                if(msg.validation_result != 0){
                    validation_outcome="<font color='red'>Failed</font>";
                }
                var content = "<b>Simulation "+validation_outcome+" </b><br><br>";
                var next_card_trigger=`
                    <br>
                    <form id='synthesize_design' method='POST' action='#' style='display:inline;'>
                        <input type="SUBMIT" value="Synthesize Design">
                    </form>`;
                var dl_c_dump='<button class="btn-dl"><i class="fa fa-download"></i>'+ 
                        "<a href='"+msg.c_source_dump+
                        "' style='color: inherit;text-decoration: inherit;'> Download C Vector Dump</a>"+
                    "</button> ";                   
                var dl_dfe_dump='<button class="btn-dl"><i class="fa fa-download"></i>'+ 
                        "<a href='"+msg.dfe_host_dump+
                        "' style='color: inherit;text-decoration: inherit;'> Download DFE Vector Dump</a> "+
                    "</button>";    
                var dl_diff=' <button class="btn-dl"><i class="fa fa-download"></i>'+ 
                        "<a href='"+msg.c_source_vs_dfe_host_dump+
                        "' style='color: inherit;text-decoration: inherit;'> Download C vs DFE diff</a>"+
                    "</button>";
                content+=next_card_trigger;
                content+=dl_c_dump;
                if (msg.validation_result!=0){
                    content+=dl_dfe_dump;
                    content+=dl_diff;
                }
                var card=create_card(title,content);
                $('#simulation').html("");
                $('#simulation').prepend(card);

                $('form#synthesize_design').submit(function(event){
                        socket.emit('synthesize_design');
                        return false;
                    });
                return false; 
            });
            // Handlers for the different forms in the page.
            // These accept data from the user and send it to the server in a
            // variety of ways
            

            $('form#select_project').submit(function(event){
                socket.emit('select_project', {project: $('#project_list').val()});
                return false;
                    });

            

            $('form#create_project').submit(function(event){
                //TODO check name
                socket.emit('create_project',
                    {project_name:$('#create_project_name_input').val()});
                return false;
                    });
            $('form#delete_project').submit(function(event){
                //TODO check name
                console.log("called delete project with arg " + current_project);
                socket.emit('delete_project',
                    {project_name:current_project});
                current_project="";
                
                $(".project_data").html("");
                return false;
                    });
        }
