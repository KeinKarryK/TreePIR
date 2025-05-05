from queue import Queue
import base
import random
import queue
import linecache
import os
import time
import shutil

# 类似blocklist的分chunk版本
state_N:int = base.N
upper_N:int = 2*base.N
n:int = upper_N.bit_length() - 1
m:int = base.m
len_prefix:int = n - n//2
len_suffix:int = n//2
C2S:Queue[bytes] = queue.Queue()
S2C:Queue[bytes] = queue.Queue()

class Client:
    def __init__(self, FolderName:str = "Chunk_Blocklist_Client_Hints"):
        self.HintsNumber = 2 ** len_suffix * n  # 假设 len_suffix 和 n 已经定义
        self.FolderName = FolderName
        try:
            os.makedirs(FolderName, exist_ok=False)  # 创建文件夹
        except FileExistsError:
            pass  # 如果文件夹已存在，则忽略错误

    def FindHints(self, index:int) -> [[str, str]]:
        candidates = []
        prefix: str = hex(index >> len_suffix)[2:]
        suffix: str = hex(index & ((1 << len_suffix) - 1))[2:]
        # 遍历文件夹中的所有文件
        for filename in os.listdir(self.FolderName):
            key: str = filename
            ki: str = prefix + key
            h: str = base.Hash(ki, base.sha256)
            if suffix == hex((int(h[0:8], 16) >> (32 - len_suffix)))[2:]:
                with open(self.FolderName+"/"+filename, "r") as f:
                    parity = f.readline()
                candidates.append([key, parity])
        return candidates


    def OnlineQuery(self,index:int) -> [[str], [str], str, str, str]:
        prefix: str = hex(index >> len_suffix)[2:]
        suffix: str = hex(index & ((1 << len_suffix) - 1))[2:]
        candidates = self.FindHints(index)
        key, parity = random.choice(candidates)
        # print(candidates)
        # print(key, parity)
        while True:
            k: str = hex(random.randint(0, 2 ** 256))[2:]
            ki: str = prefix + k
            h: str = base.Hash(ki, base.sha256)
            if suffix == hex((int(h[0:8], 16) >> (32 - len_suffix)))[2:]:
                break
        indexes1 = expand(key)
        indexes2 = expand(k)
        # print(indexes1)
        # print(indexes2)
        r1 = ((index >> len_suffix) << len_suffix) + (random.randint(0, 2 ** len_suffix))
        r2 = ((index >> len_suffix) << len_suffix) + (random.randint(0, 2 ** len_suffix))
        # print(r1, r2)
        indexes1[index >> len_suffix] = r1
        indexes2[index >> len_suffix] = r2
        # print(indexes1)
        # print(indexes2)
        return indexes1[0:2**(len_prefix-1)], indexes2[0:2**(len_prefix-1)], key, parity, k

    def OnlineRecovery(self, index:int, DB1:list[str], DB2:list[str], key:str, parity:str, k:str):
        parity1: str = "0"
        # print(index, len_suffix)
        # print(index>>len_suffix)
        for i in range(len(DB1)):
            if i == index >> len_suffix:
                continue
            parity1 = hex((int(parity1, 16) ^ int(DB1[i], 16)))[2:]
            # print(indexes1[i], end=' ')
        ans: str = hex(int(parity1, 16) ^ int(parity, 16))[2:]

        parity2: str = "0"
        for i in range(len(DB1)):
            if i == index >> len_suffix:
                continue
            parity2 = hex((int(parity2, 16) ^ int(DB2[i], 16)))[2:]
        new_parity = hex((int(parity2, 16) ^ int(ans, 16)))[2:]
        # 修改 client 的 Hints
        os.remove(self.FolderName + "/" + key)
        filename: str = os.path.join(self.FolderName, k)
        with open(filename, 'w') as f:
            f.write(new_parity)
        # print(key)
        # print(k, new_parity)
        return ans

    def Add(self, myData: list):
        if state_N + 2**len_suffix > upper_N:
            print("upper_bound!")
            return
        prefix = state_N >> len_suffix
        hex_prefix: str = hex(prefix)[2:].zfill(len_prefix)
        for filename in os.listdir(self.FolderName):
            key: str = filename
            tmp_suffix: int = (int(base.Hash(str(prefix)+key, base.sha256)[0:8], 16)>>(32 - len_suffix))
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


    def FindParity(self, key:str) -> str:
        parity: str = "0"
        indexes = expand(key)
        for index in indexes:
            if index+1 > state_N:
                data = "0"
            else:
                data = linecache.getline(self.filename, index+1)
            parity = hex((int(parity, 16) ^ int(data, 16)))[2:]
        return parity

    def OnlineAnswer(self, indexes:list[int]) -> [str]:
        DB = []
        for _in1 in indexes:
            if _in1+1 > state_N:
                data = "0"
            else:
                data = linecache.getline(self.filename, _in1 + 1)
            DB.append(data)
        return DB

    def Add(self, myData=None):
        if state_N + 2 ** len_suffix > upper_N:
            return
        if myData is None:
            myData = base.add_entry(self.filename, num_entries=2**len_suffix)
            return myData
        base.add_entry(self.filename, len(myData), myData)
        return myData

def expand(key: str) -> [str]:
    indexes = []
    for i in range(2**len_prefix):
        ki: str = hex(i)[2:] + key
        h: str = base.Hash(ki, base.sha256)
        index: int = (i << len_suffix) + (int(h[0:8], 16) >> (32 - len_suffix))
        indexes.append(index)
    return indexes

def offline(c:Client, s:Server):
    start = time.time()
    klist = []
    for _ in range(c.HintsNumber):
        k: str = hex(random.randint(0, 2 ** 256))[2:]
        klist.append(k)
    end = time.time()
    clienttime1 = end-start
    uploadsize = base.getdatasize(klist)
    # send klist to server2
    start = time.time()
    paritylist = []
    for k in klist:
        parity: str = s.FindParity(k)
        paritylist.append(parity)   
    end = time.time()
    servertime = end-start
    downloadsize = base.getdatasize(paritylist)
    start = time.time()
    for i in range(c.HintsNumber):
        filename: str = os.path.join(c.FolderName, klist[i])
        with open(filename, 'w') as f:
            f.write(paritylist[i])
    end=time.time()
    clienttime2 = end-start
    return clienttime1+clienttime2, servertime, uploadsize, downloadsize

def online(c:Client, s1:Server, s2:Server, index:int):
    start = time.time()
    indexes1, indexes2, key, parity, k = c.OnlineQuery(index)
    end = time.time()
    clienttime1 = end-start
    uploadsize = base.getdatasize(indexes1)+base.getdatasize(indexes2)
    # indexes1 send to server1, indexes2 send to server2
    start = time.time()
    DB1 = s1.OnlineAnswer(indexes1)
    DB2 = s2.OnlineAnswer(indexes2)
    end=time.time()
    servertime = (end-start)/2
    downloadsize = base.getdatasize(DB1)+base.getdatasize(DB2)
    # send DB1 and DB2 to client
    start = time.time()
    ans = c.OnlineRecovery(index, DB1, DB2, key, parity, k)
    end = time.time()
    clienttime2 = end-start
    return ans, clienttime1+clienttime2, servertime, uploadsize, downloadsize

def Add(c:Client, s: Server, myData=None):
    start = time.time()
    myData = s.Add(myData)
    end = time.time()
    servertime = end-start
    start = time.time()
    c.Add(myData)
    end = time.time()
    clienttime = end-start
    return clienttime, servertime, 0, base.getdatasize(myData)

if __name__ == "__main__":
    DEBUG = 0
    offlinetest = 1
    onlinetest = 1
    addtest = 1
    shutil.rmtree("Chunk_Blocklist_Client_Hints")
    os.mkdir("Chunk_Blocklist_Client_Hints")
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
            shutil.rmtree("Chunk_Blocklist_Client_Hints")
            os.mkdir("Chunk_Blocklist_Client_Hints")
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
        shutil.rmtree("Chunk_Blocklist_Client_Hints")
        os.mkdir("Chunk_Blocklist_Client_Hints")
    
    if addtest:
        offline(client,server2)
        clienttime, servertime, uploadsize, downloadsize = Add(client, server2)
        print(clienttime, servertime, uploadsize, downloadsize)
        if DEBUG == 0:
            with open(aimtxt, "a+") as f:
                f.write(str(clienttime*1000)+" "+str(servertime*1000)+" "+str(uploadsize)+" "+str(downloadsize)+"\n")
        shutil.rmtree("Chunk_Blocklist_Client_Hints")
        os.mkdir("Chunk_Blocklist_Client_Hints")
