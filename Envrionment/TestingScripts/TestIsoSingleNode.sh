#!/bin/bash
echo "Applying Broker"
kubectl apply -f ./yamls/broker.yaml
sleep 2
for trigger in ./BrokerTriggers/trigger*.yaml; do
    echo "Applying $trigger..."
    kubectl apply -f "$trigger"
done
sleep 2
for exsvc in ./svcyamls/isoex*.yaml; do
    echo "Applying $exsvc"
    kubectl apply -f "$exsvc"
done
sleep 2
echo "Applying Shareable"
kubectl apply -f ./svcyamls/isoshare.yaml
sleep 5
kubectl get pods

