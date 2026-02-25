#!/bin/bash

echo "MOI Stealth Hijack" > lambda_results.txt

for moi in {1..10}
do
    sed -i "s/^MOI .*/MOI $moi N/" lambda.in

    output=$(./aleae lambda.in lambda.r 200 5000 0)

    stealth=$(echo "$output" | grep "cI2 >= 145" | awk -F'[()]' '{print $2}' | sed 's/%//')
    hijack=$(echo "$output" | grep "Cro2 >= 55" | awk -F'[()]' '{print $2}' | sed 's/%//')

    echo "$moi $stealth $hijack" >> lambda_results.txt
done

echo "Results saved to lambda_results.txt"

