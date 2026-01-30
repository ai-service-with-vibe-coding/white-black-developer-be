# 레벨 1 테스트 코드 - 최악의 코드 (45점 미만 목표)
# 특징: 함수 없음, 깊은 중첩, 긴 라인, 보안 취약점, 문서화 없음

import os
import subprocess
import pickle

data = input("Enter data: ")
cmd = "echo " + data
result = subprocess.call(cmd, shell=True)
user_input = input("Enter filename: ")
with open(user_input, "r") as f:
    content = f.read()
query = "SELECT * FROM users WHERE id = " + input("Enter ID: ")
password = "admin123"
secret_key = "sk-1234567890abcdef"
api_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
eval(input("Enter code to execute: "))
exec(compile(input("More code: "), "<string>", "exec"))
pickle.loads(open("data.pkl", "rb").read())
x = 1
if x > 0:
    if x > 0:
        if x > 0:
            if x > 0:
                if x > 0:
                    if x > 0:
                        if x > 0:
                            if x > 0:
                                print("deeply nested code with no purpose at all and this line is extremely long to trigger the line length penalty in the scoring system which should reduce quality score significantly")
y = 2
if y > 0:
    if y > 0:
        if y > 0:
            if y > 0:
                if y > 0:
                    if y > 0:
                        print("another deeply nested block that serves no real purpose and makes the code completely unreadable and unmaintainable for any developer who tries to understand it later on in the future when debugging issues")
z = 3
if z > 0:
    if z > 0:
        if z > 0:
            if z > 0:
                if z > 0:
                    print("yet another deeply nested block of code that demonstrates terrible coding practices and should definitely trigger low quality scores in any reasonable code review system that exists today")
a = 4
if a > 0:
    if a > 0:
        if a > 0:
            if a > 0:
                if a > 0:
                    if a > 0:
                        if a > 0:
                            print("maximum nesting level reached here and this is definitely a code smell that should be refactored immediately but we are intentionally writing bad code for testing purposes only so please ignore this warning")
b = 5
if b > 0:
    if b > 0:
        if b > 0:
            if b > 0:
                if b > 0:
                    print("this code has no functions no classes no documentation no error handling and violates every single best practice that exists in software development which is exactly what we want for testing level 1 scoring")
c = 6
if c > 0:
    if c > 0:
        if c > 0:
            if c > 0:
                print("continuing with more terrible code patterns that should definitely reduce the overall quality score to below 45 points which is the threshold for level 1 rating in our scoring system implementation today")
d = 7
if d > 0:
    if d > 0:
        if d > 0:
            if d > 0:
                if d > 0:
                    if d > 0:
                        print("extremely long line of code that goes way beyond any reasonable limit and should definitely trigger penalties in the line length evaluation part of our quality scoring algorithm implementation here today now")
e = 8
if e > 0:
    if e > 0:
        if e > 0:
            if e > 0:
                if e > 0:
                    print("more nested code with security vulnerabilities like hardcoded credentials and command injection and sql injection and path traversal and code execution all in one terrible file designed to fail quality checks")
subprocess.Popen(input("command: "), shell=True)
os.system(input("another command: "))
__import__(input("module: "))
globals()[input("key: ")] = input("value: ")
