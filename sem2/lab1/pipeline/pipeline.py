import subprocess
from metaflow import FlowSpec, step, Parameter

class Flow(FlowSpec):
    ref_file = Parameter('ref_file', default='ecoli.fna')
    seq_file = Parameter('seq_file', default='ecoli.fastq')

    @step
    def start(self):
        subprocess.run(['rm', '-rf', 'output'])
        subprocess.run(['mkdir', 'output'])
        self.next(self.fastqc, self.minimap2)

    @step
    def fastqc(self):
        subprocess.run(['fastqc', self.seq_file, '--outdir', 'output'])
        subprocess.run(['mv', './output/*_fastqc.html', './fastqc.html'])
        self.next(self.join_fastqc)

    @step
    def minimap2(self):
        subprocess.run(['minimap2', '-d', f'./output/{self.ref_file}', self.ref_file])
        subprocess.run(['minimap2', '-a', f'./output/{self.ref_file}', self.seq_file], stdout=open('./output/alignments.sam', 'w+'))
        self.next(self.samtools_view)

    @step
    def samtools_view(self):
        subprocess.run(['samtools', 'view', '-b', './output/alignments.sam', '-o', './output/alignments.bam'])
        self.next(self.samtools_flagstat)

    @step
    def samtools_flagstat(self):
        subprocess.run(['samtools', 'flagstat', './output/alignments.bam'], stdout=open('./flagstat.txt', 'w+'))
        self.next(self.parse_flagstat)

    @step
    def parse_flagstat(self):
        percent = 0.0
        with open('./flagstat.txt') as f:
            for line in f:
                if 'mapped' in line:
                    percent = float(line.split("(")[1].split("%")[0])
                    break
            self.result = percent
        self.next(self.ok_result, self.bad_result)

    @step
    def bad_result(self):
        if self.result < 90:
            print(f"BAD RESULT {self.result}")
        self.next(self.join_freebayes)

    @step
    def ok_result(self):
        if self.result >= 90:
            print(f"OK RESULT {self.result}")
        self.next(self.samtools_sort)

    @step
    def samtools_sort(self):
        if self.result >= 90:
            subprocess.run(['samtools', 'sort', '-o', './output/alignments.sorted.bam', './output/alignments.bam'])
        self.next(self.freebayes)

    @step
    def freebayes(self):
        if self.result >= 90:
            subprocess.run(['freebayes', '-f', self.ref_file, './output/alignments.sorted.bam'], stdout=open('./output/result.vcf', 'w+'))
        self.next(self.join_freebayes)

    @step
    def join_freebayes(self, inputs):
        self.next(self.join_fastqc)

    @step
    def join_fastqc(self, inputs):
        self.next(self.end)


    @step
    def end(self):
        pass

if __name__ == '__main__':
    Flow()