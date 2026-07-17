#!/bin/bash
#
# 服务端性能监控脚本
# 用途：监控 CPU、内存、网络连接等指标
#
# 使用方式：
#   ./monitor.sh              # 实时监控（1秒刷新）
#   ./monitor.sh 5            # 5秒刷新
#   ./monitor.sh 1 100        # 刷新100次后停止
#   ./monitor.sh > monitor.log &  # 后台运行并保存日志
#

set -e

# 配置
INTERVAL=${1:-1}    # 刷新间隔（秒）
COUNT=${2:-0}       # 刷新次数（0=无限）
LOG_FILE=""         # 日志文件（可选）

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印帮助
print_help() {
    echo "服务端性能监控脚本"
    echo ""
    echo "使用方式:"
    echo "  $0 [interval] [count]"
    echo ""
    echo "参数:"
    echo "  interval   刷新间隔（秒），默认 1"
    echo "  count      刷新次数，默认 0（无限）"
    echo ""
    echo "示例:"
    echo "  $0              # 1秒刷新，无限次"
    echo "  $0 5            # 5秒刷新，无限次"
    echo "  $0 1 100        # 1秒刷新，100次后停止"
    echo "  $0 > log.txt &  # 后台运行，保存日志"
    echo ""
    exit 0
}

# 参数检查
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    print_help
fi

# 检查是否支持的颜色
if [[ -t 1 ]]; then
    USE_COLOR=1
else
    USE_COLOR=0
fi

# 获取 CPU 使用率
get_cpu_usage() {
    # Linux: 使用 top 命令
    if command -v top &> /dev/null; then
        # 方法1：top -bn1（更准确）
        cpu_idle=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}' | cut -d'%' -f1)
        if [[ -n "$cpu_idle" ]]; then
            cpu_used=$(echo "100 - $cpu_idle" | bc)
            echo "$cpu_used"
            return
        fi
        
        # 方法2：从 /proc/stat 计算（备用）
        if [[ -f /proc/stat ]]; then
            read -r cpu user nice system idle iowait irq softirq steal guest guest_nice < /proc/stat
            total=$((user + nice + system + idle + iowaut + irq + softirq + steal))
            if [[ $total -gt 0 ]]; then
                usage=$((100 * (total - idle) / total))
                echo "$usage"
                return
            fi
        fi
    fi
    
    # macOS: 使用 top 命令
    if [[ "$(uname)" == "Darwin" ]]; then
        cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | cut -d'%' -f1)
        echo "${cpu_usage:-0}"
        return
    fi
    
    echo "0"
}

# 获取内存使用率
get_memory_usage() {
    # Linux
    if [[ -f /proc/meminfo ]]; then
        mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        
        if [[ -n "$mem_total" ]] && [[ -n "$mem_available" ]]; then
            mem_used=$((mem_total - mem_available))
            mem_percent=$((100 * mem_used / mem_total))
            echo "${mem_percent}% ${mem_used}/${mem_total}"
            return
        fi
    fi
    
    # macOS
    if [[ "$(uname)" == "Darwin" ]]; then
        mem_total=$(sysctl -n hw.memsize)
        mem_total_mb=$((mem_total / 1024 / 1024))
        
        # 使用 vm_stat 获取内存信息
        if command -v vm_stat &> /dev/null; then
            pages_free=$(vm_stat | grep "free" | awk '{print $3}' | cut -d'.' -f1)
            pages_used=$(vm_stat | grep "used" | awk '{print $3}' | cut -d'.' -f1 2>/dev/null || echo "0")
            
            # 计算使用量（假设页面大小为 4096 字节）
            mem_used_kb=$((pages_used * 4))
            mem_used_mb=$((mem_used_kb / 1024))
            mem_percent=$((100 * mem_used_kb * 4 / mem_total))
            
            echo "${mem_percent}% ${mem_used_mb}/${mem_total_mb}"
            return
        fi
    fi
    
    # 使用 free 命令（备用）
    if command -v free &> /dev/null; then
        free -m | awk 'NR==2{printf "%s%% %s/%s", $3*100/$2, $3, $2}'
        return
    fi
    
    echo "N/A"
}

# 获取 Python 进程数
get_python_processes() {
    ps aux | grep -E "python|uvicorn" | grep -v grep | wc -l | tr -d ' '
}

# 获取网络连接数
get_network_connections() {
    local port=${1:-8009}
    
    # Linux: 使用 ss 命令
    if command -v ss &> /dev/null; then
        connections=$(ss -tan | grep ":${port}" | grep ESTAB | wc -l)
        echo "$connections"
        return
    fi
    
    # 备用：使用 netstat
    if command -v netstat &> /dev/null; then
        connections=$(netstat -an | grep ":${port}" | grep ESTABLISHED | wc -l)
        echo "$connections"
        return
    fi
    
    # macOS: 使用 lsof
    if [[ "$(uname)" == "Darwin" ]]; then
        connections=$(lsof -i ":${port}" | grep ESTABLISHED | wc -l)
        echo "$connections"
        return
    fi
    
    echo "0"
}

# 获取磁盘使用率
get_disk_usage() {
    df -h / | awk 'NR==2{print $5 " " $3 "/" $2}'
}

# 获取系统负载
get_system_load() {
    if [[ -f /proc/loadavg ]]; then
        load=$(cut -d' ' -f1-3 /proc/loadavg)
        echo "$load"
    elif command -v sysctl &> /dev/null; then
        # macOS
        sysctl -n vm.loadavg | awk '{print $2, $3, $4}'
    else
        echo "N/A"
    fi
}

# 格式化输出
print_header() {
    if [[ $USE_COLOR -eq 1 ]]; then
        printf "${BLUE}%-20s %8s %12s %10s %10s %10s %15s${NC}\n" \
            "时间" "CPU%" "内存" "进程数" "连接数" "磁盘" "系统负载"
    else
        printf "%-20s %8s %12s %10s %10s %10s %15s\n" \
            "时间" "CPU%" "内存" "进程数" "连接数" "磁盘" "系统负载"
    fi
    
    printf "%s\n" "----------------------------------------------------------------------------------------"
}

print_line() {
    local timestamp=$1
    local cpu=$2
    local memory=$3
    local processes=$4
    local connections=$5
    local disk=$6
    local load=$7
    
    # 根据值设置颜色
    local cpu_color=""
    local mem_color=""
    
    if [[ $USE_COLOR -eq 1 ]]; then
        # CPU 颜色
        cpu_num=$(echo "$cpu" | cut -d'.' -f1)
        if [[ "$cpu_num" -gt 80 ]]; then
            cpu_color="${RED}"
        elif [[ "$cpu_num" -gt 60 ]]; then
            cpu_color="${YELLOW}"
        else
            cpu_color="${GREEN}"
        fi
        
        # 内存颜色
        mem_num=$(echo "$memory" | cut -d'%' -f1)
        if [[ "$mem_num" -gt 80 ]]; then
            mem_color="${RED}"
        elif [[ "$mem_num" -gt 60 ]]; then
            mem_color="${YELLOW}"
        else
            mem_color="${GREEN}"
        fi
    fi
    
    printf "%-20s ${cpu_color}%8s${NC} ${mem_color}%12s${NC} %10s %10s %10s %15s\n" \
        "$timestamp" "$cpu" "$memory" "$processes" "$connections" "$disk" "$load"
}

# 主循环
main() {
    echo "========================================"
    echo "服务端性能监控"
    echo "========================================"
    echo "刷新间隔: ${INTERVAL}s"
    echo "刷新次数: ${COUNT:-无限}"
    echo "停止方式: Ctrl+C"
    echo ""
    
    print_header
    
    counter=0
    
    while true; do
        # 检查是否达到指定次数
        if [[ "$COUNT" -gt 0 ]] && [[ "$counter" -ge "$COUNT" ]]; then
            break
        fi
        
        # 获取时间
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # 获取各项指标
        cpu=$(get_cpu_usage)
        memory=$(get_memory_usage)
        processes=$(get_python_processes)
        connections=$(get_network_connections 8009)
        disk=$(get_disk_usage)
        load=$(get_system_load)
        
        # 输出
        print_line "$timestamp" "$cpu" "$memory" "$processes" "$connections" "$disk" "$load"
        
        # 递增计数器
        ((counter++))
        
        # 等待
        sleep "$INTERVAL"
    done
    
    echo ""
    echo "监控结束（共 ${counter} 次）"
}

# 捕获 Ctrl+C
trap 'echo ""; echo "监控已停止（共 ${counter:-0} 次）"; exit 0' INT TERM

# 执行
main