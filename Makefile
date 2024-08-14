.PHONY: test

SAMPLE_DIR := BIH-run/W_240523_1_10842_1_insect_RNA

all: data add rerun

data:
	./make-data.py --virus hendra --outDir OUT

add:
	./add-data.py \
            --sampleDir $(SAMPLE_DIR) \
            --json OUT/json/*.json.bz2 \
            --fastq OUT/fastq/*.fastq.gz

rerun:
	./rerun-pipeline.py --sampleDir $(SAMPLE_DIR)

test:
	env PYTHONPATH=. pytest -v

clean:
	rm -f *~
	rm -fr OUT
	find . -name .mypy_cache | xargs -r rm -fr
	find . -name .pytest_cache | xargs -r rm -fr
	find . -name .__pycache__ | xargs -r rm -fr
