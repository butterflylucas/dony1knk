#!/bin/bash

# 上传到云服务脚本
# Upload to Cloud Script

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

# 获取参数
CLOUD_PROVIDER=${CLOUD_PROVIDER:-aliyun}
SOURCE_DIR="${1:-.}"
BUCKET="${2:-my-website-bucket}"
REGION="${3:-cn-hangzhou}"

print_info "上传配置:"
print_info "云服务商: $CLOUD_PROVIDER"
print_info "源目录: $SOURCE_DIR"
print_info "OSS 桶: $BUCKET"
print_info "地区: $REGION"

if [ "$CLOUD_PROVIDER" = "aliyun" ]; then
    print_info "使用 ossutil 上传到阿里云 OSS"
    
    # 检查 ossutil
    if ! command -v ossutil &> /dev/null; then
        print_info "未找到 ossutil，请先安装"
        exit 1
    fi
    
    # 配置 ossutil
    ossutil config -e "oss-${REGION}.aliyuncs.com" \
                   -i "$ALIYUN_ACCESS_KEY" \
                   -k "$ALIYUN_SECRET_KEY" \
                   -c osscfg
    
    # 上传文件
    ossutil cp -r "$SOURCE_DIR" "oss://$BUCKET/sites/"
    
    print_success "文件已上传到阿里云 OSS"

elif [ "$CLOUD_PROVIDER" = "aws" ]; then
    print_info "使用 aws-cli 上传到 AWS S3"
    
    # 检查 aws-cli
    if ! command -v aws &> /dev/null; then
        print_info "未找到 aws-cli，请先安装"
        exit 1
    fi
    
    # 上传文件
    aws s3 sync "$SOURCE_DIR" "s3://$BUCKET/sites/" \
        --region "$REGION" \
        --delete
    
    print_success "文件已上传到 AWS S3"

else
    print_info "不支持的云服务商: $CLOUD_PROVIDER"
    exit 1
fi

print_success "上传完成"
