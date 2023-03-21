# gsed -n 's/.* DEBUG | [0-9]\+ \(.*\)/\1/p' $1 >>  "$2.allvars.txt"
name=$(basename $2)
if [ $1=="states" ]; then
    sed -n '/X variables$/,/alias/p' $2 | sed 's/.* DEBUG | [0-9]\+ \(.*\)/\1/p' >>  "$name.states.txt"
fi
if [ $1=="models" ]; then
    sed -n 's/.*id="\([^"]*\).*/\1/p' $2 >> "$name.models.txt" 
fi
if [ $1=="terminals" ]; then
    sed -n '/X variables$/,/alias/p' $2 | sed '/terminal/!d' | sed 's/.* DEBUG | [0-9]\+ \(.*\)/\1/p' >>  "$name.terminals.txt"
fi
