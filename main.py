import getpass
import json
import random
import time
import os
import traceback
from threading import Thread

import requests
import base64

import win32ui
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

from utils.Login import SSO, Login
from utils.tempzip import compress

sso = SSO({})
PATH = os.path.dirname(__file__) + "/downloads/"
PATH_CONF = os.path.dirname(__file__) + "/utils/conf.json"
if not os.path.exists(PATH):
    os.mkdir(PATH)
SIZE = ["B", "KB", "MB", "GB"]

class Node:
    def __init__(self, id: int, name: str, is_dir: bool, filesize: int, children: dict, parent):
        self.id = id
        self.name = name
        self.is_dir = is_dir
        self.filesize = filesize
        self.children = children
        self.parent = parent
        self.inited = False

    def __repr__(self):
        if self.parent is None:
            return ""
        else:
            return f"{self.parent}/{self.name}"

    def getPath(self):
        if self.parent is None:
            return ""
        else:
            return f"{self.parent.getPath()}/{self.name}"

    def init(self):
        dirs = getDirs(self)
        files = getFiles(self)
        self.children = dict()
        self.children.update(dirs)
        self.children.update(files)
        self.inited = True

    def load(self):
        self.init()
        for i in self.children.values():
            if i.is_dir:
                # print(i.name, end=" | ")
                i.load()

    def download(self, link:bool=False):
        if self.is_dir:
            return "文件夹无法下载"
        else:
            try:
                url = f"http://lms.eurasia.edu/api/uploads/{self.id}/blob"
                res = sso.get(url, allow_redirects=False)
                location = res.headers.get("Location", None)
                if location:
                    if link:
                        return location
                    res = sso.get(location, stream=True)
                    totalsize = int(res.headers["Content-Length"])
                    with open(PATH + self.name, "wb") as f:
                        for cont in res.iter_content(10240):
                            progress = round(((f.tell()+len(cont)) / totalsize) * 100, 2)
                            print(f"\r Downloading...  {progress}%", end="", flush=True)
                            f.write(cont)
                    return f" 下载完成。"
            except Exception as e:
                return f" 下载失败！"


def addNode(uploads: list, nodes: dict, parent: Node):
    for i in uploads:
        nodes[i["id"]] = Node(
            id=i["id"],
            name=i["name"],
            is_dir=i["is_folder"],
            filesize=i["size"],
            children=dict(),
            parent=parent
        )
    return nodes


def getDirs(node: Node) -> dict:
    '''
    获取文件夹下的所有文件夹
    '''
    children = dict()
    url = "http://lms.eurasia.edu/api/user/resources"
    condition = {
        "keyword": "",
        "includeSlides": False,
        "limitTypes": ["folder"],
        "fileType": "all",
        "parentId": node.id,
        "sourceType": "MyResourcesFolder",
        "no-intercept": True
    }
    params = {
        "conditions": json.dumps(condition),
        "page": 1,
        "page_size": 100,
    }
    firstPage = sso.get(url, params=params)
    js_first = json.loads(firstPage.text)
    children = addNode(js_first["uploads"], children, node)
    for _ in range(js_first["pages"] - 1):
        params["page"] += 1
        page = sso.get(url, params=params)
        js = json.loads(page.text)
        children = addNode(js["uploads"], children, node)
    return children


def getFiles(node: Node) -> dict:
    '''
    获取文件夹下的所有文件
    '''
    children = dict()
    url = "http://lms.eurasia.edu/api/user/resources"
    condition = {
        "keyword": "",
        "includeSlides": False,
        "limitTypes": ["file", "video", "document", "image", "audio", "scorm", "evercam", "swf", "wmpkg", "link"],
        "fileType": "all",
        "parentId": node.id,
        "sourceType": "MyResourcesFile",
        "no-intercept": True
    }
    params = {
        "conditions": json.dumps(condition),
        "page": 1,
        "page_size": 100,
    }
    firstPage = sso.get(url, params=params)
    js_first = json.loads(firstPage.text)
    children = addNode(js_first["uploads"], children, node)
    for _ in range(js_first["pages"] - 1):
        params["page"] += 1
        page = sso.get(url, params=params)
        js = json.loads(page.text)
        children = addNode(js["uploads"], children, node)
    return children


def uplaodFile(filename, parentid):
    assert os.path.exists(filename)

    url = "http://lms.eurasia.edu/api/uploads"
    size = os.path.getsize(filename)
    data = {
        "name": os.path.basename(filename),
        "size": size,
        "parent_id": parentid,
        "is_scorm": False,
        "is_wmpkg": False,
        "source": "",
        "is_marked_attachment": False,
        "embed_material_type": ""
    }

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50"
    }
    res = sso.post(url, data=json.dumps(data), headers=headers)
    js = json.loads(res.text)

    upload_url = js["upload_url"]
    requests.options(upload_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50"
    }
    multipart = MultipartEncoder(
        fields={
            "file": (os.path.basename(filename), open(filename, "rb"), "application/octet-stream")
        },
        boundary="-----------------------------" + str(random.randint(1e28, 1e29 - 1))
    )
    def monitor(m):
        progress = round((m.bytes_read / m.len) * 100, 2)
        print(f"\r Uploading...  {progress}%({m.bytes_read}/{m.len})", end="", flush=True)

    multipartMonitor = MultipartEncoderMonitor(multipart, monitor)
    headers["Content-Type"] = multipartMonitor.content_type
    res = requests.put(upload_url, data=multipartMonitor, headers=headers)
    js: dict = json.loads(res.text)
    if js.__contains__("file_key"):
        return 1
    elif (js.__contains__("error")) & (js["error"] == "Invalid file type."):
        return 2
    else:
        raise Exception(res.text)


def getSize(bytesnum):
    size = int(bytesnum)
    for i in range(len(SIZE)):
        if size > 1024:
            size /= 1024
        else:
            break
    size = str(round(size, 2)) + SIZE[i]
    return size

class FS:
    def __init__(self):
        self.root = Node(id=0, name="root", is_dir=True, filesize=0, children=dict(), parent=None)
        self.now: Node = self.root
        # sso.get("http://lms.eurasia.edu/center/static/js/wg-apps.js")
        # self.root.init()
        Thread(target=self.root.load, daemon=True).start()
        # self.root.load()
        # print()
        sso.get("http://lms.eurasia.edu/center/api/users/20338209150460/apps-panel-settings")
        # sso.get("http://lms.eurasia.edu/center/api/users/20338209150460/permissions")
        print(sso.getCookies())

    def getIdByIndex(self, num):
        return tuple(self.now.children.items())[num][0]

    def ls(self):
        if not self.now.inited:
            print(f"{self.now.name} is initializing, wait for a sec...")
        while not self.now.inited:
            time.sleep(0.5)
        nodes = self.now.children.values()
        string = ""
        for i, node in enumerate(nodes):
            if node.is_dir:
                string += f"{i}. [D]{node.name} \n"
            else:
                size = getSize(int(node.filesize))
                # size = int(node.filesize)
                # for i in range(len(SIZE)):
                #     if size > 1024:
                #         size /= 1024
                #     else:
                #         break
                # size = str(round(size, 2)) + SIZE[i]
                string += f"{i}. {node.name} - [{size}]\n"
        return string

    def cd(self, name):
        cded = False
        try:
            name = int(name)
        except:
            pass
        if isinstance(name, int):
            self.cdid(self.getIdByIndex(name))
            cded = True
        elif isinstance(name, str):
            if name == "..":
                self.cdid("..")
                cded = True
            else:
                nodes = self.now.children.items()
                for i in nodes:
                    if i[1].name == name:
                        self.cdid(i[0])
                        cded = True
                        break
        if not cded:
            return "Wrong name"

    def cdid(self, _id):
        if (_id == "..") & (self.now.parent is not None):
            self.now: Node = self.now.parent
        elif isinstance(_id, int) and self.now.children[_id].is_dir:
            print(f"changed to {self.now.children[_id].name}")
            self.now: Node = self.now.children[_id]
        else:
            print("Wrong id input")
        if not self.now.inited:
            self.now.init()

    def _upload(self, filename):
        """
        上传文件
        """
        try:
            uploadStatus = uplaodFile(filename, self.now.id)
            if uploadStatus == 1:
                self.now.init()
                return "上传完成"
            elif uploadStatus == 2:
                print("格式不支持，正在压缩...")
                compressStatus = compress(filename)
                if (compressStatus != 0) & (compressStatus != 2):
                    print(compressStatus)
                    uploadStatus = uplaodFile(compressStatus, self.now.id)
                    if uploadStatus == 1:
                        self.now.init()
                        return "上传完成"
                    else:
                        return f"上传失败 - {uploadStatus}"
                else:
                    return f"压缩失败 - {compressStatus}"

        except Exception as e:
            traceback.print_exc()

    def upload(self, filename):
        size = os.path.getsize(filename)
        if (size / (1024**3)) > 1:
            size = getSize(size)
            print(f"文件大小为 {size} 超过1GB, 将会进行500MB分卷压缩")
            _id = self.mkdir(name=os.path.basename(filename))
            self.reload()
            self.cdid(_id=_id)
            filenames = compress(filename, "500M")
            for i in filenames:
                self._upload(i)
        else:
            self._upload(filename)

    def delete(self, num):
        fileid = self.getIdByIndex(num)
        url = f"http://lms.eurasia.edu/api/user/upload/{fileid}"
        print(url)
        res = sso.delete(url)
        js = json.loads(res.text)
        self.reload()
        return js["message"]

    def reload(self):
        self.now.init()

    def mkdir(self, name):
        url = "http://lms.eurasia.edu/api/uploads"
        data = {
            "is_folder": True,
            "name": name,
            "parent_id": self.now.id,
        }
        headers = {"Content-Type": "application/json;charset=UTF-8",}
        res = sso.post(url, data=json.dumps(data), headers=headers)
        # print(res.text)
        js = json.loads(res.text)
        if js.__contains__("error"):
            print(js)
        else:
            self.reload()
            return js["id"]


    def move(self, _ids: list, parentid: int):
        url = "http://lms.eurasia.edu/api/uploads/move"
        data = {
            "parent_id": parentid,
            "upload_ids": _ids,
        }
        headers = {"Content-Type": "application/json;charset=UTF-8",}
        res = sso.put(url, data=json.dumps(data), headers=headers)

        js = json.loads(res.text)
        print(js)

    def movecmd(self, _id: int):
        origin = self.now
        print(self.ls())
        while 1:
            cmd = input(">")
            if cmd == "drop":
                self.move([_id], self.now.id)
                break
            elif cmd == "exit":
                break
            else:
                try:
                    print(self.cd(cmd))
                except:
                    traceback.print_exc()
                print(self.ls())
        self.now = origin


def login():
    global sso

    if not os.path.exists(PATH_CONF):
        with open(PATH_CONF, "w") as f:
            f.write("{}")
    try:
        with open(PATH_CONF, "r") as f:
            js = json.loads(f.read())
    except Exception as e:
        print(e)
        with open(PATH_CONF, "w") as f:
            f.write("{}")
        raise Exception("文件内容有误，已重置内容，请重新启动")
    if not js.__contains__("username") or not js.__contains__("password"):
        print("账号密码不全，请重新填写")
        username = input("账号: ")
        password = getpass.getpass("密码: ")
    else:
        username = js["username"]
        password = base64.b64decode(js["password"].encode()).decode()

    while 1:
        try:
            login = Login(username, password)
            sso = login.login()
            time.sleep(1)
            break
        except Exception as e:
            traceback.print_exc()
            print("登陆失败，请重新输入账号密码")
            username = input("账号: ")
            password = getpass.getpass("密码: ")
    with open(PATH_CONF, "w") as f:
        f.write(json.dumps({"username": username, "password": base64.b64encode(password.encode()).decode()}))

class cmdSimulation:
    def __init__(self):
        fs_start = time.time()
        self.fs = FS()
        print(f"文件系统创建耗时: {time.time() - fs_start}")
        print(self.fs.ls())
        print(self.fs.now.getPath())

    def ls(self):
        print(self.fs.ls())

    def cd(self, cmd):
        try:
            cd_start = time.time()
            if cmd[-1] == "..":
                cd = cmd[-1]
                self.fs.cdid(cd)
            else:
                cd = " ".join(cmd[1:])
                self.fs.cd(cd)
            print(f"cd并获取新内容耗时: {time.time() - cd_start}")
        except:
            traceback.print_exc()

    def cdid(self, cmd):
        try:
            if cmd[-1] == "..":
                cdid = cmd[-1]
            else:
                cdid = self.fs.getIdByIndex(int(cmd[-1]))
            cd_start = time.time()
            self.fs.cdid(cdid)
            print(f"cd并获取新内容耗时: {time.time() - cd_start}")
        except:
            traceback.print_exc()

    def get(self, cmd, link=False):
        try:
            getid = self.fs.getIdByIndex(int(cmd[-1]))
            print(f"正在下载 - {self.fs.now.children[getid].name}")
            get_start = time.time()
            print(self.fs.now.children[getid].download(link=link))
            print(f"下载内容耗时: {time.time() - get_start}")
        except:
            traceback.print_exc()

    def put(self):
        try:
            fileDialog = win32ui.CreateFileDialog(True)
            fileDialog.SetOFNInitialDir(__file__)
            fileDialog.DoModal()
            filename = fileDialog.GetPathName()
            print(filename)
            upload_start = time.time()
            print(self.fs.upload(filename))
            print(f"上传内容耗时: {time.time() - upload_start}")
        except:
            traceback.print_exc()

    def reload(self):
        self.fs.reload()

    def rm(self, cmd):
        try:
            index = int(cmd[-1])
            print("正在删除文件名为:", self.fs.now.children[self.fs.getIdByIndex(index)].name)
            del_start = time.time()
            print(self.fs.delete(index))
            print(f"删除内容耗时: {time.time() - del_start}")
        except:
            traceback.print_exc()

    def move(self, cmd):
        try:
            _id = self.fs.getIdByIndex(int(cmd[-1]))
            print("正在移动文件:", self.fs.now.children[_id].name)
            move_start = time.time()
            self.fs.movecmd(_id)
            print(f"移动内容耗时: {time.time() - move_start}")
        except Exception as e:
            traceback.print_exc()

    def mkdir(self, cmd):
        try:
            name = " ".join(cmd[1:])
            mkdir_start = time.time()
            self.fs.mkdir(name)
            print(f"创建文件夹耗时: {time.time() - mkdir_start}")
        except:
            traceback.print_exc()


    def mainloop(self):
        while 1:
            cmd = input(">>>").split()
            match cmd[0]:
                case "ls":
                    self.ls()
                case "cd":
                    self.cd(cmd)
                case "cdid":
                    self.cdid(cmd)
                case "get":
                    self.get(cmd, link=False)
                case "getlink":
                    self.get(cmd, link=True)
                case "put":
                    self.put()
                case "reload":
                    self.reload()
                case "rm":
                    self.rm(cmd)
                case "move":
                    self.move(cmd)
                case "mkdir":
                    self.mkdir(cmd)

def main():
    login_start = time.time()
    login()
    print(f"登录耗时: {time.time() - login_start}")
    simulation =  cmdSimulation()
    simulation.mainloop()



if __name__ == "__main__":
    main()
