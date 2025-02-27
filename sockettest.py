import asyncio

async def create_tcp_connection(target_host, target_port, idx):
    """异步创建一个到指定host和port的TCP连接，保持连接直到程序结束"""
    try:
        reader, writer = await asyncio.open_connection(host=target_host, port=target_port)
        print(f"成功创建连接 {idx}")
        return writer  # 返回writer，保持连接
    except Exception as e:
        print(f"连接 {idx} 失败: {str(e)}")
        return None

async def main():
    target_host = "sz.10000gd.tech"
    target_port = 12348
    num_connections = 1000  # 测试用10个连接
    
    print(f"开始测试连接到 {target_host}:{target_port}")
    tasks = [create_tcp_connection(target_host, target_port, i+1) for i in range(num_connections)]
    writers = await asyncio.gather(*tasks)
    
    print("所有连接已建立，按Ctrl+C退出程序...")
    try:
        # 永久等待，直到被KeyboardInterrupt中断
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        # 捕获Ctrl+C，进行清理
        print("\n收到Ctrl+C，正在关闭连接...")
        for writer in writers:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
        print("所有连接已关闭，程序退出")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 确保主程序也能捕获Ctrl+C
        pass