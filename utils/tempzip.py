import tempfile
import os
import traceback

# from Tools import ok, fatal

PATH = os.path.dirname(__file__) + "/../Temp"
if not os.path.exists(PATH):
    os.mkdir(PATH)

tmp=tempfile.mkdtemp(prefix='tmp',dir=PATH)


def _compress(name,path, sep=""):
    if sep:
        cmd = f'7z.exe a {name} {path} -v{sep}'
    else:
        cmd = f'7z.exe a {name} {path}'
    print("开始压缩...")
    res=os.popen(cmd)
    result = res.read()
    if 'Everything is Ok' in result:
        return 1
    else:
        print(result)
        return 0


def compress(dirpath, sep=""):
    if os.path.exists(dirpath):
        name=tmp+'\\'+os.path.basename(dirpath)+'.zip'
        try:
            res=_compress(name,dirpath, sep)
            if res:
                if sep:
                    news = rename(name)
                    return news
                else:
                    return name
            else:
                return 0
        except:
            traceback.print_exc()
            return 0
    else:
        return 2

def rename(name):
    length = len(os.path.basename(name))
    dirname = os.path.dirname(name)
    fl = os.listdir(dirname)
    print(fl)
    old = []
    new = []
    for i in fl:
        if i[:length] == os.path.basename(name):
            new += [dirname + "/" + i + ".zip"]
            old += [dirname + "/" + i]
    for i in range(len(old)):
        os.rename(old[i], new[i])
    # print(new)
    return new


if __name__=='__main__':
    # _dir=r'C:\Users\moiiii\Desktop\test'
    # tmp=tempfile.mkdtemp(prefix='tmp',dir=__file__ + '/Temp/')
    # print(tmp)
    name = compress(r"D:\下载\septest\Lightyear.2022.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264-OVE.007.zip", "100M")
    length = len(os.path.basename(name))
    dirname = os.path.dirname(name)
    fl = os.listdir(dirname)
    print(fl)
    old = []
    new = []
    for i in fl:
        if i[:length] == os.path.basename(name):
            new += [dirname + "/" + i + ".zip"]
            old += [dirname + "/" + i]
    for i in range(len(old)):
        os.rename(old[i], new[i])
    print(new)