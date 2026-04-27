import requests, time, json

hhstu_session = input("输入session：")

session = requests.Session()
url = "https://dcca.hhstu.edu.cn/oauth/auth/oauth/authorize"
params = {
    "response_type": "code",
    "client_id": "1654673625133109211",
    "redirect_uri": "https://dcca.hhstu.edu.cn/api/open/wap/oauth2/callback",
    "scope": "FOO"
}
headers1 = {
    "Host": "dcca.hhstu.edu.cn",
    "Cookie": f"SESSION={hhstu_session}; useNameTemp=",  # 在这里填入你的学号
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept": "*/*",
    "Referer": "https://dcca.hhstu.edu.cn/wap/?v=2.2.2",
    "Accept-Encoding": "gzip, deflate",
    "Priority": "u=0, i",
    "Connection": "keep-alive"
}

try:
    response = session.get("https://dcca.hhstu.edu.cn/oauth/auth/oauth/authorize", params = {
        "response_type": "code",
        "client_id": "1654673625133109211",
        "redirect_uri": "https://dcca.hhstu.edu.cn/api/open/wap/oauth2/callback",
        "scope": "FOO"
    }, headers = headers1, allow_redirects = False)
    response.raise_for_status()

    response = session.get(response.headers['Location'], headers = headers1, allow_redirects = False)
    response.raise_for_status()
    
    key = response.headers['Location'].split("key=")[1]
    print("获取key：" + key)

    response = session.post("https://dcca.hhstu.edu.cn/api/wap/login/oauth2", headers = headers1, json = {"key": key})
    response.raise_for_status()

    token = response.json()["data"]["token"]
    print("获取token：" + token)
    headers1["Authorization"] = token

    response = session.post("https://dcca.hhstu.edu.cn/api/wap/course/schedule", headers = headers1, json = {"diff": 0, "typeStr": "courseEdit"})
    response.raise_for_status()
    response = response.json()["data"]["courseWeekVos"]

    print("------获取课程ID------")
    used_course_id = []
    max_roll_call_id = 0
    course_id = 0
    for courses in response:
        # print("周" + courses["wek"])
        for course in courses["dayTimeTables"]:
            course_id = course["courseId"]
            course_name = course["courseName"]
            if course_id and (course_id not in used_course_id):
                used_course_id.append(course_id)
                print(f"{course_name} - {course_id}")

                response = session.post("https://dcca.hhstu.edu.cn/api/wap/course/student/attendance", headers = headers1, json = {"courseId": course_id, "current": 1, "pageSize": 1})
                response.raise_for_status()
                try:
                    roll_call_id = response.json()["data"]["content"][0]["rollCallId"]
                    if roll_call_id > max_roll_call_id:
                        max_roll_call_id = roll_call_id
                except:
                    pass

    print("------------------")

    input_course_id = int(input("输入课程ID："))

    low = max_roll_call_id - 1
    high = max_roll_call_id + 5000

    print(f"最近一次点名会话：{max_roll_call_id}，折半查找区间 [{low}, {high}]")

    last_success_id = -1
    while low <= high:
        mid = (low + high) // 2
        print(f"测试 {mid}...", end="")

        response = session.post(
            "https://dcca.hhstu.edu.cn/api/roll/course/rollCallRefresh",
            headers=headers1,
            json={"rollCallId": mid, "courseId": input_course_id}
        )

        response.raise_for_status()
        response = response.json()
        success = response["success"]

        if success:
            print("True")
            last_success_id = mid
            low = mid + 1
        else:
            print("False")
            high = mid - 1

    print(f"最后一次点名会话：{last_success_id}")

    last_success_id += 1
    listen = False
    while(1):
        if not listen:
            print(f"开始监听 {last_success_id}...",end="", flush=True)
            listen = True
        else:
            print(".",end="", flush=True)

        response = session.post(
            "https://dcca.hhstu.edu.cn/api/roll/course/rollCallRefresh",
            headers=headers1,
            json={"rollCallId": last_success_id, "courseId": input_course_id}
        )
        response.raise_for_status()
        response = response.json()

        if response["success"]:
            find = False
            for student in response["data"]["list"]:
                if student["studentUsername"] == "":  # 在这里填入你的学号
                    find = True
            if not find:
                print(f"未找到指定学生", flush=True)
            else:
                print("找到", flush=True)
                break
            last_success_id += 1
            listen = False

        time.sleep(0.5)

    code = response["data"]["code"]
    print(f"获取点名码：{code}，等待10秒进行点名", flush=True)

    time.sleep(10)

    response = session.post("https://dcca.hhstu.edu.cn/api/roll/course/signin", headers = headers1, json = {"code":code,"longitude":"","latitude":""})
    response.raise_for_status()
    response = response.json()

    if response["success"]:
        print("点名成功")
    else:
        print(f"点名失败：{response["message"]}")
    
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    session.close()

