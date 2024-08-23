# IsoFaaS
This repo is the prototype's implementation of IsoFaaS: Resource Isolation for function as a service, and MXFaaS, the baseline system.

IsoFaaS is a serverless platform that improves resource efficiency through resource isolation and global scheduling. IsoFaaS provides two different abstraction called Ex-container and Sh-container to enable fine granularity control. These abstractions will strictly bind the processes running inside it to CPUs and numa nodes, then with the help of Intel CAT and MBA technology, the given amount of resource would be allocated to them dynamically. Also, a global scheduler would apply scheduling algorithm to figure out a function placement policy, which will try to make compute bound functions and memory bound functions combined together.

## Baseline

[MXFaaS](https://github.com/jovans2/MXFaaS_Artifact) is a serverless platform improve serving capability through multiplexing. However, it only consider fully utilize CPU resources, ignoring the memory bandwidth side.

## Code structure
The baseline code is under Baseline/MXFaaS_Artifact directory, which contains original system and functions used in both systems. Curl has the container for trace generation. Envrionment directory has scripts for deployment and testing. LCTest,Profiling and TPProfiling are the codes for profiling functions/generate input data. ExIsoContainers and ShIsoContainers are the two new abstractions' implementation. And Invoker is the code for local single node autoscaling.

## Requirements
### Hardware
To fulfill the hardware requriements, the VM should support the Intel MBA and Intel CAT. We used C5.metal machine from AWS for testing. It has 2 numa nodes and 24 CPUs for each node.

### Software
The code runs on Ubuntu 20.04+, with latest Docker/Containerd/Kubernetes and KNative.
