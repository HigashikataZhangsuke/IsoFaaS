import math

def ComputeBound(ArrivalRateDict,ProfilingDataConsum):
    #Maybe no element in AliveList, this means need to just set the func
    #Assuming all rate containd in the Arrival Rate dict.
    #FuncName is the new func added here
    #CurrFuncList is the curr alive func in this node
    #ArrivalRate is the Rate vector, contains all rate of related alive function you need. This could be attained before computation through
    #Redis Reading
    NewBounds = {}
    AliveList = []
    for func in ArrivalRateDict:
        if ArrivalRateDict[func] >0:
            AliveList.append(func)
    #A dictioinary contains all DataConsumption you need.
    #Then all the needed data will be reachable from the Dic and Rate Ratio. Solve the equation,pick the smallest one to get bounds.
    #For each func you have one bound, so will have len(CurrFuncList) bounds to return
    smallest = 10000
    TotalResource = [23,120*1024,192*1024,11] #check later if we really need this. think about CAT usage here.
    Ratio = {}
    FuncName = min(ArrivalRateDict, key=lambda k: ArrivalRateDict[k])
    for item in range(len(AliveList)):
        Ratio[AliveList[item]] = ArrivalRateDict[AliveList[item]]/ArrivalRateDict[FuncName]
    for i in range(4):
        Coeff = 0
        for item in range(len(AliveList)):
            Coeff +=  (ProfilingDataConsum[AliveList[item]][i])*Ratio[AliveList[item]]
        if TotalResource[i]/Coeff<smallest:
            smallest = math.floor(TotalResource[i]/Coeff)
    #New bound first, a tuple. And the CPU/MBA/CAT should be integer. Here to put the system's one numa node's maximuim BW, and maximum allocable cache line(To check later)
    for key in AliveList:
        NewBounds[key] = (Ratio[key]*math.floor(smallest*ProfilingDataConsum[key][0]),Ratio[key]*math.floor(smallest*ProfilingDataConsum[key][1]),Ratio[key]*smallest*ProfilingDataConsum[key][2],Ratio[key]*math.floor(smallest*ProfilingDataConsum[key][3]))
    return NewBounds

def ComputeCost(FuncName, NewBounds, ArrivalRateDict,ProfilingDataTP):
    # Assuming all rate containd in the Arrival Rate.
    #To get the cost, find out the unused resources amount, then apply the cost function
    Cost = 0
    RateRatio = []
    TotalResource = 23 #Or 24?
    for key in NewBounds:
        TotalResource -= NewBounds[key][0]
        RateRatio.append(ArrivalRateDict[key]/sum(ArrivalRateDict.values()))
    #The get the Cost:
    for key in NewBounds:
        Cost -= ProfilingDataTP[FuncName][math.floor(RateRatio[key]*TotalResource)]
    return Cost
