#!/bin/bash
echo "Applying Broker"
kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/broker.yaml
sleep 2
for exsvc in /home/ubuntu/Envrionment/svcyamls/isoex*.yaml; do
    echo "Applying $exsvc"
    kubectl apply -f "$exsvc"
done
sleep 2
echo "Applying Shareable"
kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoshare.yaml
sleep 5
kubectl get pods
for trigger in /home/ubuntu/Envrionment/BrokerTriggers/trigger*.yaml; do
    echo "Applying $trigger..."
    kubectl apply -f "$trigger"
done



#Shall start them first, then start iso invoker, and finally start curl/Rate.
