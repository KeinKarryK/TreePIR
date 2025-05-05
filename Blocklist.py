from queue import Queue
import base
import random
import linecache
import os
import numpy as np
import time
import shutil
upper_N:int = base.N
n:int = upper_N.bit_length() - 1
m:int = base.m
len_prefix: int = n // 2
len_suffix: int = n - n // 2

def expand(key: str) -> [str]:
    indexes = []
    for i in range(2**len_prefix):
        ki: str = hex(i)[2:] + key
        h: str = base.Hash(ki, base.sha256)
        index: int = (int(h[0:8], 16) >> (32-n))
        indexes.append(index)
    return indexes

def HD(a,b,c):
    return np.random.hypergeometric(b, a-b, c)


class Client:
    def __init__(self, FolderName: str = "Blocklist_Hints"):
        self.HintsNumber = 2 ** len_suffix * n
        self.HintSize = 2 ** len_prefix
        self.FolderName = FolderName
        try:
            os.makedirs(FolderName, exist_ok=False)  # 创建文件夹
        except FileExistsError:
            pass  # 如果文件夹已存在，则忽略错误

    def FindHints(self, index: int) -> [[str, str]]:
        candidates = []
        # 遍历文件夹中的所有文件
        for filename in os.listdir(self.FolderName):
            key: str = filename
            for i in range(self.HintSize):
                ki: str = hex(i)[2:] + key
                h: str = base.Hash(ki, base.sha256)
                if index == (int(h[0:8], 16) >> (32-n)):
                    with open(self.FolderName+"/"+filename, "r") as f:
                        parity = f.readline()
                    candidates.append([key, parity])
                    break
        return candidates

    def OnlineQuery(self, index: int) -> [[str], [str], str, str, str]:
        candidates = self.FindHints(index)
        key, parity = random.choice(candidates)
        # print(candidates)
        # print(key, parity)
        flag = True
        k = ""
        while flag:
            k: str = hex(random.randint(0, 2 ** 256))[2:]
            for i in range(2 ** len_prefix):
                ki: str = hex(i)[2:] + k
                h: str = base.Hash(ki, base.sha256)
                if (int(h[0:8], 16) >> (32 - n)) == index:
                    flag = False
                    break
        indexes1 = expand(key)
        indexes2 = expand(k)
        # print(indexes1)
        # print(indexes2)
        indexes1.remove(index)
        indexes2.remove(index)
        # print(indexes1)
        # print(indexes2)
        return indexes1, indexes2, key, parity, k

    def OnlineRecovery(self, parity1:str, parity2:str, key: str, parity: str, k: str):
        ans = hex((int(parity1, 16) ^ int(parity, 16)))[2:]
        new_parity = hex((int(parity2, 16) ^ int(ans, 16)))[2:]
        # 修改 client 的 Hints
        os.remove(self.FolderName + "/" + key)
        filename: str = os.path.join(self.FolderName, k)
        with open(filename, 'w') as f:
            f.write(new_parity)
        # print(key)
        # print(k, new_parity)
        return ans

class Server:
    def __init__(self, filename:str = 'server.txt'):
        self.filename = filename
        try:
            with open(filename, 'x'):
                pass  # 不进行任何读写操作，只需创建文件
        except FileExistsError:
            pass
        return


    def FindParity(self, key:str) -> str:
        parity: str = "0"
        indexes = expand(key)
        for index in indexes:
            data = linecache.getline(self.filename, index+1)
            parity = hex((int(parity, 16) ^ int(data, 16)))[2:]
        return parity

    def OnlineAnswer(self, indexes:list[int]) -> [str]:
        parity: str = "0"
        for _in1 in indexes:
            data = linecache.getline(self.filename, _in1 + 1)
            parity = hex((int(parity, 16) ^ int(data, 16)))[2:]
        return parity

    def Add(self, myData=None):
        if myData is None:
            myData = base.add_entry(self.filename, num_entries=2**len_suffix)
            return myData
        base.add_entry(self.filename, len(myData), myData)
        return myData
    
    def AddKey(self, key, parity, w, LenAddedData):
        global upper_N
        indexes = expand(key)
        hintsize = len(indexes)
        k1: str = hex(random.randint(0, 2 ** 256))[2:]
        k2: str = hex(random.randint(0, 2 ** 256))[2:]
        new_parity = parity
        for i in range(w):
            ki: str = hex(i)[2:] + k1
            h: str = base.Hash(ki, base.sha256)
            offset = int(h[0:8], 16) % hintsize
            index = indexes[offset]
            indexes[offset] = indexes[-1]
            hintsize -= 1
            data = linecache.getline(self.filename, index + 1)           
            new_parity = hex((int(new_parity, 16) ^ int(data, 16)))[2:]
        for i in range(w):
            ki: str = hex(i)[2:] + k2
            h: str = base.Hash(ki, base.sha256)
            index = int(h[0:8],16) % LenAddedData + upper_N
            data = linecache.getline(self.filename, index + 1)
            # print(index, data)
            new_parity = hex((int(new_parity, 16) ^ int(data, 16)))[2:] 
        return [key, k1, k2], new_parity

        


def offline(c:Client, s:Server):
    #for _ in range(c.HintsNumber):
    #     k: str = hex(random.randint(0, 2 ** 256))[2:]
    #     # client send k to server2
    #     parity: str = s.FindParity(k)
    #     # server2 send parity to client
    #     filename: str = os.path.join(c.FolderName, k)
    #     with open(filename, 'w') as f:
    #         f.write(parity)
    start = time.time()
    klist = []
    for _ in range(c.HintsNumber):
        k: str = hex(random.randint(0, 2 ** 256))[2:]
        klist.append(k)
    end = time.time()
    clienttime1 = end-start
    uploadsize = base.getdatasize(klist)
        # client send k to server2
    start = time.time()
    paritylist = []
    for k in klist:
        parity: str = s.FindParity(k)
        paritylist.append(parity)
    end = time.time()
    servertime = end-start
        # server2 send parity to client
    downloadsize = base.getdatasize(paritylist)
    start = time.time()
    for i in range(c.HintsNumber):
        filename: str = os.path.join(c.FolderName, klist[i])
        with open(filename, 'w') as f:
            f.write(paritylist[i])
    end = time.time()
    clienttime2 = end-start
    clienttime = clienttime1+clienttime2
    return clienttime, servertime, uploadsize, downloadsize
    

def online(c:Client, s1:Server, s2:Server, index:int):
    start = time.time()
    indexes1, indexes2, key, parity, k = c.OnlineQuery(index)
    end = time.time()
    clienttime1 = end-start
    # indexes1 send to server1, indexes2 send to server2
    uploadsize = base.getdatasize(indexes1)+base.getdatasize(indexes2)
    start = time.time()
    parity1: str = s1.OnlineAnswer(indexes1)
    parity2: str = s2.OnlineAnswer(indexes2)
    end = time.time()
    servertime = (end-start)/2
    # send parity1 and parity2 to client
    downloadsize = base.getdatasize(parity1)+base.getdatasize(parity2)
    start = time.time()
    ans = c.OnlineRecovery(parity1, parity2, key,parity,k)
    end = time.time()
    clienttime2 = end-start
    return ans, clienttime1+clienttime2, servertime, uploadsize, downloadsize

def Add(c:Client, s:Server, myData=None):
    myData = s.Add()
    keyparitylist = []
    for filename in os.listdir(c.FolderName):
        key: str = filename
        with open(c.FolderName+"/"+filename, "r") as f:
            parity = f.readline()
        keyparitylist.append((key, parity))
    uploadsize = base.getdatasize(keyparitylist)
    # print(key, parity, base.getdatasize((key,parity)))
    start = time.time()
    newkeyparitylist = []
    for filename in os.listdir(c.FolderName):
        key: str = filename
        with open(c.FolderName+"/"+filename, "r") as f:
            parity = f.readline()
        w = HD(upper_N+len(myData), len(myData), 2**len_prefix)
        new_key, new_parity = s.AddKey(key, parity, w, len(myData))
        new_key.append(w)
        newkeyparitylist.append((new_key, new_parity))
    end = time.time()
    # print(new_key, new_parity, base.getdatasize((new_key,new_parity)))
    servertime = end-start
    downloadsize = base.getdatasize(newkeyparitylist)
    start = time.time()
    for filename in os.listdir(c.FolderName):
        with open(c.FolderName+"/"+filename, "w") as f:
            f.write(new_parity+'\n')
            f.write(str(new_key))
    end = time.time()
    clienttime = end-start
    return clienttime, servertime, uploadsize, downloadsize



if __name__ == "__main__":
    DEBUG = 0
    offlinetest = 1
    onlinetest = 1
    addtest = 1
    shutil.rmtree("Blocklist_Hints")
    os.mkdir("Blocklist_Hints")
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
            shutil.rmtree("Blocklist_Hints")
            os.mkdir("Blocklist_Hints")
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
        shutil.rmtree("Blocklist_Hints")
        os.mkdir("Blocklist_Hints")
    
    if addtest:
        offline(client,server2)
        clienttime, servertime, uploadsize, downloadsize = Add(client, server2)
        print(clienttime, servertime, uploadsize, downloadsize)
        if DEBUG == 0:
            with open(aimtxt, "a+") as f:
                f.write(str(clienttime*1000)+" "+str(servertime*1000)+" "+str(uploadsize)+" "+str(downloadsize)+"\n")
        shutil.rmtree("Blocklist_Hints")
        os.mkdir("Blocklist_Hints")

    # for i in range(N):
    #     print(i, len(client.FindHints(i)))
    # for i in range(100):
    #     print(online(client, server1, server2, 34))
    # Add(client, server2)

# 离线计算开销，离线通信开销
# 在线计算开销，计算通信开销
# 更改计算开销，计算通信开销