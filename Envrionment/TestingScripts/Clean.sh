#!/bin/bash
#now try to build image and then push to dockerhub. Need you login to dockerhub first
kubectl delete ksvc --all --namespace=default
kubectl delete broker default
kubectl delete triggers --all --namespace=default
kubectl delete pods --all --namespace=default --force

