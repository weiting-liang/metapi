rule coalignment_scaftigs_index:
    input:
        scaftigs = os.path.join(
            config["output"]["coassembly"],
            "scaftigs/all.{assembler_co}.out/all.{assembler_co}.scaftigs.fa.gz")
    output:
        temp(expand(
            os.path.join(
                config["output"]["coalignment"],
                "index/all.{{assembler_co}}.out/all.{{assembler_co}}.scaftigs.fa.gz.{suffix}"),
            suffix=["amb", "ann", "bwt", "pac", "sa"]))
    log:
        os.path.join(
            config["output"]["coalignment"],
            "logs/index/all.{assembler_co}.scaftigs.index.log")
    params:
        output_prefix = os.path.join(
            config["output"]["coalignment"],
            "index/all.{assembler_co}.out/all.{assembler_co}.scaftigs.fa.gz")
    shell:
        '''
        bwa index {input.scaftigs} -p {params.output_prefix} 2> {log}
        '''


rule coalignment_reads_scaftigs:
    input:
        reads = assembly_input_with_short_reads,
        index = expand(os.path.join(
            config["output"]["coalignment"],
            "index/all.{{assembler_co}}.out/all.{{assembler_co}}.scaftigs.fa.gz.{suffix}"),
                       suffix=["amb", "ann", "bwt", "pac", "sa"])
    output:
        flagstat = os.path.join(
            config["output"]["coalignment"],
            "report/flagstat/{sample}.{assembler_co}.align2scaftigs.flagstat"),
        bam = temp(
            os.path.join(
                config["output"]["coalignment"],
                "bam/{sample}.{assembler_co}.out/{sample}.{assembler_co}.align2scaftigs.sorted.bam")),
        bai = temp(
            os.path.join(
                config["output"]["coalignment"],
                "bam/{sample}.{assembler_co}.out/{sample}.{assembler_co}.align2scaftigs.sorted.bam.bai"))
 
    log:
        os.path.join(config["output"]["coalignment"],
                     "logs/alignment/{sample}.{assembler_co}.align.reads2scaftigs.log")
    benchmark:
        os.path.join(config["output"]["coalignment"],
                     "benchmark/alignment/{sample}.{assembler_co}.align.reads2scaftigs.benchmark.txt")
    params:
        index_prefix = os.path.join(
            config["output"]["coalignment"],
            "index/all.{assembler_co}.out/all.{assembler_co}.scaftigs.fa.gz")
    threads:
        config["params"]["alignment"]["threads"]
    shell:
        '''
        rm -rf {output.bam}*

        bwa mem \
        -t {threads} \
        {params.index_prefix} \
        {input.reads} 2> {log} |
        tee >(samtools flagstat \
              -@{threads} - \
              > {output.flagstat}) | \
        samtools sort \
        -m 3G \
        -@{threads} \
        -T {output.bam} \
        -O BAM -o {output.bam} -

        samtools index -@{threads} {output.bam} {output.bai} 2>> {log}
        '''


if config["params"]["alignment"]["cal_base_depth"]:
    rule coalignment_base_depth:
        input:
            os.path.join(
                config["output"]["coalignment"],
                "bam/{sample}.{assembler_co}.out/{sample}.{assembler_co}.align2scaftigs.sorted.bam")
        output:
            os.path.join(
                config["output"]["coalignment"],
                "depth/{sample}.{assembler_co}.out/{sample}.{assembler}.align2scaftigs.depth.gz")
        shell:
            '''
            samtools depth {input} | gzip -c > {output}
            '''


    rule coalignment_base_depth_all:
        input:
            expand(os.path.join(
                config["output"]["coalignment"],
                "depth/{sample}.{assembler_co}.out/{sample}.{assembler_co}.align2scaftigs.depth.gz"),
                   assembler_co=ASSEMBLERS_CO,
                   sample=SAMPLES.index.unique())

else:
    rule coalignment_base_depth_all:
        input:


rule coalignment_report:
    input:
        expand(
            os.path.join(
                config["output"]["coalignment"],
                "report/flagstat/{sample}.{{assembler_co}}.align2scaftigs.flagstat"),
            sample=SAMPLES.index.unique())
    output:
        flagstat = os.path.join(config["output"]["coalignment"],
                                "report/alignment_flagstat_{assembler_co}.tsv")
    run:
        input_list = [str(i) for i in input]
        metapi.flagstats_summary(input_list, 2, output=output.flagstat)


rule coalignment_report_all:
    input:
        expand(
            os.path.join(
                config["output"]["coalignment"],
                "report/alignment_flagstat_{assembler_co}.tsv"),
            assembler_co=ASSEMBLERS_CO)
 

rule coalignment_all:
    input:
        rules.coalignment_base_depth_all.input,
        rules.coalignment_report_all.input#,

        #rules.coassembly_all.input


rule alignment_all:
    input:
        rules.single_alignment_all.input,
        rules.coalignment_all.input
