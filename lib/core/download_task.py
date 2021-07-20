#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Kun 根据输入后缀修正输入类型，处理自动下载APP或者H5的任务
# Github:     


import os
import re
import time
import config
import hashlib
from queue import Queue
import lib as cores
from lib.request.download import DownloadThreads

class DownloadTask(object):

    def start(self,path,types):
        create_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        # 自动根据文件后缀名称进行修正，DEX待完善
        if path.endswith("apk"):
            types = "Android"
            file_name = create_time+ ".apk"
        elif path.endswith("ipa"):
            types = "iOS"
            file_name = create_time + ".ipa"
        else:
            # 防止文件后缀与输入类型不一致，先看后缀后看输入类型
            if types == "Android":
                file_name = create_time+ ".apk"
            elif types == "iOS":
                file_name = create_time + ".ipa"
            else:
                # 其他一律按HTML处理，可能有错误，待优化
                types = "WEB"
                file_name = create_time + ".html"
        if not(path.startswith("http://") or path.startswith("https://")):
            if not os.path.isdir(path): 
                # 不是目录
                return {"path":path,"type":types}
            else: 
                # 目录处理
                return {"path":path,"type":types}
        else:
            print("[*] Detected that the task is not local, preparing to download file......")
            cache_path = os.path.join(cores.download_path, file_name)            
            thread = DownloadThreads(path,file_name,cache_path,types)
            thread.start()
            thread.join()
            print()
            return {"path":cache_path,"type":types}
            
            
            
            
            
            
            
            
            