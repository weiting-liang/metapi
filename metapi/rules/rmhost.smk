if not os.path.exists(os.path.join(config["results"]["host"]["prefix"], "bwt")):
    rule build_host_index:
        input:
            config["results"]["host"]["fasta"]
        output:
            expand("{prefix}.{suffix}",
                prefix=config["results"]["host"]["prefix"],
                suffix=["amb", "ann", "bwt", "pac", "sa"])
        params:
            prefix = config["results"]["host"]["prefix"]
        shell:
            "bwa index {input} -p {params.prefix}"


rule rmhost:
    input:
        reads = expand("{trimming}/{{sample}}.trimmed.{read}.fq.gz",
                       trimming=config["results"]["trimming"],
                       read=["1", "2"]),
        index = expand("{prefix}.{suffix}",
                       prefix=config["results"]["host"]["prefix"],
                       suffix=["amb", "ann", "bwt", "pac", "sa"])
    output:
        flagstat = os.path.join(config["results"]["rmhost"], "{sample}.rmhost.flagstat.txt"),
        reads = expand("{rmhost}/{{sample}}.rmhost.{read}.fq.gz",
                       rmhost=config["results"]["rmhost"],
                       read=["1", "2"]),
        bam = os.path.join(config["results"]["rmhost"], "{sample}.host.sorted.bam")
    log:
        os.path.join(config["logs"]["rmhost"], "{sample}.rmhost.log")
    params:
        threads = config["params"]["rmhost"]["threads"],
        save_bam = config["params"]["rmhost"]["save_bam"],
        prefix = config["results"]["host"]["prefix"]
    run:
        if {params.save_bam}:
            shell(
                '''
                bwa mem -t {threads} {params.prefix} {input.reads} |
                tee >(samtools flagstat -@{threads} - > {output.flagstat}) |
                tee >(samtools fastq -@{threads} -N -f 12 -F 256 -1 {output.reads[0]} -2 {output.reads[1]} -) |
                samtools sort -@{threads} -o {output.bam} - 2>{log}
                ''')
        else:
           shell(
               '''
               bwa mem -t {threads} {params.prefix} {input.reads} |
               tee >(samtools flagstat -@{threads} - > {output.flagstat}) |
               samtools fastq -@{threads} -N -f 12 -F 256 -1 {output.reads[0]} -2 {output.reads[1]} - 2>{log}
               ''')
