name="allcurves"
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" >> $name.crv
echo "<curvesInput xmlns=\"http://www.rte-france.com/dynawo\">" >> $name.crv
IFS=''
cat "$1" |while read model; do
    sed -n "s/^${model}_\(.*\).*$/<curve model=\"$model\" variable=\"\1\"\/>/p" $2 >> $name.crv
done
awk -i inplace '!seen[$0]++' $name.crv
echo "</curvesInput>" >> $name.crv

