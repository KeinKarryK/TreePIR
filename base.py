import hashlib
import os
import random
import shutil
import linecache
import math

bound: int = 20
N:int = 2**bound # 数据库大小
m:int = 8*32 # parity的长度
aimtxt = "cost"+str(bound)+".txt"
testdata = str(bound)+"_backup.txt"
def DatabaseGen(filename):
    hex_length = m // 4  # 计算十六进制字符长度
    with open(filename, "w") as f:
        # 生成m位随机数 (0 到 2^m-1)
        num = random.getrandbits(m)
        # 转换为带前导零的十六进制字符串
        hex_str = f"{num:0{hex_length}x}"  # 大写X表示大写十六进制
        # 写入文件
        f.write(hex_str)
        for _ in range(N-1):
            # 生成m位随机数 (0 到 2^m-1)
            num = random.getrandbits(m)
            # 转换为带前导零的十六进制字符串
            hex_str = f"{num:0{hex_length}x}"  # 大写X表示大写十六进制
            # 写入文件

            f.write("\n"+hex_str)

def add_entry(filename, num_entries=1, entries=None):
    """添加新条目到数据库"""
    hex_length = m // 4
    myData = []
    if entries is None:
        with open(filename, "a+") as f:
            for _ in range(num_entries):
                num = random.getrandbits(m)
                hex_str = f"{num:0{hex_length}x}"
                myData.append(hex_str)
                f.write("\n"+ hex_str)
            linecache.clearcache()
        return myData
    else:
        with open(filename, "a") as f:
            for i in range(num_entries):
                num = entries[i]
                hex_str = f"{num:0{hex_length}x}"
                f.write( "\n"+ hex_str)
            linecache.clearcache()
        return entries



def delete_entry(filename, line_number):
    """按行号删除指定条目"""
    # 读取所有行
    with open(filename, "r") as f:
        lines = f.readlines()

    # 验证行号有效性
    if line_number < 1 or line_number > len(lines):
        print(f"无效行号，有效范围: 1-{len(lines)}")
        return

    # 删除指定行并重写文件
    del lines[line_number - 1]
    with open(filename, "w") as f:
        f.writelines(lines)


def modify_entry(filename, line_number):
    """修改指定行号的条目"""
    hex_length = m // 4

    # 读取所有行
    with open(filename, "r") as f:
        lines = f.readlines()

    # 验证行号有效性
    if line_number < 1 or line_number > len(lines):
        print(f"无效行号，有效范围: 1-{len(lines)}")
        return

    # 生成新条目并替换
    num = random.getrandbits(m)
    new_hex = f"{num:0{hex_length}X}"
    lines[line_number - 1] = new_hex + "\n"

    # 重写文件
    with open(filename, "w") as f:
        f.writelines(lines)


def getData(src_path="16_backup.txt", dst_dir="./", new_name="server"):
    """
    复制并重命名文本文件

    :param src_path: 源文件路径（例如 "data/original.txt"）
    :param dst_dir:  目标目录（例如 "backup"）
    :param new_name: 新文件名（不含扩展名，例如 "backup_2023"）
    """
    # 确保目标目录存在
    os.makedirs(dst_dir, exist_ok=True)
    # 构建目标路径（保留 .txt 扩展名）
    dst_path = os.path.join(dst_dir, f"{new_name}.txt")
    # 复制文件（保留元数据）
    shutil.copy2(src_path, dst_path)
    # print(f"文件已复制并重命名为：{dst_path}")

def Hash(x:hex, function)-> hex:
    return function(x)

def sha256(x:str)->str:
    hash_object = hashlib.sha256()
    hash_object.update(x.encode())
    return hash_object.hexdigest()

def getdatasize(data_list):
    return 0
    if isinstance(data_list, int):
            # 假设存储为4字节int32（根据实际需求可调整）
        return 4
    elif isinstance(data_list, float):
            # 双精度浮点数固定8字节
        return 8
    elif isinstance(data_list, str):
        return math.ceil(len(data_list.encode('utf-8'))/2)
    elif isinstance(data_list, bytes):
            # 直接计算字节对象长度
        return len(data_list)
    total_bytes = 0
    for item in data_list:
        total_bytes += getdatasize(item)
    return total_bytes

if __name__ == "__main__":
    DatabaseGen(testdata)
    # getData()
