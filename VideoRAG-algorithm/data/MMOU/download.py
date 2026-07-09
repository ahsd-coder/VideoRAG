'''
下载数据
from datasets import load_dataset

mmou = load_dataset("nvidia/MMOU")["train"]
test = load_dataset("nvidia/MMOU", "test", split="test")

mmou.save_to_disk("./train")
test.save_to_disk("./test")
'''

"""
Arrow格式牺牲了“人类可读性”换取了“程序读取效率”，这是设计上的权衡，不是bug,
只能通过代码去读，不能指望编辑器直接打开看明文
"""

# 加载数据
from datasets import load_from_disk

mmou = load_from_disk("./train")
test = load_from_disk("./test")

# for element in mmou:
#     print(element)
#     break

# 一次性把整个数据集导出成JSON Lines格式
mmou.to_json("./train/train.json")
test.to_json("./test/test.json")

