mkdir /Users/jeunetoujour/pill_test/good/error
rm /Users/jeunetoujour/pill_test/good/error/*

for file in `ls *.jpg`
do
     RESPONSE=`curl --request POST -F "file=@/Users/jeunetoujour/pill_test/good/$file" http://127.0.0.1:5000/upload`
     echo $RESPONSE
     COUNT=`echo $RESPONSE | awk -F":" '{print $2}'`
     REAL_COUNT=`echo $file | awk -F"_" '{print $1}'`
     if [ $COUNT -ne $REAL_COUNT ]
     then
        echo "Error counting ${file}."
        cp $file /Users/jeunetoujour/pill_test/good/error/
     fi
done
