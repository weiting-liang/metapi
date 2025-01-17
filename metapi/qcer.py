#!/usr/bin/env python3

import sys
from metapi import tooler
import seaborn as sns
import matplotlib.pyplot as plt
import argparse
import os
import json
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("agg")


def parse_fastp_json(json_f, paired):
    trimming_dict = {}
    sample_id = os.path.basename(json_f).split(".")[0]
    with open(json_f, 'r') as ih:
        json_ob = json.load(ih)
        trimming_dict["sample_id"] = sample_id
        trimming_dict["before_filtering_total_reads"] = json_ob["summary"]["before_filtering"]["total_reads"]
        trimming_dict["before_filtering_total_bases"] = json_ob["summary"]["before_filtering"]["total_bases"]
        trimming_dict["before_filtering_q20_bases"] = json_ob["summary"]["before_filtering"]["q20_bases"]
        trimming_dict["before_filtering_q30_bases"] = json_ob["summary"]["before_filtering"]["q30_bases"]
        trimming_dict["before_filtering_q20_rate"] = json_ob["summary"]["before_filtering"]["q20_rate"]
        trimming_dict["before_filtering_q30_rate"] = json_ob["summary"]["before_filtering"]["q30_rate"]
        trimming_dict["before_filtering_qc_content"] = json_ob["summary"]["before_filtering"]["qc_content"]
        trimming_dict["before_filtering_read1_mean_length"] = json_ob["summary"]["before_filtering"]["read1_mean_length"]
        if paired:
            trimming_dict["before_filtering_read2_mean_length"] = json_ob["summary"]["before_filtering"]["read2_mean_length"]

        trimming_dict["read1_before_filtering_total_reads"] = json_ob["read1_before_filtering"]["total_reads"]
        trimming_dict["read1_before_filtering_total_bases"] = json_ob["read1_before_filtering"]["total_bases"]
        trimming_dict["read1_before_filtering_q20_bases"] = json_ob["read1_before_filtering"]["q20_bases"]
        trimming_dict["read1_before_filtering_q30_bases"] = json_ob["read1_before_filtering"]["q30_bases"]
        if paired:
            trimming_dict["read2_before_filtering_total_reads"] = json_ob["read2_before_filtering"]["total_reads"]
            trimming_dict["read2_before_filtering_total_bases"] = json_ob["read2_before_filtering"]["total_bases"]
            trimming_dict["read2_before_filtering_q20_bases"] = json_ob["read2_before_filtering"]["q20_bases"]
            trimming_dict["read2_before_filtering_q30_bases"] = json_ob["read2_before_filtering"]["q30_bases"]

        trimming_dict["after_filtering_total_reads"] = json_ob["summary"]["after_filtering"]["total_reads"]
        trimming_dict["after_filtering_total_bases"] = json_ob["summary"]["after_filtering"]["total_bases"]
        trimming_dict["after_filtering_q20_bases"] = json_ob["summary"]["after_filtering"]["q20_bases"]
        trimming_dict["after_filtering_q30_bases"] = json_ob["summary"]["after_filtering"]["q30_bases"]
        trimming_dict["after_filtering_q20_rate"] = json_ob["summary"]["after_filtering"]["q20_rate"]
        trimming_dict["after_filtering_q30_rate"] = json_ob["summary"]["after_filtering"]["q30_rate"]
        trimming_dict["after_filtering_qc_content"] = json_ob["summary"]["after_filtering"]["qc_content"]
        trimming_dict["after_filtering_read1_mean_length"] = json_ob["summary"]["after_filtering"]["read1_mean_length"]
        if paired:
            trimming_dict["after_filtering_read2_mean_length"] = json_ob["summary"]["after_filtering"]["read2_mean_length"]

        trimming_dict["read1_after_filtering_total_reads"] = json_ob["read1_after_filtering"]["total_reads"]
        trimming_dict["read1_after_filtering_total_bases"] = json_ob["read1_after_filtering"]["total_bases"]
        trimming_dict["read1_after_filtering_q20_bases"] = json_ob["read1_after_filtering"]["q20_bases"]
        trimming_dict["read1_after_filtering_q30_bases"] = json_ob["read1_after_filtering"]["q30_bases"]
        if paired:
            trimming_dict["read2_after_filtering_total_reads"] = json_ob["read2_after_filtering"]["total_reads"]
            trimming_dict["read2_after_filtering_total_bases"] = json_ob["read2_after_filtering"]["total_bases"]
            trimming_dict["read2_after_filtering_q20_bases"] = json_ob["read2_after_filtering"]["q20_bases"]
            trimming_dict["read2_after_filtering_q30_bases"] = json_ob["read2_after_filtering"]["q30_bases"]

        return trimming_dict


def change(output, sample_id, step, fq_type, reads_list):
    df = pd.read_csv(output, sep="\t").sort_values("file", ascending=True)
    df["id"] = sample_id
    df["reads"] = reads_list
    df["step"] = step
    df["fq_type"] = fq_type
    df.to_csv(output, sep="\t", index=False)


def compute_host_rate(df, **kwargs):
    host_rate = {}
    df = df.set_index("id")
    for i in df.index.unique():
        if not pd.isnull(i):
            if not df.loc[[i], ].query('reads=="fq1" and step=="rmhost"').empty:
                reads_num_rmhost = df.loc[[i], ].query('reads=="fq1" and step=="rmhost"')[
                    "num_seqs"
                ][0]
                if not df.loc[[i], ].query('reads=="fq1" and step=="trimming"').empty:
                    reads_num = df.loc[[i], ].query('reads=="fq1" and step=="trimming"')[
                        "num_seqs"
                    ][0]
                elif not df.loc[[i], ].query('reads=="fq1" and step=="raw"').empty:
                    reads_num = df.loc[[i], ].query('reads=="fq1" and step=="raw"')[
                        "num_seqs"
                    ][0]
                hostrate = (reads_num - reads_num_rmhost) / reads_num
                host_rate[i] = hostrate
            else:
                host_rate[i] = np.nan
        else:
            print("exists NA value in sample id list, please check")
            sys.exit(1)

    df = df.reset_index()
    df["host_rate"] = df.apply(lambda x: host_rate[x["id"]], axis=1)

    if "output" in kwargs:
        df.to_csv(kwargs["output"], sep="\t", index=False)
    return df


def qc_bar_plot(df, engine, stacked=False, **kwargs):
    if engine == "seaborn":
        # seaborn don't like stacked barplot
        f, ax = plt.subplots(figsize=(10, 7))
        df_ = df.query('reads=="fq1"')
        sns.barplot(x="id", y="num_seqs", hue="step", data=df_)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=-90)

    elif engine == "pandas":
        if not stacked:
            df_ = (
                df.query('reads=="fq1"')
                .pivot(index="id", columns="step", values="num_seqs")
                .loc[:, ["raw", "trimming", "rmhost"]]
            )
            df_.plot(kind="bar", figsize=(10, 7))

        else:
            dict_ = {"id": [], "clean": [], "rmhost": [], "trim": []}
            df = df.set_index("id")
            for i in df.index.unique():
                reads_total = 0

                reads_trimmed = 0
                reads_host = 0
                reads_clean = 0

                if not df.loc[[i], ].query('reads=="fq1" and step=="raw"').empty:
                    reads_total = df.loc[[i], ].query('reads=="fq1" and step=="raw"')[
                        "num_seqs"
                    ][0]

                if not df.loc[[i], ].query('reads=="fq1" and step=="trimming"').empty:
                    reads_trim = df.loc[[i], ].query('reads=="fq1" and step=="trimming"')[
                        "num_seqs"
                    ][0]

                if not df.loc[[i], ].query('reads=="fq1" and step=="rmhost"').empty:
                    reads_clean = df.loc[[i], ].query('reads=="fq1" and step=="rmhost"')[
                        "num_seqs"
                    ][0]

                reads_trimmed = reads_total - reads_trim
                reads_host = reads_trim - reads_clean

                dict_["id"].append(i)
                dict_["trim"].append(reads_trimmed)
                dict_["rmhost"].append(reads_host)
                dict_["clean"].append(reads_clean)

            df_ = pd.DataFrame(dict_).sort_values("id").set_index("id")

            colors = ["#2ca02c", "#ff7f0e", "#1f77b4"]

            df_.plot(kind="bar", stacked=True, color=colors, figsize=(10, 7))

    plt.xlabel("Sample ID")
    plt.ylabel("The number of reads(-pair)")
    plt.title("Fastq quality control barplot", fontsize=11)

    if "output" in kwargs:
        plt.savefig(kwargs["output"])


def main():
    parser = argparse.ArgumentParser(description="quality control reporter")
    parser.add_argument("--raw_stats_list", help="raw stats list")
    parser.add_argument("--trimming_stats_list", help="trimming stats list")
    parser.add_argument("--rmhost_stats_list", help="rmhost stats list")
    parser.add_argument("--output", help="quality control output basename")
    args = parser.parse_args()

    raw_list = pd.read_csv(args.raw_stats_list, header=None, names=["raw"])
    trimming_list = pd.read_csv(
        args.trimming_stats_list, header=None, names=["trimming"]
    )
    rmhost_list = pd.read_csv(args.rmhost_stats_list,
                              header=None, names=["rmhost"])

    df = tooler.merge(
        raw_list["raw"].dropna().tolist()
        + trimming_list["trimming"].dropna().tolist()
        + rmhost_list["rmhost"].dropna().tolist(),
        tooler.parse,
        8,
    )

    df_ = compute_host_rate(df, output=os.path.join(args.output, ".stats.tsv"))
    qc_bar_plot(df_, "seaborn", output=os.path.join(args.output, ".plot.pdf"))


if __name__ == "__main__":
    main()
