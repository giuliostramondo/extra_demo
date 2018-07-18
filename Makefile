ifndef SOURCE
$(error SOURCE is not set. Please define the input source file SOURCE=input.c )
endif
ifdef SOURCE
$(info == Using input file $(SOURCE) )
endif

INPUT_FILE_STEM=$(basename $(SOURCE))

all: analysis prediction design

analysis: $(SOURCE) 
	cat current_input.c | grep -v "#include" $(INPUT_FILE_STEM)_no_header.c 
	python input_code/parser_2.py $(INPUT_FILE_STEM)_no_header.c
	if [ ! -d "patterns" ];then mkdir patterns;fi
	mv $(INPUT_FILE_STEM)_no_header.atrace patterns
	mv $(INPUT_FILE_STEM)_no_header.maxj_compute $(INPUT_FILE_STEM)_no_header.vec_info generated_hardware_design
	python ./performance_prediction/prf_utils.py writePDFTrace ./patterns/$(INPUT_FILE_STEM)_no_header.atrace
	mv trace.pdf ./patterns/$(INPUT_FILE_STEM)_no_header_trace.pdf

prediction: patterns/$(INPUT_FILE_STEM)_no_header.atrace
	python2.7 performance_prediction/schedule_atrace.py patterns/$(INPUT_FILE_STEM)_no_header.atrace ReRo 2 4
	python2.7 performance_prediction/schedule_atrace.py patterns/$(INPUT_FILE_STEM)_no_header.atrace ReCo 2 4
	python2.7 performance_prediction/schedule_atrace.py patterns/$(INPUT_FILE_STEM)_no_header.atrace RoCo 2 4
	python2.7 performance_prediction/schedule_atrace.py patterns/$(INPUT_FILE_STEM)_no_header.atrace ReTr 2 4
	if [ ! -d "schedules" ];then mkdir schedules;fi
	mv patterns/*.schedule schedules
	./performance_prediction/generate_analysis.sh $(INPUT_FILE_STEM)_no_header
	mv $(INPUT_FILE_STEM)_no_header.analysis schedules
	@echo "Best configuration"
	@cat ./schedules/$(INPUT_FILE_STEM)_no_header.analysis | head -n 1 | sed "s/,/ /g"
	@cat ./schedules/$(INPUT_FILE_STEM)_no_header.analysis | tail -n +2 |sed "s/,/ /g" | sort -k7rn -k1n | head -n 1

design:
	cd generated_hardware_design;./generate_cfg.sh $(INPUT_FILE_STEM)_no_header;unzip PolyMemStream_ref.zip;cp -r ./PolyMemStream_ref/ ./PolyMemStream_out;./generate_prf_constants.sh $(INPUT_FILE_STEM)_no_header;python ./generate_kernel.py $(INPUT_FILE_STEM)_no_header;mv PRFStreamKernel.maxj PolyMemStream_out/EngineCode/src/prfstream/
	

sequential:
	gcc  -std=c99 current_input.c -o current_input
	
clean:
	rm -rf parser_error.log patterns schedules ./generated_hardware_design/PolyMemStream_out/ current_input.maxj_compute current_input.cfg current_input.vec_info 

