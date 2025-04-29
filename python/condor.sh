#!/bin/bash
source ~/startWjetmassAnalysis.sh
cd ../python
./submit_jms_templates.sh 0 $1 substructure
