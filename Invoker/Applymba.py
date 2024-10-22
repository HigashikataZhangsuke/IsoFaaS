import subprocess

# This is per-core setting. So what you will do is:
# Assign All MBA first, since it is settled, except the shareable part.
# However need to dynamic change the core-COS mapping
def StaticAllocation(ProflingDataResourConsum,FuncList):
    #For mapping, we'd better settle them down: COS5 -> share, and all other for omp,vid,mlserve,mltrain,imgrot
    MemList = ["omp","vid","che","mlt","rot"]
    for i in range(5):
        if MemList[i] in FuncList:
            subprocess.run(['sudo', 'pqos', '-e', 'mba_max:' +str(i) + '=' + str(ProflingDataResourConsum[MemList[i]][1]), '-r'], check=True)

def DynamicAllocation(ProflingDataResourConsum,CurrMaskList,FuncList):
    #This is for the shareable parts. SH should get results same to the amount lefted in this VM.
    #Get lefted first:
    Lefted = 120*1024 #Check later.
    for function in FuncList:
        Lefted -= ProflingDataResourConsum[function][1]*sum(CurrMaskList[function])
    Lefted /= 2
    Lefted = int(Lefted)
    subprocess.run(
        ['sudo', 'pqos', '-e', 'mba_max:5'  + '=' + str(Lefted), '-r'],check=True)

def DynamicLinkcore(CurrMaskList,FuncList):
    MemList = ["omp", "vid", "che", "mlt", "rot"]
    for i in range(5):
        if MemList[i] in FuncList:
            cpu_list = ','.join(str(cpu) for cpu in CurrMaskList[MemList[i]])
            subprocess.run(['sudo', 'pqos', '-a', f'core:{i}={cpu_list}'],check=True)
    subprocess.run(['sudo', 'pqos', '-a', f'core:{5}={23}'], check=True)
