"""Main module."""
import os
from pathlib import Path

"""Main module."""
from hydra.tool import *
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


if __name__ == '__main__':
    env = os.environ.copy()
    env["PATH"] = env["PATH"] + ":/home/kevin/anaconda3/envs/albacore/bin"
    runner = ShellRunner(env=env)

    # Data
    albacore_input = "/home/kevin/bin/hydra_nanopore/tests/test_data/minion_sample_raw_data/Experiment_01/sample_01_local/pass/2"
    albacore_output = "/home/kevin/bin/hydra_nanopore/tests/test_data/output"

    minimap2_output = "/home/kevin/bin/hydra_nanopore/tests/test_data/lambda.sam"

    view_input = minimap2_output
    view_output = view_input.replace(".sam", ".bam")

    sort_input = view_output
    sort_output = sort_input.replace(".bam", ".sorted.bam")

    index_output = sort_output.replace(".sorted.bam", ".bai.sorted.bam")

    mpileup_output = sort_output.replace(".sorted.bam", ".bcf")

    # Parameters
    basecall_params = {
        "flowcell": "FLO-MIN106",
        "kit": "SQK-LSK109",
        "output_format": "fastq",
        "worker_threads": 2,
        "reads_per_fastq": 1000
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
    mapper = Tool.load_command(name="minimap2", command="map-nanopore")

    samtools = Tool.load(name="samtools")
    view = samtools.get_command("view", view_params)
    sort = samtools.get_command("sort")
    index = samtools.get_command("index")

    mpileup = Tool.load_command(name="bcftools", command="mpileup")

    # Command Execution Tasks
    execute_basecall = ExecuteCommand(runner, basecaller, albacore_input, albacore_output)
    execute_map_nanopore = ExecuteCommand(runner, mapper)
    execute_view = ExecuteCommand(runner, view)
    execute_sort = ExecuteCommand(runner, sort)
    execute_index = ExecuteCommand(runner, index)
    execute_mpileup = ExecuteCommand(runner, mpileup)

    prev_flow_state = None
    # Workflow Definition
    with Flow('test') as flow:
        basecall_result = execute_basecall()
        map_nanopore_input = extract_fastqs(albacore_output)

        minimap2_result = execute_map_nanopore(input=map_nanopore_input, output=minimap2_output, reference="/home/kevin/bin/hydra_nanopore/tests/test_data/lambda_reference.fasta")

        view_result = execute_view(input=view_input, output=view_output)
        sort_result = execute_sort(input=sort_input, output=sort_output)

        mpileup_result = execute_mpileup(input=sort_output, output=mpileup_output, **mpileup_params)


    state = flow.run()
    with open("result.hydra", "wb") as f:
        cloudpickle.dump(state, f)
