from typing import Dict

from numpy.core.defchararray import upper

import base
import random
import linecache
import os
import time
import shutil
state_N:int = base.N
upper_N:int = 2*base.N
n:int = upper_N.bit_length()-1
m:int = base.m
len_prefix:int = n - n//2
len_suffix:int = n//2
cnt = 0
# def expand(root: str, Database) -> str:
#     key = ["0"] * (2 ** (len_prefix + 1)-1)
#     key[0] = root
#     for i in range(2**len_prefix-1):
#         key[2*i+1] = base.Hash("0"+key[i], base.sha256)
#         key[2*i+2] = base.Hash("1"+key[i], base.sha256)
#     parity: str = "0"
#     for i in range(2**len_prefix-1, 2**(len_prefix+1)-1):
#         prefix: int = i-2**len_prefix+1
#         suffix = int(base.Hash(str(prefix)+key[i], base.sha256)[0:4], 16)>>(16 - len_suffix)
#         index: int = (prefix << len_suffix) + suffix
#         data = linecache.getline(Database, index+1)
#         parity = hex((int(parity, 16) ^ int(data, 16)))[2:]
#     return parity

def expand(root: str, Database, height:int, start_prefix: int) -> str:
    global cnt
    key = ["0"] * (2 ** (height + 1)-1)
    key[0] = root
    for i in range(2**height-1):
        key[2*i+1] = base.Hash("0"+key[i], base.sha256)
        key[2*i+2] = base.Hash("1"+key[i], base.sha256)
    parity: str = "0"
    for i in range(2**height-1, 2**(height+1)-1):
        prefix = start_prefix + i - (2**height - 1)
        suffix = (int(base.Hash(str(prefix)+key[i], base.sha256)[0:8], 16)>>(32 - len_suffix))
        index: int = (prefix << len_suffix) + suffix
        if index+1 > state_N:
            data = "0"
        else:
            data = linecache.getline(Database, index+1)
        # cnt += 1
        parity = hex((int(parity, 16) ^ int(data, 16)))[2:]
    return parity

class Client:
    def __init__(self, FolderName: str = "TreePIR_Client_Hints"):
        self.HintsNumber = 2 ** len_suffix * n
        self.HintSize = 2 ** len_prefix
        self.FolderName = FolderName
        try:
            os.makedirs(FolderName, exist_ok=False)  # 创建文件夹
        except FileExistsError:
            pass  # 如果文件夹已存在，则忽略错误

    def FindHints(self, index: int) -> [[str, str]]:
        candidates = []
        prefix: int = index >> len_suffix
        bin_prefix: str = bin(index >> len_suffix)[2:].zfill(len_prefix)
        suffix: int = index & ((1 << len_suffix) - 1)
        # 遍历文件夹中的所有文件
        for filename in os.listdir(self.FolderName):
            key: str = filename
            tmp :str = key
            for i in bin_prefix:
                tmp = base.Hash(i+tmp, base.sha256)
            tmp_suffix: int = (int(base.Hash(str(prefix)+tmp, base.sha256)[0:8], 16)>>(32 - len_suffix))
            if suffix == tmp_suffix:
                with open(self.FolderName+"/"+filename, "r") as f:
                    parity = f.readline()
                candidates.append([key, parity])
        return candidates

    def OnlineQuery(self, index:int):
        prefix: int = index >> len_suffix
        bin_prefix: str = bin(prefix)[2:].zfill(len_prefix)
        suffix: int = index & ((1 << len_suffix) - 1)
        candidates = self.FindHints(index)
        key, parity = random.choice(candidates)
        # print(key, parity)
        while True:
            left = []
            right = []
            k: str = hex(random.randint(0, 2 ** 256))[2:]
            tmp: str = k
            for i in bin_prefix:
                if i == "0":
                    right.append(base.Hash("1" + tmp, base.sha256))
                if i == "1":
                    left.append(base.Hash("0" + tmp, base.sha256))
                tmp = base.Hash(i + tmp, base.sha256)
            tmp_suffix: int = (int(base.Hash(str(prefix) + tmp, base.sha256)[0:8], 16) >> (32 - len_suffix))
            if suffix == tmp_suffix:
                right.reverse()
                merged2 = left + right
                break
        left = []
        right = []
        tmp = key
        for i in bin_prefix:
            if i == "0":
                right.append(base.Hash("1" + tmp, base.sha256))
            if i == "1":
                left.append(base.Hash("0" + tmp, base.sha256))
            tmp = base.Hash(i + tmp, base.sha256)
        right.reverse()
        merged1 = left + right
        return merged1, merged2, key, parity, k

    def OnlineRecovery(self, index:int, parities1:[str], parities2:[str], key:str, parity:str, k:str):
        ans = hex(int(parities1[index>>len_suffix], 16) ^ int(parity, 16))[2:]
        new_parity = hex(int(parities2[index>>len_suffix], 16) ^ int(ans, 16))[2:]
        # 修改 client 的 Hints
        os.remove(self.FolderName + "/" + key)
        filename: str = os.path.join(self.FolderName, k)
        with open(filename, 'w') as f:
            f.write(new_parity)
        return ans

    def Add(self, myData: list):
        if state_N + 2**len_suffix > upper_N:
            print("upper_bound!")
            return
        prefix = state_N >> len_suffix
        bin_prefix: str = bin(prefix)[2:].zfill(len_prefix)
        for filename in os.listdir(self.FolderName):
            key: str = filename
            tmp :str = key
            for i in bin_prefix:
                tmp = base.Hash(i+tmp, base.sha256)
            tmp_suffix: int = (int(base.Hash(str(prefix)+tmp, base.sha256)[0:8], 16)>>(32 - len_suffix))
            with open(self.FolderName+"/"+filename, "r") as f:
                parity = f.readline()
            parity = hex((int(parity, 16) ^ int(myData[tmp_suffix], 16)))[2:]
            with open(self.FolderName+"/"+filename, "w") as f:
                f.write(parity)
        return

class Server:
    def __init__(self, filename:str = 'server.txt'):
        self.filename = filename
        try:
            with open(filename, 'x'):
                pass  # 不进行任何读写操作，只需创建文件
        except FileExistsError:
            pass
        return

    def HintGenerator(self, key:str) -> str:
        return expand(key, self.filename, len_prefix, 0)

    def OnlineAnswer(self, merged)-> [str]:
        mydict = dict()
        ans = []
        for i in range(2**len_prefix):
            point = [0, len(merged) - 1]
            parity = "0"
            for j in range(len_prefix, 0, -1):
                x = (i & (1 << (j - 1))) >> (j - 1)
                subscript = bin((i>>(j-1))^1)[2:].zfill(len_prefix)[-(len_prefix-j+1):]
                now = point[x^1]
                if mydict.get((subscript, merged[now])) is None:
                    mydict[(subscript, merged[now])] = hex(int(expand(merged[now], self.filename, j-1, int(subscript, 2)<<(j-1)), 16))[2:]
                parity = hex(int(mydict[(subscript, merged[now])], 16) ^ int(parity, 16))[2:]
                point[x^1] += (2*x-1)
            ans.append(parity)
        return ans

    def Add(self, myData=None):
        if state_N + 2 ** len_suffix > upper_N:
            return
        if myData is None:
            myData = base.add_entry(self.filename, num_entries=2**len_suffix)
            return myData
        base.add_entry(self.filename, len(myData), myData)
        return myData


def offline(c:Client, s:Server):
    start = time.time()
    klist = []
    for _ in range(c.HintsNumber):
        key:str = hex(random.randint(0,2**256))[2:]
        klist.append(key)
    end = time.time()
    clienttime1 = end-start
    uploadsize = base.getdatasize(klist)
        # send k to server2
    start = time.time()
    paritylist = []
    for key in klist:
        parity:str = s.HintGenerator(key)
        paritylist.append(parity)
        # send parity to client
    end = time.time()
    servertime = end-start
    downloadsize = base.getdatasize(paritylist)
    start = time.time()
    for i in range(c.HintsNumber):
        filename: str = os.path.join(c.FolderName,klist[i])
        with open(filename, 'w') as f:
            f.write(paritylist[i])
    end = time.time()
    clienttime2 = end-start
    return clienttime1+clienttime2, servertime, uploadsize, downloadsize

def online(c:Client, s1:Server, s2:Server, index:int):
    start = time.time()
    merged1, merged2, key, parity, k = c.OnlineQuery(index)
    end = time.time()
    clienttime1 = end-start
    uploadsize = base.getdatasize(merged1)+base.getdatasize(merged2)
    # send merged1 to server1
    # send merged2 to server2
    start = time.time()
    ans1 = s1.OnlineAnswer(merged1)[0:2**(len_prefix-1)]
    ans2 = s2.OnlineAnswer(merged2)[0:2**(len_prefix-1)]
    end = time.time()
    servertime = (end-start)/2
    downloadsize = base.getdatasize(ans1)+base.getdatasize(ans2)
    # send ans1 and ans2 to client
    start = time.time()
    ans = c.OnlineRecovery(index,ans1,ans2,key,parity,k)
    end = time.time()
    clienttime2 = end-start
    return ans, clienttime1+clienttime2, servertime, uploadsize, downloadsize

def Add(c:Client, s: Server, myData=None):
    global state_N
    start = time.time()
    myData = s.Add(myData)
    end = time.time()
    servertime = end-start
    start = time.time()
    c.Add(myData)
    end = time.time()
    clienttime = end-start
    # state_N = state_N + 2 ** len_suffix
    return clienttime, servertime, 0, base.getdatasize(myData)

if __name__ == "__main__":
    DEBUG = 0
    offlinetest = 1
    onlinetest = 1
    addtest = 1
    shutil.rmtree("TreePIR_Client_Hints")
    os.mkdir("TreePIR_Client_Hints")
    testdata = base.testdata
    base.getData(testdata, "./", "server")
    aimtxt = base.aimtxt
    client = Client()
    server1 = Server()
    server2 = Server()
    
    if offlinetest: 
        clienttime, servertime, uploadsize, downloadsize = 0, 0, 0, 0
        for i in range(1):
            ct, st, upsiz, downsiz = offline(client, server2)
            shutil.rmtree("TreePIR_Client_Hints")
            os.mkdir("TreePIR_Client_Hints")
            clienttime += ct
            servertime += st
            uploadsize += upsiz
            downloadsize += downsiz
        clienttime /= 1
        servertime /= 1
        uploadsize /= 1
        downloadsize /= 1
        print(clienttime, servertime, uploadsize, downloadsize)
        if DEBUG == 0:
            with open(aimtxt, "a+") as f:
                f.write(str(clienttime*1000)+" "+str(servertime*1000)+" "+str(uploadsize)+" "+str(downloadsize)+"\n")
    if onlinetest:
        offline(client,server2)
        clienttime, servertime, uploadsize, downloadsize = 0, 0, 0, 0
        for _ in range(2**3):
            ans, ct, st, upsiz, downsiz = online(client, server1, server2, 34)
            clienttime += ct
            servertime += st
            uploadsize += upsiz
            downloadsize += downsiz
        it = 2**(len_suffix - 3)
        clienttime *= it
        servertime *= it
        uploadsize *= it
        downloadsize *= it
        print(clienttime, servertime, uploadsize, downloadsize)
        if DEBUG == 0:
            with open(aimtxt, "a+") as f:
                f.write(str(clienttime*1000)+" "+str(servertime*1000)+" "+str(uploadsize)+" "+str(downloadsize)+"\n")
        shutil.rmtree("TreePIR_Client_Hints")
        os.mkdir("TreePIR_Client_Hints")
    
    if addtest:
        offline(client,server2)
        clienttime, servertime, uploadsize, downloadsize = Add(client, server2)
        print(clienttime, servertime, uploadsize, downloadsize)
        if DEBUG == 0:
            with open(aimtxt, "a+") as f:
                f.write(str(clienttime*1000)+" "+str(servertime*1000)+" "+str(uploadsize)+" "+str(downloadsize)+"\n")
        shutil.rmtree("TreePIR_Client_Hints")
        os.mkdir("TreePIR_Client_Hints")


