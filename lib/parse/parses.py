#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Kun 用于解析文件中的静态信息
# Github: 

import re
import os
import config
import threading
import lib as cores

class ParsesThreads(threading.Thread):

    def __init__(self,threadID,name,file_queue,result_dict,types):
        threading.Thread.__init__(self) 
        self.threadID = threadID
        self.name = name
        self.file_queue = file_queue
        self.result_dict = result_dict
        self.types = types
        self.result_list = []
            
    def __regular_parse__(self):
        while True:
            if self.file_queue.empty():
                break
            
            file_path = self.file_queue.get(timeout = 5)
            scan_str = ("[+] Scan file : %s" % file_path)
            # 输出的信息过多，注释掉
            #print(scan_str)
            
            # 调用Android 相关处理逻辑
            if self.types == "Android":
                self.__get_string_by_file__(file_path)
            # 调用iOS 相关处理逻辑
            elif self.types == "iOS":
                self.__get_string_by_iOS__(file_path)
            # 调用Web 相关处理逻辑
            else:
                self.__get_string_by_file__(file_path)
            
            result_set = set(self.result_list)
            if len(result_set) != 0:
                self.result_dict[file_path] = result_set

    def __get_string_by_iOS__(self,file_path):
        output_path = cores.output_path
        strings_path = cores.strings_path
        temp = os.path.join(output_path,"temp.txt")
        cmd_str = ("%s %s > %s") % (strings_path,file_path,temp)
        if os.system(cmd_str) == 0:
            with open(temp,"r",encoding='utf-8',errors='ignore') as f:
                lines = f.readlines()
                for line in lines:
                    self.__parse_string__(line)

    def __get_string_by_file__(self,file_path):
        with open(file_path,"r",encoding="utf8",errors='ignore') as f :
            file_content = f.read()
            # 获取到所有的字符串
            pattern = re.compile(r'\"(.*?)\"') 
            results = pattern.findall(file_content)
            
            # 遍历所有的字符串
            for result in set(results): 
                self.__parse_string__(result)    
        
    def __parse_string__(self,result):
        # 通过正则筛选需要过滤的字符串
        for filter_str in config.filter_strs:
            filter_str_pat = re.compile(filter_str) 
            filter_resl = filter_str_pat.findall(result)

            # 过滤掉未搜索到的内容
            if len(filter_resl) != 0:
                # 只提取了第一个结果
                resl_str = filter_resl[0]
                # 过滤
                if self.__filter__(resl_str) == 0:
                    continue

                self.threadLock.acquire()
                if cores.all_flag:
                    print("[+] Match to domain name: %s" % (resl_str))
                self.result_list.append(resl_str)
                self.threadLock.release()
            continue

    def __filter__(self,resl_str):
        return_flag = 1 
        resl_str = resl_str.replace("\r","").replace("\n","").replace(" ","")
        
        if len(resl_str) == 0:
            return 0
            
        for filte in set(config.filter_no):
            resl_str = resl_str.replace(filte,"")
            if len(resl_str) == 0:
                return_flag = 0 
                continue
            
            if re.match(filte,resl_str):
                return_flag = 0 
                continue
        return return_flag  

    def run(self):
        self.threadLock = threading.Lock()
        self.__regular_parse__()
