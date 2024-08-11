#The part used for Exresource amount decision. Here just write the functions
#We use profiling data, and we shall provide it at the main py file.
import bisect

#Note the GC and GS/ merge or scale up, always can trigger getnewmask.

def GetNewMask(CurrMask,FuncName,Instruction,AllList,ArrivalRate,ProfilingDataTp,ProflingDataConsum,Bound,Clusterpolicy):
    #CurrMask: A dict stores alive function's CPU usage
    #FuncName: A string = funcname
    #AllList: CPU usage record list
    #Arrivalrate: a dict stores function's arrival rate. If it is zero means not an alive funtion
    #Profilingdatatp: CPU-TP dict
    #ProfilingConsum: Resource usage dict
    #Bound is a dict to record the bound of one function
    resource = []
    # Add one since start from zero
    # Profiling must be sorted, from small to bigg. No add to one, the overload part will be sent to the shareable part.
    CPUamount = bisect.bisect_left(ProfilingDataTp[FuncName], ArrivalRate[FuncName])
    if ArrivalRate[FuncName] - ProfilingDataTp[FuncName][CPUamount] > ArrivalRate[FuncName] - ProfilingDataTp[FuncName][CPUamount+1]:
        CPUamount += 1
    #Lastly check if reach the bound. If reached, stop at the bound. And tell the GS to cluster scaling.
    if CPUamount > Bound[FuncName]:
        CPUamount = Bound[FuncName]
        Clusterpolicy[FuncName] = "ClusterScaleup"
    resource.append(CPUamount)
    for i in range(1, 4):
        resource.append(CPUamount * ProflingDataConsum[FuncName][i])
    #Then after you get the new ex resource amount needed, and you know which one you need to update, then
    #Have potential perf increment here. by reduce j range.
    #print(CPUamount,flush=True)
    if Instruction =='ScaleUp':
        old = sum(CurrMask[FuncName])
        new_mask = list(CurrMask[FuncName])
        for i in range(old, resource[0]):
            # Add this much resource
            for j in range(len(AllList)):
                if AllList[j] == 1:
                    # Take the resources
                    new_mask[j] = 1
                    AllList[j] = 0
                    break
                #print(new_mask,flush=True)
        CurrMask[FuncName] = new_mask
    else:
        old = sum(CurrMask[FuncName])
        new_mask = list(CurrMask[FuncName])
        for i in range(resource[0],old):
            # Add this much resource
            for j in range(old):
                if CurrMask[FuncName][j] == 1:
                    # Take the resources
                    new_mask[j] = 0
                    AllList[j] = 1
                    break
        #print(new_mask, flush=True)
        CurrMask[FuncName] = new_mask
    #return resource