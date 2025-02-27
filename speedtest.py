import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl
import threading
import time
import os

class TlsAdapter(HTTPAdapter):
    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.options |= ssl.OP_NO_SSLv2
        ctx.options |= ssl.OP_NO_SSLv3   
        self.poolmanager = PoolManager(*pool_args,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2,
                                       ssl_context=ctx,
                                       **pool_kwargs)

session = requests.session()
adapter = TlsAdapter()
session.mount("https://", adapter)

upload_urls = [
    "https://sz.10000gd.tech:12348/upload",
    "https://gz.10000gd.tech:12348/upload",
    "https://fs.10000gd.tech:12348/upload",
    "https://zh.10000gd.tech:12348/upload",
    "https://st.10000gd.tech:12348/upload",
    "https://zs.10000gd.tech:12348/upload",
    "https://sg.10000gd.tech:12348/upload",
    "https://dg.10000gd.tech:12348/upload"
]

download_urls = [
    "https://sz.10000gd.tech:12348/shmfile/4000",
    "https://gz.10000gd.tech:12348/shmfile/4000",
    "https://fs.10000gd.tech:12348/shmfile/4000",
    "https://zh.10000gd.tech:12348/shmfile/4000",
    "https://st.10000gd.tech:12348/shmfile/4000",
    "https://zs.10000gd.tech:12348/shmfile/4000",
    "https://sg.10000gd.tech:12348/shmfile/4000",
    "https://dg.10000gd.tech:12348/shmfile/4000"
]

upload_size_mb = 100  # 设置你想要上传的数据大小，单位为MB

lock_upload = threading.Lock()
lock_download = threading.Lock()

total_uploaded_since_last_update = 0
total_downloaded_since_last_update = 0

last_time = time.time()

def upload_speed_test(url, stop_event, data):
    global total_uploaded_since_last_update
    chunk_size = 1024 * 1024  # 每次读取1MB
    while not stop_event.is_set():
        for i in range(0, len(data), chunk_size):
            if stop_event.is_set():
                break
            chunk = data[i:i + chunk_size]
            try:
                response = session.post(url, data=chunk, timeout=60)
                if response.status_code == 200:
                    with lock_upload:
                        total_uploaded_since_last_update += len(chunk)
                else:
                    print(f"\nFailed to upload to {url}, status code: {response.status_code}")
            except Exception as e:
                # 移除了错误信息的打印
                    pass

def download_speed_test(url, stop_event):
    global total_downloaded_since_last_update
    while not stop_event.is_set():
        try:
            response = session.get(url, stream=True, timeout=5)
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=1024):
                    if stop_event.is_set():
                        break
                    if chunk:
                        with lock_download:
                            total_downloaded_since_last_update += len(chunk)
            else:
                print(f"\nFailed to download from {url}, status code: {response.status_code}")
        except Exception as e:
            # 移除了错误信息的打印
                    pass

def report_total_speed(stop_event):
    global total_uploaded_since_last_update, total_downloaded_since_last_update, last_time
    while not stop_event.is_set():
        current_time = time.time()
        elapsed_time = current_time - last_time
        
        # 计算并打印上传速度
        with lock_upload:
            uploaded = total_uploaded_since_last_update
            total_uploaded_since_last_update = 0
        upload_speed = uploaded / elapsed_time / 1024 / 1024  # 转换为MB/s
        
        # 计算并打印下载速度
        with lock_download:
            downloaded = total_downloaded_since_last_update
            total_downloaded_since_last_update = 0
        download_speed = downloaded / elapsed_time / 1024 / 1024  # 转换为MB/s
        
        # 打印上传和下载速度
        print(f"\rUpload Speed: {upload_speed:.2f} MB/s | Download Speed: {download_speed:.2f} MB/s", end='', flush=True)
        
        last_time = current_time
        time.sleep(1)  # 等待一秒以确保至少一秒钟的间隔

def main():
    stop_event = threading.Event()
    threads = []
    data = os.urandom(upload_size_mb * 1024 * 1024)  # 生成100MB的随机数据
    
    try:
        # 启动上传线程
        for url in upload_urls:
            thread = threading.Thread(target=upload_speed_test, args=(url, stop_event, data))
            threads.append(thread)
            thread.start()

        # 启动下载线程
        for url in download_urls:
            thread = threading.Thread(target=download_speed_test, args=(url, stop_event))
            threads.append(thread)
            thread.start()

        # 启动速度报告线程
        report_thread = threading.Thread(target=report_total_speed, args=(stop_event,))
        report_thread.start()

        # 主线程等待，直到收到 Ctrl+C
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nAttempting to close threads...")
        stop_event.set()  # 设置停止事件，让所有线程知道需要退出
        for thread in threads:
            thread.join()  # 等待所有线程完成
        report_thread.join()
        print("\nAll threads have been closed.")

if __name__ == "__main__":
    main()