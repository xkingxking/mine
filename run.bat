@echo off  
REM 检查并安装依赖  
pip install -r requirements.txt  
IF %ERRORLEVEL% NEQ 0 (  
    echo [错误] 依赖安装失败，请确认已安装 Python 且配置了pip环境变量。  
    goto end  
)  
echo [信息] 项目依赖已安装完毕。  

REM 如无.env则复制默认配置  
IF NOT EXIST ".env" (  
    copy ".env.example" ".env"  
    echo [信息] 已生成默认配置文件.env，请根据需要修改其中配置。  
)  

REM 启动后端服务  
echo [信息] 正在启动评测平台后端服务...  
python app\api\main.py  

:end  
pause  
