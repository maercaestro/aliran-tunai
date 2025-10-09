#!/bin/bash

# Systemd Security Analysis Script for AliranTunai
# This script helps validate and monitor security settings

echo "🔒 AliranTunai Systemd Security Analysis"
echo "========================================"

SERVICE_NAME="aliran-tunai.service"

# Check if service exists and is running
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service is running"
else
    echo "❌ Service is not running"
fi

echo ""
echo "🛡️  Security Configuration Analysis:"
echo "-----------------------------------"

# Check security settings
echo "Checking security hardening..."

# Network restrictions
if systemctl show $SERVICE_NAME -p RestrictAddressFamilies | grep -q "AF_INET"; then
    echo "✅ Network address families restricted"
else
    echo "⚠️  Network address families not restricted"
fi

# Filesystem protections
if systemctl show $SERVICE_NAME -p ProtectSystem | grep -q "strict"; then
    echo "✅ Filesystem protection enabled (strict)"
else
    echo "⚠️  Filesystem protection not optimal"
fi

# Memory protections
if systemctl show $SERVICE_NAME -p MemoryDenyWriteExecute | grep -q "yes"; then
    echo "✅ Memory write+execute protection enabled"
else
    echo "⚠️  Memory protection not enabled"
fi

# Process restrictions
if systemctl show $SERVICE_NAME -p NoNewPrivileges | grep -q "yes"; then
    echo "✅ No new privileges restriction enabled"
else
    echo "⚠️  New privileges not restricted"
fi

# System call filtering
if systemctl show $SERVICE_NAME -p SystemCallFilter | grep -q "@system-service"; then
    echo "✅ System call filtering enabled"
else
    echo "⚠️  System call filtering not configured"
fi

echo ""
echo "📊 Resource Usage:"
echo "-----------------"

# Memory usage
MEMORY_CURRENT=$(systemctl show $SERVICE_NAME -p MemoryCurrent --value)
MEMORY_MAX=$(systemctl show $SERVICE_NAME -p MemoryMax --value)
if [ "$MEMORY_CURRENT" != "[not set]" ]; then
    MEMORY_MB=$((MEMORY_CURRENT / 1024 / 1024))
    echo "Memory usage: ${MEMORY_MB}MB"
    if [ "$MEMORY_MAX" != "infinity" ] && [ "$MEMORY_MAX" != "[not set]" ]; then
        MEMORY_MAX_MB=$((MEMORY_MAX / 1024 / 1024))
        echo "Memory limit: ${MEMORY_MAX_MB}MB"
    fi
else
    echo "Memory usage: Not available"
fi

# CPU usage
CPU_USAGE=$(systemctl show $SERVICE_NAME -p CPUUsageNSec --value)
if [ "$CPU_USAGE" != "[not set]" ] && [ "$CPU_USAGE" != "0" ]; then
    echo "CPU time used: $((CPU_USAGE / 1000000000))s"
else
    echo "CPU usage: Not available"
fi

# Task count
TASKS_CURRENT=$(systemctl show $SERVICE_NAME -p TasksCurrent --value)
TASKS_MAX=$(systemctl show $SERVICE_NAME -p TasksMax --value)
if [ "$TASKS_CURRENT" != "[not set]" ]; then
    echo "Tasks: $TASKS_CURRENT"
    if [ "$TASKS_MAX" != "infinity" ] && [ "$TASKS_MAX" != "[not set]" ]; then
        echo "Tasks limit: $TASKS_MAX"
    fi
fi

echo ""
echo "🔍 Security Recommendations:"
echo "---------------------------"

# Check for common security issues
if ! systemctl show $SERVICE_NAME -p User | grep -q "ec2-user"; then
    echo "⚠️  Consider running as non-root user"
fi

if ! systemctl show $SERVICE_NAME -p PrivateNetwork | grep -q "yes"; then
    echo "ℹ️  Service has network access (expected for API server)"
fi

echo ""
echo "📋 Service Status:"
echo "-----------------"
systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo "🔐 Security Score Summary:"
echo "-------------------------"
SCORE=0

# Calculate security score based on enabled features
systemctl show $SERVICE_NAME -p NoNewPrivileges | grep -q "yes" && SCORE=$((SCORE + 10))
systemctl show $SERVICE_NAME -p ProtectSystem | grep -q "strict" && SCORE=$((SCORE + 15))
systemctl show $SERVICE_NAME -p PrivateTmp | grep -q "yes" && SCORE=$((SCORE + 10))
systemctl show $SERVICE_NAME -p ProtectHome | grep -q "yes" && SCORE=$((SCORE + 10))
systemctl show $SERVICE_NAME -p MemoryDenyWriteExecute | grep -q "yes" && SCORE=$((SCORE + 15))
systemctl show $SERVICE_NAME -p SystemCallFilter | grep -q "@system-service" && SCORE=$((SCORE + 20))
systemctl show $SERVICE_NAME -p RestrictAddressFamilies | grep -q "AF_INET" && SCORE=$((SCORE + 10))
systemctl show $SERVICE_NAME -p PrivateDevices | grep -q "yes" && SCORE=$((SCORE + 10))

echo "Security Score: $SCORE/100"

if [ $SCORE -ge 80 ]; then
    echo "🟢 Excellent security configuration!"
elif [ $SCORE -ge 60 ]; then
    echo "🟡 Good security, minor improvements possible"
elif [ $SCORE -ge 40 ]; then
    echo "🟠 Moderate security, improvements recommended"
else
    echo "🔴 Security needs significant improvement"
fi

echo ""
echo "Analysis complete. Run this script regularly to monitor security status."