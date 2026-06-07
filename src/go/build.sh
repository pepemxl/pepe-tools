#!/bin/bash
cd go
go build -buildmode=c-shared -o libbridge.so bridge.go
cp libbridge.so ../pepe_tools/