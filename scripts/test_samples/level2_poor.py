# 레벨 2 테스트 코드 - 부족한 코드 (45-60점 목표)
# 특징: 함수 2개, 중간 중첩, 문서화 부족

import os


def process_data(data):
    """데이터 처리"""
    result = []
    for item in data:
        if item > 0:
            if item > 10:
                result.append(item * 2)
            else:
                result.append(item)
        else:
            result.append(-1)
    return result


def calculate_sum(numbers):
    """합계 계산"""
    total = 0
    for n in numbers:
        total += n
    return total


x = 1
y = 2
z = 3

user_input = input("Enter something: ")
filename = user_input
with open(filename, "r") as file:
    content = file.read()

password = "weakpassword"

if x > 0:
    if y > 0:
        if z > 0:
            print("nested")
        else:
            print("level 2")
    else:
        print("level 1")
else:
    print("level 0")

data = [1, 2, 3, 4, 5]
result = process_data(data)
total = calculate_sum(result)
print(result)
print(total)

config = {"key": "value", "password": "admin123"}
