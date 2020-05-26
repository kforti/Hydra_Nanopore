"""Main module."""
import os
from pathlib import Path

from distributed import LocalCluster
from prefect.engine.executors import DaskExecutor, LocalDaskExecutor

"""Main module."""
from hydra.tool import *
from hydra.pipeline import Pipeline
from hydra.runners.shell import ShellRunner
from prefect import task, Flow
import cloudpickle

@task
def extract_fastqs(path):
    fastqs = []
    for dir_, subdirs, files in os.walk(path):
        for f in files:
            if Path(dir_).name == "pass" and Path(f).suffix == ".fastq":
                fastqs.append(os.path.join(dir_, f))
    result = " ".join(fastqs)
    print(result)
    return result


def partition_strategy():
    pass


if __name__ == '__main__':
    env = os.environ.copy()
    env["PATH"] = env["PATH"] + ":/home/kevin/anaconda3/envs/albacore/bin"
    runner = ShellRunner(env=env)
    cluster = LocalCluster()
    executor = LocalDaskExecutor(address=cluster.scheduler_address)

    # Data
    albacore_input = ["/home/kevin/bin/hydra_nanopore/tests/test_data/minion_sample_raw_data/Experiment_01/sample_02_local/pass/2",
                      "/home/kevin/bin/hydra_nanopore/tests/test_data/minion_sample_raw_data/Experiment_01/sample_02_local/pass/3",
                      "/home/kevin/bin/hydra_nanopore/tests/test_data/minion_sample_raw_data/Experiment_01/sample_02_local/pass/4",
                      "/home/kevin/bin/hydra_nanopore/tests/test_data/minion_sample_raw_data/Experiment_01/sample_02_local/pass/5"]
    albacore_output = ["/home/kevin/bin/hydra_nanopore/tests/test_data/output/2",
                       "/home/kevin/bin/hydra_nanopore/tests/test_data/output/3",
                       "/home/kevin/bin/hydra_nanopore/tests/test_data/output/4",
                       "/home/kevin/bin/hydra_nanopore/tests/test_data/output/5"]

    minimap2_output = ["/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_2.sam",
                       "/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_3.sam",
                       "/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_4.sam",
                       "/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_5.sam"]

    view_input = minimap2_output
    view_output = [i.replace(".sam", ".bam") for i in view_input]

    sort_input = view_output
    sort_output = [i.replace(".bam", ".sorted.bam") for i in sort_input]

    index_output = [i.replace(".sorted.bam", ".bai.sorted.bam") for i in sort_output]

    mpileup_output = [i.replace(".sorted.bam", ".bcf") for i in sort_output]

    # Parameters
    basecall_params = {
        "flowcell": "FLO-MIN106",
        "kit": "SQK-LSK109",
        "output_format": "fastq",
        "worker_threads": 2,
        "reads_per_fastq": 1000
    }

    minimap2_params = {
        "reference": "/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_reference.fasta"
    }

    view_params = {
        "options": "bS"
    }

    mpileup_params = {
        "options": "Ob",
        "reference": "/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_reference.fasta",
        "output_format": "u"
    }

    # Tools and Commands
    basecaller = Tool.load_command(name="albacore", command="basecall", params=basecall_params)
    mapper = Tool.load_command(name="minimap2", command="map-nanopore", params=minimap2_params)

    samtools = Tool.load(name="samtools")
    view = samtools.get_command("view", view_params)
    sort = samtools.get_command("sort")
    index = samtools.get_command("index")

    mpileup = Tool.load_command(name="bcftools", command="mpileup")

    # Pipeline
    pipeline = Pipeline("nanopore")

    basecall_result = pipeline.add_command(runner, basecaller, albacore_input, albacore_output)
    fastqs = pipeline.map_task(extract_fastqs, albacore_output, upstream_depens=basecall_result)
    minimap2_result = pipeline.add_command(runner, mapper, fastqs, minimap2_output)
    view_result = pipeline.add_command(runner, view, view_input, view_output, upstream_depens=minimap2_result)
    sort_result = pipeline.add_command(runner, sort, sort_input, sort_output, upstream_depens=view_result)

    pipeline.visualize()
    pipeline.run(executor=executor)

    cluster.close()

    # execute_basecall = ExecuteCommand(runner, basecaller)
    # execute_map_nanopore = ExecuteCommand(runner, mapper)
    # with Flow("test") as flow:
    #     r1 = execute_basecall.map(input=albacore_input, output=albacore_output)
    #     r2 = extract_fastqs.map(r1)
    #     r3 = execute_map_nanopore.map(input=r2, output=minimap2_output)
    # flow.visualize()

