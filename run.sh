#!/bin/bash
count=1
for repo in "bighero4/MarkParser" "NCSU-CSC510/CMS-module" "TeamAGGS/DefectProneness" "incognito666/tarantula-python" "FrustratedGameDev/Papers" "SuperCh-SE-NCSU/ProjectScraping" "smartSE/constraintAnalysis" "CSC510/SQLvsNOSQL" "CSC510-2015-Axitron/maze"
do python gitable-sql.py $repo $(echo group${count})
count=$((count+1))
done
