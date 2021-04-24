#!/bin/bash
sleep 1
echo -e "\033[1;35m####################################################################\033[0m"
echo -e "\033[1;35m  ____          ____  _                   _            _ _         \033[0m"
echo -e "\033[1;35m | __ ) _   _  / ___|(_)_ __   __ _ _   _| | __ _ _ __(_) |_ _   _ \033[0m"
echo -e "\033[1;35m |  _ \\| | | | \\___ \\| | '_ \\ / _\` | | | | |/ _\` | '__| | __| | | |\033[0m"
echo -e "\033[1;35m | |_) | |_| |  ___) | | | | | (_| | |_| | | (_| | |  | | |_| |_| |\033[0m"
echo -e "\033[1;35m |____/ \\__, | |____/|_|_| |_|\\__, |\\__,_|_|\\__,_|_|  |_|\\__|\\__, |\033[0m"
echo -e "\033[1;35m        |___/                 |___/                          |___/ \033[0m"
echo -e "\033[1;35m####################################################################\033[0m"
echo
echo -e "\033[1;36mGithub:\033[0m \033[4;36mhttps://github.com/Singularity0104/test.sh-for-LazyBoy.git\033[0m"
echo -e "\033[1;36mGitee :\033[0m \033[4;36mhttps://gitee.com/singularity0104/test.sh-for-LazyBoy.git\033[0m"
sleep 1
BIN_DIR="./bin/"
PBS_DIR="./pbs/"
RUNLOG_DIR="./runlog/"
TIMELOG_DIR="./timelog/"
TEMPLATE="./submit-template.pbs"
OUT_DATA="./outdata.txt"
CONFIG="./config"
NODE_INFO="./node.txt"
test -d $BIN_DIR && rm -rf $BIN_DIR 
mkdir $BIN_DIR
test -d $PBS_DIR && rm -rf $PBS_DIR
mkdir $PBS_DIR
test -d $RUNLOG_DIR && rm -rf $RUNLOG_DIR
mkdir $RUNLOG_DIR
test -d $TIMELOG_DIR && rm -rf $TIMELOG_DIR
mkdir $TIMELOG_DIR
test -f $OUT_DATA && rm $OUT_DATA
touch $OUT_DATA
test -f $NODE_INFO && rm $NODE_INFO
touch $NODE_INFO
id_index=0
tmp=`grep "min_thread_num:" $CONFIG`
start_thread_num=${tmp#*:}
tmp=`grep "max_thread_num:" $CONFIG`
end_thread_num=${tmp#*:}
tmp=`grep "compiler:" $CONFIG`
compiler=${tmp#*:}
# tmp=`grep "test_stride:" $CONFIG`
# stride=${tmp#*:}
stride=1
tmp=`grep "args:" $CONFIG`
args=${tmp#*:}
tmp=`grep "repeat:" $CONFIG`
repeat=${tmp#*:}
for file in *.c *.cpp
do
if [ $file = "*.c" -o $file = "*.cpp" ]
then
continue
fi
fname="${file%.*}"
fnamelist[$c]="$fname"
if [ $compiler = 0 ]
then
compiling="icc -pthread $file -o $BIN_DIR$fname"
running="TESTFILE ARGS \$procs"
elif [ $compiler = 1 ]
then
compiling="mpiicpc $file -o $BIN_DIR$fname"
running="mpirun -np \$procs TESTFILE ARGS"
else
echo -e "\033[1;31mERROR!\033[0m"
exit 1
fi
$compiling
echo
echo -e "\033[1;32mCompiled Successfully! \033[0m$file"
echo -e "\033[1;32mSubmitting...\033[0m"
for((j=start_thread_num;j<=end_thread_num;j=j+stride))
do
for((k=1;k<=repeat;k++))
do
test -d $PBS_DIR$fname/ || mkdir $PBS_DIR$fname/
cp $TEMPLATE $PBS_DIR$fname/$fname-$j-$k.pbs
sed -i "s/T_NUM/$j/g" $PBS_DIR$fname/$fname-$j-$k.pbs
sed -i "s/RUNNING/$running/g" $PBS_DIR$fname/$fname-$j-$k.pbs
sed -i "s/TESTFILE_NAME/$fname/g" $PBS_DIR$fname/$fname-$j-$k.pbs
sed -i "s/TESTFILE/.\/bin\/$fname/g" $PBS_DIR$fname/$fname-$j-$k.pbs
sed -i "s/ARGS/$args/g" $PBS_DIR$fname/$fname-$j-$k.pbs
sed -i "s/RUNLOG/.\/runlog\/$fname-$j-$k.log/g" $PBS_DIR$fname/$fname-$j-$k.pbs
this_id=`qsub $PBS_DIR$fname/$fname-$j-$k.pbs`
id[id_index]="${this_id%.*}"
file_to_id[id_index]=$fname-$j-$k.log
echo "id: ${id[id_index]} task: ${file_to_id[id_index]%.*}"
echo ${id[id_index]} >> $NODE_INFO
((id_index++))
done
done
done
echo
all_flag=false
sin_flag=true
postfix=('|' '/' '-' '\')
num=0
until $all_flag
do
let now_num=id_index
sin_flag=true
for((i=0;i<id_index;i++))
do
if ! test -f $RUNLOG_DIR${file_to_id[$i]}
then
sin_flag=false
let now_num=now_num-1
fi
done
let index=num%4
printf "\033[1;32mRunning...%c [%d/%d]\r\033[0m" "${postfix[$index]}" "$now_num" "$id_index"
let num=num+1
if $sin_flag
then
all_flag=true
fi
sleep 1
done
printf "\n"
sleep 1
echo
echo -e "\033[1;32mExtracting Time Information...\033[0m"
grep "min_thread_num:" $CONFIG >> $OUT_DATA
grep "max_thread_num:" $CONFIG >> $OUT_DATA
grep "args:" $CONFIG >> $OUT_DATA
grep "repeat:" $CONFIG >> $OUT_DATA
echo >> $OUT_DATA
sleep 1
for((i=0;i<id_index;i++))
do
echo ${file_to_id[$i]%.*} >> $OUT_DATA
until find *${id[$i]}* > /dev/null 2>&1
do
sleep 1
done
time_log_name=`find *${id[$i]}*`
echo $time_log_name
grep "real" $time_log_name >> $OUT_DATA
done
mv *.o* $TIMELOG_DIR
echo
echo -e "\033[1;31mFinished! \033[0m"
echo
echo -e "\033[1;34mIf you want to look over all the results, please input \033[0m\033[1;36mcat ./runlog/*\033[0m\033[1;34m.\033[0m"
echo -e "\033[1;34mIf you want to get the original time information, please get into the timelog folder by \033[0m\033[1;36mcd ./timelog\033[0m\033[1;34m.\033[0m"
echo