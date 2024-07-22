#!/bin/bash

#Firstly Start All Redis repo
./yamls/Redis.sh
#Then apply the trigger and broker.
kubectl apply -f ./yamls/broker.yaml
sleep 2
kubectl apply -f ./yamls/trigger.yaml
sleep 2
#Then start Fake SH and Fake Invoker
#numactl --cpunodebind=1 --membind=1 python3 FakeSh.py &
#numactl --cpunodebind=1 --membind=1 python3 FakeInvoker.py &
#echo "Start your curl now!"
#And Finally start the IsoExContainer.
sleep 1
kubectl apply -f ./yamls/IsoSh.yaml
sleep 1 
kubectl apply -f ./yamls/Curlpod.yaml
kubectl apply -f ./yamls/FakeIvkSh.yaml
sleep 1
kubectl get pods

