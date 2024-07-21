# 判断两个区间有没有交集
def isInter(a1, a2):
    s1, e1 = a1
    s2, e2 = a2
    if s1 == s2:
        return True
    elif s1<s2:
        return e1>=s2
    else:
        # s1>s2
        return e2>=s1

# 算法入口
def result():
    # used 保存被占用的内存 [起始地址，结束地址]，初始时有一个[100,101]作为尾边界限定
    used =[[100, 101]] # 题目说了最大就100，就是0-99嘛
    for key ,val in cmds:
        # 申请内存
        if key == "REQUEST":
            # 当指令为 REQUEST 时，对应值为要申请的内存的大小，即 size
            size = int(val)
            # 开始位置从0 开始检查，有没有可用的空间。
            start = 0
            flag = True
            for i in range(len(used)):
                end = start+size-1 # [start, end] 都是闭区间，所以
                # 需要申请的区间
                ran = [start, end]
                # 检查要申请的内存区间和已占有的内存区间是否交叉
                if not isInter(used[i], ran):
                    # 若不存在交叉，则将申请区间加入 used 中
                    used.insert(i, ran)
                    flag = False
                    # 并打印此时申请区间的起始位置
                    print(start)
                    break
                else:
                    # 若存在交叉，则将变更要申请的内存区间的起始位置
                    start = used[i][1] + 1 # 记得加1，不然还是重叠。
            # 一旦申请到内存，那么 flag 就会被赋值为 false，否则就保持 true，意味着没申请到内存，则打印error
            if flag:
                # 搞了一圈了，还没申请到内存
                print("error")
        # 释放内存。
        else:
            # key == "REQUEST" 当指令为 RELEASE 时，值为要释放内存的起始地址 addr
            addr = int(val)
            # 那我就要去找首地址对应的区间呀
            flag = True
            for i in range(len(used)):
                # 到已占有内存中找起始位置是 addr 的，找到则将该区间从 used 中删除，表示解除占用
                if used[i][0] == addr:
                    used.pop(i) # 这个厉害。我一般用的多的是pop(0)
                    flag = False
                    break
            if flag:
                # 找了一圈没找到。只能返回error了
                print("error")
'''
2
REQUEST=10
REQUEST=20
RELEASE=0
'''
n = int(input())
cmds = [input().split("=") for i in range(n)]
print(n)
print(cmds)
result()