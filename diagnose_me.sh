#!/bin/bash
# Make sure only root can run our script
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

log_file=diagnose_me.log

log() {
  echo "========================================="
  echo "BEGIN $1"
  echo "========================================="
  while read data
  do
    echo "[$(date +"%D %T")] $data" 
  done
  echo "========================================="
  echo "END $1"
  echo "========================================="
  echo
  echo
}

ask_perm() {
  echo -n "$1 (Y/n): "
  read ans
  case "$ans" in
    y|Y|yes|YES|Yes) return 0 ;;
    n|N|no|NO|No) return 1 ;;
    *) return 0 ;;
  esac
}


echo "Cleaning up after any previous runs..."
rm debug.log diagnose_me.zip diagnose_me.tcpdump diagnose_me.log nohup.out &> /dev/null

echo "Gathering basic system information..."
uname -a | log "uname" > $log_file

echo "Gathering basic network information..."
ifconfig -a | log "ifconfig" >> $log_file
netstat -rnW | log "routing tables" >> $log_file
netstat -vnlW | log "netstat" >> $log_file

which iptables &> /dev/null
if [[ $? -eq 0 ]]; then
  iptables -nL | log "iptables" >> $log_file
fi

echo
echo
echo "Gathering process information..."
echo "WARNING: Process information may contain passwords!"
echo 'Check `ps auxwww` output before sending.'
ask_perm "Would you like to send process information?" && ps auxwww | log "process information" >> $log_file

echo "Starting network capture..."
nohup tcpdump -e -s 1514 -w diagnose_me.tcpdump &

echo "Starting pc_autobackup in debug mode..."
nohup ./pc_autobackup.py --debug --log_file=debug.log &

sleep 3
echo
echo
echo
echo "Please start AutoBackup on your camera..."
echo
read -p "Press [Enter] key once AutoBackup fails/finishes..."

echo "Shutting down pc_autobackup..."
pkill -f pc_autobackup

echo "Shutting down network capture..."
pkill tcpdump

cat debug.log | log "pc_autobackup debug output" >> $log_file

echo "Archiving diagnostic files..."
zip -9 diagnose_me.zip diagnose_me.log diagnose_me.tcpdump nohup.out

echo "Deleting diagnostic files..."
rm debug.log diagnose_me.tcpdump diagnose_me.log nohup.out

echo
echo
echo "Please email diagnose_me.zip to jeff@rebeiro.net"