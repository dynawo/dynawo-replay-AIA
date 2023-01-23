name="allcurves"
rm $name.crv
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" >> $name.crv
echo "<curvesInput xmlns=\"http://www.rte-france.com/dynawo\">" >> $name.crv
IFS=''
cat "$1" |while read model; do
    # model=$(echo $model | sed 's/\//\\\//g')
    # echo "model: $model."
    # sed -n 's/.*$model_\(.*\)/<curve model="$model" variable="\1">/p' $2 
    sed -n "s/^${model}_\(.*\).*$/<curve model=\"$model\" variable=\"\1\"\/>/p" $2 >> $name.crv
    # sed -n 's/^DM_.AGUAT 1_tfo_\(.*\).*$/<curve model="$model" variable="\1">/p' testcase.states.txt
done
awk -i inplace '!seen[$0]++' $name.crv
echo "</curvesInput>" >> $name.crv

