all: analysis prediction design

analysis: current_input.c
	cat current_input.c | grep -v "#include" > current_input_no_header.c
	python input_code/parser_2.py current_input_no_header.c
	if [ ! -d "patterns" ];then mkdir patterns;fi
	mv current_input_no_header.atrace patterns
	mv current_input_no_header.maxj_compute current_input_no_header.vec_info generated_hardware_design
	python ./performance_prediction/prf_utils.py writePDFTrace ./patterns/current_intput_no_header.atrace
	mv trace.pdf ./patterns/current_intput_no_header_trace.pdf

prediction: patterns/current_input.atrace
	python2.7 performance_prediction/schedule_atrace.py patterns/current_input.atrace ReRo 2 4
	python2.7 performance_prediction/schedule_atrace.py patterns/current_input.atrace ReCo 2 4
	python2.7 performance_prediction/schedule_atrace.py patterns/current_input.atrace RoCo 2 4
	python2.7 performance_prediction/schedule_atrace.py patterns/current_input.atrace ReTr 2 4
	if [ ! -d "schedules" ];then mkdir schedules;fi
	mv patterns/*.schedule schedules
	./performance_prediction/generate_analysis.sh
	mv current_input.analysis schedules
	@echo "Best configuration"
	@cat ./schedules/current_input.analysis | head -n 1 | sed "s/,/ /g"
	@cat ./schedules/current_input.analysis | tail -n +2 |sed "s/,/ /g" | sort -k7rn -k1n | head -n 1

design:
	cd generated_hardware_design;./generate_cfg.sh;cp -r ./PolyMemStream_ref/ ./PolyMemStream_out;./generate_prf_constants.sh;python ./generate_kernel.py;mv PRFStreamKernel.maxj PolyMemStream_out/EngineCode/src/prfstream/
	

sequential:
	gcc  -std=c99 current_input.c -o current_input
	
clean:
	rm -rf parser_error.log patterns schedules ./generated_hardware_design/PolyMemStream_out/ current_input.maxj_compute current_input.cfg current_input.vec_info 

