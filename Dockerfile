FROM python:3.11-slim-bookworm

# 设置环境变量，确保 Python 输出不被缓冲，以便日志能实时显示
ENV PYTHONUNBUFFERED=1

# 启用 non-free 和 contrib 仓库以安装硬件加速驱动
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/Components: main.*/Components: main contrib non-free non-free-firmware/g' /etc/apt/sources.list.d/debian.sources; \
    else \
        sed -i 's/main/main contrib non-free non-free-firmware/g' /etc/apt/sources.list; \
    fi

# 安装 FFmpeg 和硬件加速驱动
# intel-media-va-driver-non-free: Intel QSV/VAAPI (仅 amd64)
# mesa-va-drivers: AMD VAAPI
# nvidia-vaapi-driver: NVIDIA VAAPI (仅 amd64)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    vainfo \
    mesa-va-drivers && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        apt-get install -y --no-install-recommends \
        intel-media-va-driver-non-free \
        nvidia-vaapi-driver; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置 NVIDIA 驱动环境变量，以便支持 NVIDIA GPU
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,video,utility

# 默认运行 main.py，终止 main.py 即退出容器
CMD ["python", "main.py"]
