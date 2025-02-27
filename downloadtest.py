import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl
import threading
import time

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

urls = [
    "https://sz.10000gd.tech:12348/shmfile/4000",
    "https://gz.10000gd.tech:12348/shmfile/4000",
    "https://fs.10000gd.tech:12348/shmfile/4000",
    "https://zh.10000gd.tech:12348/shmfile/4000",
    "https://st.10000gd.tech:12348/shmfile/4000",
    "https://zs.10000gd.tech:12348/shmfile/4000",
    "https://sg.10000gd.tech:12348/shmfile/4000",
    "https://dg.10000gd.tech:12348/shmfile/4000"
]

lock = threading.Lock()
total_downloaded_since_last_update = 0
last_time = time.time()

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
                        with lock:
                            total_downloaded_since_last_update += len(chunk)
            else:
                print(f"\nFailed to download from {url}, status code: {response.status_code}")
        except Exception as e:
            if not stop_event.is_set():
                print(f"\nError downloading {url}: {e}")

def report_total_speed(stop_event):
    global total_downloaded_since_last_update, last_time
    while not stop_event.is_set():
        current_time = time.time()
        elapsed_time = current_time - last_time
        with lock:
            downloaded = total_downloaded_since_last_update
            total_downloaded_since_last_update = 0  # 清零以便于下次计算
        if elapsed_time >= 1:  # 只有当时间间隔至少为1秒时才更新速度
            speed = downloaded / elapsed_time / 1024 / 1024  # 转换为MB/s
            print(f"\rTotal download speed: {speed:.2f} MB/s", end='', flush=True)
            last_time = current_time
        else:
            # 如果时间间隔小于1秒，则等待直到达到1秒再进行计算
            time.sleep(1 - elapsed_time)
        time.sleep(0.1)

def main():
    stop_event = threading.Event()
    threads = []
    try:
        # 启动下载线程
        for url in urls:
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