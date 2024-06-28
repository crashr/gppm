#!/bin/bash

mkfifo llama_server_output_2
CUDA_VISIBLE_DEVICES=1,2
CUDA_VISIBLE_DEVICES=1,2 llama-server --host 0.0.0.0 -ngl 100 -m ~/models/Replete-Coder-Llama3-8B-Q4_K_M.gguf --port 8082 -fa -sm row -mg 0 --no-mmap --log-format json > llama_server_output_2 &
llamacpp_pid=$!
jq --unbuffered -c --arg pid "$llamacpp_pid" --arg cvd "$CUDA_VISIBLE_DEVICES" ".gppm = {\"llamacpp_pid\":\$pid,\"gppm_cvd\":\$cvd}" < llama_server_output_2 \
| egrep "slot is processing task|slot released" --line-buffered \
| tee -a ~/llama-server.log
rm llama_server_output_2

