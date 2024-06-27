#!/bin/bash

#mkfifo llama_server_output_1
CUDA_VISIBLE_DEVICES=0,1
CUDA_VISIBLE_DEVICES=0,1 llama-server --host 0.0.0.0 -ngl 100 -m ~/models/Codestral-22B-v0.1-Q8_0.gguf --port 8081 -fa -sm row -mg 0 --no-mmap --log-format json > llama_server_output_1 &
llamacpp_pid=$!
jq --unbuffered -c --arg pid "$llamacpp_pid" --arg cvd "$CUDA_VISIBLE_DEVICES" ".gppm = {\"llamacpp_pid\":\$pid,\"gppm_cvd\":\$cvd}" < llama_server_output_1 \
| egrep "slot is processing task|slot released" --line-buffered \
| tee -a ~/llama-server.log
rm llama_server_output_1

