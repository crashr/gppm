#!/bin/bash

#while true; do

curl -N http://192.168.178.56:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer No-ClosedAI-API-key" \
  -d '{
    "model": "Codestral",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Write a poem on frogs"
      }
    ],
    "stream": false
  }'

#done
