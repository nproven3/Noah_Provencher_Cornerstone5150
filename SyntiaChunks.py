import subprocess
import os


#All this code does is run a bunch of commands on every file in a directory to feed
#Into Syntia.

INPUT = "/home/why/snap/ghidra/33/SyntiaCandidates"
OUTPUT = "/home/why/SyntiaResults"
IMAGE = "syntia-deps"
RUNTIME = "podman"
SYNTIA_REPO = "/home/why/Desktop/syntia"
ARCH = "x86_64" #if this is not a varaible things break for some reason. I couldn't just 
                #put it in normally it had to be a variable
SAMPLE_NUMBER = 50

ITERATIONS_MAX = 200
UCT = 0.7

def main():
    if not os.path.isdir(INPUT):
        print("Directory is not real")
        return
    if not os.path.exists(OUTPUT):
        os.makedirs(OUTPUT)
    files = sorted(f for f in os.listdir(INPUT) if f.endswith(".bin"))
    if not files:
        print("No files found at directory")
        return

    print("Found fhunks")

    for idx, fname in enumerate(files):
        in_path = os.path.join(INPUT, fname)
        base, _ = os.path.splitext(fname)

        sampling_json = base + "_sampling.json"
        syntia_json   = base + "_syntia.json"

        print("[*] (%d/%d) Processing %s" %
              (idx + 1, len(files), in_path))

        inner_commands = ( #This was a nightmare to set up but it works do not touch if there is
            "cd /opt/syntia && " #If it's not working it's the docker image not this
            "export PYTHONPATH=. && "
            "python2 scripts/random_sampling.py "
            "'/input/{bin}' {arch} {n} '/output/{sampling}' && "
            "python2 scripts/mcts_synthesis_multi_core.py "
            "{ITERATIONS_MAX} {uct} '/output/{sampling}' '/output/{syntia}'"
        ).format(
            bin=fname,
            arch=ARCH,
            n=SAMPLE_NUMBER,
            sampling=sampling_json,
            syntia=syntia_json,
            ITERATIONS_MAX=ITERATIONS_MAX,
            uct=UCT,
        )
        #NIGHTMARE NIGHTMARE NIGHTMARE
        commands = [
            RUNTIME, "run", "--rm",
            "--user", "0:0",
            "-v", INPUT + ":/input:ro",
            "-v", OUTPUT + ":/output",
            "-v", SYNTIA_REPO + ":/opt/syntia:ro",
            IMAGE,
            "bash", "-lc", inner_commands
        ]

        print("Starting running hopefully nothing breaks")
        try:
            ret = subprocess.call(commands)
        except OSError as e:
            print("Could not start Image")
            continue
        if ret != 0:
            print("Something broke")
        else:
            print("ok")
    print("Everythikng worked yay")


if __name__ == "__main__":
    main()
