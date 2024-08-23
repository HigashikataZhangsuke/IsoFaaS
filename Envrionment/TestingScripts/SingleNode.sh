#!/bin/bash
#echo "Applying Broker"
kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/broker.yaml
kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggermat.yaml
#kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggerpyae.yaml
#kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggerrot.yaml
#kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggerweb.yaml
#kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggermls.yaml
kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggervid.yaml
kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggeralu.yaml
kubectl apply -f /home/ubuntu/Envrionment/BrokerTriggers/triggermlt.yaml
sleep 2
#kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexmls.yaml
#kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexpyae.yaml
#kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexrot.yaml
#kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexweb.yaml
kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexmat.yaml
kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexvid.yaml
kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexalu.yaml
kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoexmlt.yaml
#kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoshare.yaml
sleep 5
kubectl get pods
sleep 5
kubectl apply -f curl.yaml
#kubectl apply -f curl.yaml
#for exsvc in /home/ubuntu/Envrionment/svcyamls/isoex*.yaml; do
#    echo "Applying $exsvc"
#    kubectl apply -f "$exsvc"
#done
#sleep 2
#echo "Applying Shareable"
#kubectl apply -f /home/ubuntu/Envrionment/svcyamls/isoshare.yaml
#sleep 2
#kubectl get pods
#for trigger in /home/ubuntu/Envrionment/BrokerTriggers/trigger*.yaml; do
#    echo "Applying $trigger..."
#    kubectl apply -f "$trigger"
#done



#Shall start them first, then start iso invoker, and finally start curl/Rate.
