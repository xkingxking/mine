import torch

def test_cuda():
    """测试 PyTorch 的 CUDA 支持"""
    print(f"PyTorch 版本: {torch.__version__}")
    print(f"CUDA 是否可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA 版本: {torch.version.cuda}")
        print(f"当前使用的 GPU: {torch.cuda.get_device_name(0)}")
        
        # 测试 CUDA 张量
        x = torch.rand(5, 3)
        print("\nCPU 张量:")
        print(x)
        print(f"设备: {x.device}")
        
        x_cuda = x.cuda()
        print("\nGPU 张量:")
        print(x_cuda)
        print(f"设备: {x_cuda.device}")
    else:
        print("警告: CUDA 不可用，PyTorch 将使用 CPU 模式运行")

if __name__ == "__main__":
    test_cuda() 