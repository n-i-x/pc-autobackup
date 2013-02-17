#!/bin/bash
# Make sure only root can run our script
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

echo "Cleaning up after any previous runs..."
rm diagnose_me.zip diagnose_me.tcpdump diagnose_me.log nohup.out

echo "Gathering basic system information..."
uname -a > diagnose_me.log
echo >> diagnose_me.log

echo "Gathering basic network information..."
ifconfig -a >> diagnose_me.log
echo >> diagnose_me.log
netstat -rnW >> diagnose_me.log
echo >> diagnose_me.log
netstat -vnlW >> diagnose_me.log
echo >> diagnose_me.log

echo "Gathering process information..."
ps auxwww >> diagnose_me.log
echo >> diagnose_me.log
echo >> diagnose_me.log

echo "Starting network capture..."
nohup tcpdump -e -s 1514 -w diagnose_me.tcpdump &

echo "Starting pc_autobackup in debug mode..."
nohup ./pc_autobackup.py --debug --log_file=diagnose_me.log &

sleep 3
echo
echo
echo
echo "Please start AutoBackup on your camera..."
echo
read -p "Press [Enter] key once AutoBackup fails/finishes..."

echo "Shutting down pc_autobackup..."
pkill pc_autobackup.py

echo "Shutting down network capture..."
pkill tcpdump

echo "Archiving diagnostic files..."
zip -9 diagnose_me.zip diagnose_me.tcpdump diagnose_me.log nohup.out

echo "Deleting diagnostic files..."
rm diagnose_me.tcpdump diagnose_me.log nohup.out