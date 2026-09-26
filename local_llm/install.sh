set -e
export PATH=/root/miniconda3/bin:$PATH
export PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple PIP_TRUSTED_HOST=mirrors.huaweicloud.com
pip install -q -U uv
[ -d /root/autodl-tmp/vllm-env ] || uv venv --python 3.12 /root/autodl-tmp/vllm-env
source /root/autodl-tmp/vllm-env/bin/activate
uv pip install pip
python -m pip install --timeout 600 --retries 20 vllm==0.29.0 huggingface_hub
echo INSTALL_DONE
