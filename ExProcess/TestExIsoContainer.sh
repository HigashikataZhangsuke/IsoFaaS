#!/bin/bash

#Firstly Start All Redis repo
./yamls/Redis.sh
#Then apply the trigger and broker.
kubectl apply -f ./yamls/broker.yaml
sleep 2
kubectl apply -f ./yamls/trigger.yaml
sleep 15
#Then start Fake SH and Fake Invoker
numactl --cpunodebind=1 --membind=1 python3 FakeSh.py &
numactl --cpunodebind=1 --membind=1 python3 FakeInvoker.py &
#And Finally start the IsoExContainer.
sleep 1
kubectl apply -f ./yamls/IsoEx.yaml

