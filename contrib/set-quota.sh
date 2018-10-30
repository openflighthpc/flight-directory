#!/bin/bash
#
# This script will be run by userware after creating the user.
#

USER="$1"
alcesuser="1653000004"
testdir="/opt/directory/scripts"

#
# Set filesystem quota - need to find which master is running the /export/users mount
#

if [ `ssh master1 mount -v | grep -c "export/users" | awk '{print $1}'` -gt 0 ] ; then
   master=master1
elif [ `ssh master2 mount -v | grep -c "export/users" | awk '{print $1}'` -gt 0 ] ; then
   master=master2
else
   echo "Cannot identify master running export/users mount - exiting"
   exit 1
fi

# echo "$master" >> "/opt/directory/scripts/post_create_script.out"

echo "Setting filesystem quota for user: $USER  on $master"
# Need to use userID number of user, not their username, to set quota
eval="ipa user-find $USER"
uidnum=`ssh infra1 $eval | grep UID | awk '{print $2}'`
eval="setquota -p $alcesuser -u $uidnum /export/users"
ssh $master $eval >> "$testdir/logfile.test"
eval="repquota -s /export/users | grep $USER"
echo "User quota information: " >> "$testdir/logfile.test"
ssh $master $eval >> "$testdir/logfile.test"
echo "Creating home-dirs" >> "$testdir/logfile.test"
eval="su - $USER -c whoami"
ssh login1 $eval >> "$testdir/logfile.test"

# echo "Complete - check logfile "$testdir/logfile.test" for info"

exit 0

