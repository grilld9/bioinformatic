#!/bin/bash

rm -rf output
mkdir output

fastqc ecoli.fastq --outdir output

mv ./output/ecoli_fastqc.html ./fastqc.html

minimap2 -d ./output/ecoli.fna ecoli.fna

minimap2 -a ./output/ecoli.fna ecoli.fastq > ./output/alignments.sam

samtools view -b ./output/alignments.sam -o ./output/alignments.bam

samtools flagstat ./output/alignments.bam > ./output/flagstat.txt

percents=$(grep -o -P '\d+\.\d+%' ./output/flagstat.txt)
percents=$(echo $percents | sed 's/%//' |  cut -f1 -d' ')

echo "Качество выравнивания: $percents"

mv ./output/flagstat.txt ./flagstat.txt

if (( $(awk 'BEGIN {print ("'$percents'" > "90.0")}') ))
then
  samtools sort -o ./output/alignments.sorted.bam ./output/alignments.bam
  freebayes -f ecoli.fna ./output/alignments.sorted.bam > ./output/result.vcf
  echo "OK"
else
  echo "not OK"
fi