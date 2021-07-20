#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Kun 统一任务调度中心
# Github: 

import os
import re
import config
import threading
from queue import Queue
#Bootstrapper
import lib as cores
from lib.core.android_task import AndroidTask
from lib.core.download_task import DownloadTask
from lib.core.ios_task import iOSTask
from lib.core.net_task import NetTask
from lib.core.web_task import WebTask
from lib.parse.parses import ParsesThreads


class BaseTask(object):
    thread_list = []
    result_dict = {}
    app_history_list = []
    domain_history_list = []
    
    # 统一初始化入口，默认类型为Android
    def __init__(self, target_type="Android", inputs="", rules="", sniffer=True, threads=10, package=""):
        self.target_type = target_type
        self.path = inputs
        if rules:
            config.filter_strs.append(r'.*'+str(rules)+'.*')
        self.sniffer = sniffer
        self.threads = threads
        self.package = package
        self.file_queue = Queue()
        
    
    # 统一调度平台
    def start(self):

        # 获取历史记录
        self.__history_handle__()
        
        print("[*] The matching rules are as follows:\n %s \n" % (set(config.filter_strs)) )
        
        print("[*] The ignored URL&IP are as follows:\n %s \n" % (set(config.filter_no)) )
        
        print("[*] AI is analyzing filtering rules......")
        
        task_info = self.__tast_control__()
        if len(task_info) < 1:
            return

        file_queue = task_info["file_queue"]
        shell_flag = task_info["shell_flag"]
        comp_list = task_info["comp_list"]
        packagename = task_info["packagename"]
        file_identifier = task_info["file_identifier"]
        #\033[0;31m red
        if shell_flag:
            print('[-] Error: This application has shell, the retrieval results may not be accurate, Please remove the shell and try again!')
            return

        # 线程控制中心
        print("\n[*] ==========  Searching for strings that match the rules ==============")
        self.__threads_control__(file_queue)

        # 等待线程结束
        for thread in self.thread_list:
            thread.join()
    
        # 结果输出中心
        self.__print_control__(packagename,comp_list,file_identifier)

    # 任务控制中心
    def __tast_control__(self):
        task_info = {}
        # 自动根据文件后缀名称进行修正
        cache_info = DownloadTask().start(self.path,self.target_type)
        target_path = cache_info["path"]
        target_type = cache_info["type"]
        # 下载失败，建议手动下载后重试
        if (not os.path.exists(target_path) and cores.download_flag):
            print("[-] File download failed! Please download the file manually and try again.")
            return task_info

        # 调用Android 相关处理逻辑
        if target_type == "Android":
            task_info = AndroidTask(target_path,self.package).start()
        # 调用iOS 相关处理逻辑
        elif target_type == "iOS":
            task_info = iOSTask(target_path).start()
        # 调用Web 相关处理逻辑
        else:
            task_info = WebTask(target_path).start()
        return task_info

    def __threads_control__(self,file_queue):
        for threadID in range(1,self.threads): 
            name = "Thread - " + str(int(threadID))
            thread =  ParsesThreads(threadID,name,file_queue,self.result_dict,self.target_type)
            thread.start()
            self.thread_list.append(thread)

    def __print_control__(self,packagename,comp_list,file_identifier):
        txt_result_path = cores.txt_result_path
        xls_result_path = cores.xls_result_path
                
        if self.sniffer:
            print("\n[*] ========= Sniffing the URL address of the search ===============")
            NetTask(self.result_dict,self.app_history_list,self.domain_history_list,file_identifier,self.threads).start()
            print("[*] ======================== Sniffing done =========================")
            
        if packagename: 
            print("\n[*] =========  The package name of this APP is: ===============")
            print(packagename)

        if len(comp_list) != 0:
            print("\n[*] ========= Component information is as follows :===============")
            for json in comp_list:
                print(json)
        
        if cores.all_flag:
            print("\n[*] Get more information in the TXT: %s" %(cores.txt_result_path))

        if self.sniffer:
            print("[*] Get more information in the XLS: %s" %(cores.xls_result_path))

    def __history_handle__(self):
        # domain_history.txt
        domain_history_path =  cores.domain_history_path
        # app_history.txt
        app_history_path = cores.app_history_path
        
        if os.path.exists(domain_history_path):
            domain_counts = {}
            app_size = 0 
            with open(app_history_path,"r",encoding='utf-8',errors='ignore') as f:
                lines = f.readlines()
                app_size = len(lines)
                for line in lines:
                   self.app_history_list.append(line.replace("\r","").replace("\n",""))
                f.close()
            
            # 根据历史记录忽略某些重复的域名
            with open(domain_history_path,"r",encoding='utf-8',errors='ignore') as f:
                lines = f.readlines()
                cout = 3
                if (app_size > 3) and (app_size % 3==0):
                    cout = cout + 1
                for line in lines:
                    domain = line.replace("\r","").replace("\n","")
                    self.domain_history_list.append(domain)
                    domain_count = lines.count(line)
                    if domain_count >= cout:
                        config.filter_no.append(".*" + domain)
                        print("[*] Adding ignored URL :\n %s \n" % (domain) )
                f.close()

    
