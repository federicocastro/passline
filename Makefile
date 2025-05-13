# Makefile para ejecutar obtener_filas_sync.py en paralelo

NUM_TASKS=50
SCRIPT=obtener_filas_sync.py

run-parallel:
	seq 0 $(shell expr $(NUM_TASKS) - 1) | xargs -P $(NUM_TASKS) -I{} python $(SCRIPT) {}

.PHONY: run-parallel
