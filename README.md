<div align="center">

# 欧亚学院畅课文件系统

</div>

## 说明
> 仅作学习使用

挖了个坑，主要是练习用的。  
现在已经实现文件属性获取存入自制的树形数据结构里了，完事之后直链获取也蛮简单的，加上了。  
文件下载会下载到py脚本对应文件夹下的downloads文件夹中，没有加名字去重，如果有重名文件记得先备份，不然就覆盖了

2023-02-27  阴  
- 昨天加了上传功能但是没来得及写，今天是加了删除功能顺便为了cd功能修改了大部分内容  
- 把内容加载修改了，以前是进到哪个文件夹才会去请求哪一个文件夹。改成了刚开始就一次性全部递归地给获取完，这会在一开始很费时间，之后会找机会优化一下  
- 还有登录，加了conf.json用于保存学号和密码，保存的时候会用b64简单编码一下防止不小心看到，input()输入的时候密码也不会显示出来

2023-02-27  阴  21:45  
- 随便加了个线程后台加载，就当优化了。按理来说我本来的想法是只请求后3层内的所有文件夹，因为怕请求多了会被注意，有被封的风险，不过觉得应该没太大可能。  
- 有机会和时间的话会尽量做出gui

2023-02-27 晴  15.19
- 加了移动文件的方法，把命令行整体方法改了，之后有内容更方便加，看着也清爽，只不过python版本就会被限制到10以上  
- 把文件系统脚本和登录压缩啥的模块分开了，conf.json也是，加了清除临时文件、下载文件、conf.json账号文件的bat脚本，很普通的一两句话  
- 加了requirements.txt和pipinstall脚本，默认使用pip3下载不是pip虽然没什么大的区别


## 效果:
<img src="https://user-images.githubusercontent.com/96933655/221785315-12ad9efa-f31c-4bb9-a74e-52a857897b9a.png" width=60%>

<img src="https://user-images.githubusercontent.com/96933655/221785934-041c8260-45f8-43cd-82d6-3c0f496cce92.png" width=60%>




## 为什么做这个事情呢... 
如果想把它当网盘用的话，网页端加载不知道为啥总是有些慢，尤其是文件夹加载，而且还得加载很多别的玩意很浪费资源。  
写个这个练练手，之后可能也会想实现本地直接交作业啥的，这个文件系统功能是必要的😰
