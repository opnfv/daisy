#!/bin/sh
#to be trusted by other host and no password needed when use ssh command

#check parameters legality
logfile=/var/log/trustme.log
function print_log
{
   local promt="$1"
   echo -e "$promt"
   echo -e "`date -d today +"%Y-%m-%d %H:%M:%S"`  $promt" >> $logfile
}
ip=$1
if [ -z $ip ]; then
  print_log "Usage: `basename $0` ipaddr passwd"
  exit 1
fi

passwd=$2
if [ -z $passwd ]; then
  print_log "Usage: `basename $0` ipaddr passwd"
  exit 1
fi

rpm -qi sshpass >/dev/null
if [ $? != 0 ]; then
  print_log "Please install sshpass first"
  exit 1
fi

#ping other host
unreachable=`ping $ip -c 1 -W 3 | grep -c "100% packet loss"`
if [ $unreachable -eq 1 ]; then
  print_log "host $ip is unreachable"
  exit 1
fi

#generate ssh pubkey
if [ ! -e ~/.ssh/id_dsa.pub ]; then
  print_log "generating ssh public key ..."
  ssh-keygen -t dsa -f ~/.ssh/id_dsa -N "" <<EOF
n
EOF
  if [ $? != 0 ]; then
    print_log "ssh-keygen failed"
    exit 1
  fi
fi

lcal_host="127.0.0.1"
print_log "clear my old pub key on $local_host ..."
sshpass -p $passwd ssh -o StrictHostKeyChecking=no $local_host "test -f  ~/.ssh/known_hosts"
if [ $? = 0 ]; then
    ssh-keygen -R $ip
    if [ $? != 0 ]; then
       print_log "delete pub key of $ip from $local_host known_hosts failed"
       exit 1
    fi
fi

#copy new public key
print_log "copy my public key to $ip ..."
sshpass -p $passwd ssh-copy-id -i ~/.ssh/id_dsa.pub -o StrictHostKeyChecking=no root@$ip
if [ $? != 0 ]; then
    print_log "ssh-copy-id failed"
    exit 1
fi

print_log "trustme ok!"

