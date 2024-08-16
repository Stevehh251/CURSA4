import re

answer = re.findall(r'(\/\w+|\[\d+\])', "/div/div[3]/a", )
print(answer)
print(list(answer))  