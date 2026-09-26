set -e
export PATH=/root/miniconda3/bin:$PATH
export PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple PIP_TRUSTED_HOST=mirrors.aliyun.com
pip install -q -U modelscope
modelscope download --model Qwen/Qwen3-30B-A3B-Instruct-2507 --local_dir /root/autodl-tmp/qwen3-30b-a3b
echo DOWNLOAD_DONE
