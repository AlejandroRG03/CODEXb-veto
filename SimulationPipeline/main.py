#!/bin/python3
import os
import yaml
import logging
import tempfile
import subprocess

logger = logging.getLogger()
#from ProdConf import ProdConf

OPTIONS = {
    "gauss": {
        "name"   : "Gauss",
        "version": "v56r8",
        "platform"   : "x86_64_v2-centos7-gcc11-opt",
        "output_type": "sim",
        "extra_opts" : "--use=AppConfig.v3r454 --use=Gen/DecFiles.v32r35 --use=ProdConf",
        "executable" : "gaudirun.py",
        "options"    : ["'$APPCONFIGOPTS/Gauss/Beam6800GeV-mu100-2024.W35.37-nu6.3.py'",
                        "'$APPCONFIGOPTS/Gauss/EnableSpillover-25ns.py'",
                        "'$APPCONFIGOPTS/Gauss/Run3-detector.py'",
                        "'$APPCONFIGOPTS/Gauss/DataType-2024.py'",
                        "'$DECFILESROOT/options/{event_type}.py'",
                        "'$LBPYTHIA8ROOT/options/Pythia8.py'",
                        "'$APPCONFIGOPTS/Gauss/G4PL_FTFP_BERT_EmOpt2.py'",
                        "'$APPCONFIGOPTS/Persistency/BasketSize-10.py'",
                        "'$APPCONFIGOPTS/Persistency/Compression-ZSTD-1.py'",]
    },
    "boole": {
        "name"       : "Boole",
        "version"    : "v47r0",
        "platform"   : "x86_64_v2-el9-gcc13+detdesc-opt",
        "output_type": "digi",
        "extra_opts" : "--use=AppConfig.v3r454 --use=ProdConf",
        "executable" : "gaudirun.py",
        "options"    : ["'$APPCONFIGOPTS/Boole/Default.py'",
                        "'$APPCONFIGOPTS/Boole/EnableSpillover.py'",
                        "'$APPCONFIGOPTS/Boole/Boole-Upgrade-Baseline-20200616.py'",
                        "'$APPCONFIGOPTS/Boole/Upgrade-RichMaPMT-NoSpilloverDigi.py'",
                        "'$APPCONFIGOPTS/Boole/Boole-Upgrade-IntegratedLumi-0fb.py'",
                        "'$APPCONFIGOPTS/Boole/Run3-VP-NoSpillOver.py'",
                        "'$APPCONFIGOPTS/Persistency/BasketSize-10.py'",
                        "'$APPCONFIGOPTS/Boole/MuonLowE-Bkg-G4.py'",
                        "'$APPCONFIGOPTS/Persistency/Compression-ZSTD-1.py'",],
    },
    "moore_hlt1": {
        "name"       : "Moore",
        "version"    : "v55r12p6",
        "platform"   : "x86_64_v2-el9-gcc13+detdesc-opt",
        "output_type": "dst",
        "extra_opts" : "-- --sequence=hlt1_pp_forward_then_matching_1000KHz --flagging",
        "executable" : "lbexec Moore.production:hlt1",
    },
    "moore_hlt2": {
        "name"       : "Moore",
        "version"    : "v55r12p6",
        "platform"   : "x86_64_v2-el9-gcc13+detdesc-opt",
        "output_type": "dst",
        "extra_opts" : "-- --velo-source=VPRetinaCluster --settings=hlt2_pp_2024 --flagging",
        "executable" : "lbexec Moore.production:hlt2",
    },
    "dddb_tag"  : "dddb-20240427",
    "conddb_tag": "sim10-2024.W35.37-v00.00-mu100"
}


def write_opts(application, main_directory, n_events,
               run_number, first_event_number):
    input_dir = os.path.join(main_directory, application)
    os.makedirs(input_dir, exist_ok=True)

    output_file = os.path.join(input_dir, "options.py")

    if application == "gauss":
        input_files = "[]"
    elif application == "boole":
        input_files = f"[\'{os.path.join(main_directory, 'gauss', 'gauss.sim')}\']"
    else:
        raise ValueError("Application must be 'gauss' or 'boole'")
    
    text = "from ProdConf import ProdConf\n"
    text += "ProdConf({0})".format(",".join([
        f"Application=\'{application.capitalize()}\'",
        f"AppVersion=\'{OPTIONS[application]['version']}\'",
        f"InputFiles="+input_files,
        f"OutputFilePrefix=\'{os.path.join(input_dir, application)}\'",
        f"OutputFileTypes=[\'{OPTIONS[application]['output_type']}\']",
        f"XMLSummaryFile=\'{os.path.join(input_dir, f'summary{application}.xml')}\'",
        f"XMLFileCatalog=\'{os.path.join(input_dir, 'pool_xml_catalog.xml')}\'",
        f"DDDBTag=\'{OPTIONS['dddb_tag']}\'",
        f"CondDBTag=\'{OPTIONS['conddb_tag']}\'",
        f"NOfEvents={n_events}"+f",RunNumber={run_number}" * (application == "gauss"),
        f"FirstEventNumber={first_event_number}",
        f"TCK=\'\'",
        "NThreads=1",
    ])
    )

    with open(output_file, "wt") as outf:
        outf.write(text)

    return output_file


def write_yaml(application, main_directory, n_events):
    input_dir = os.path.join(main_directory, application)
    os.makedirs(input_dir, exist_ok=True)

    output_file = os.path.join(input_dir, "options.yaml")

    dct = {}
    dct["compression"] = dict(algorithm="ZSTD", level=1,
                              max_buffer_size=1048576)
    dct["conddb_tag"] = OPTIONS["conddb_tag"]
    dct["dddb_tag"] = OPTIONS["dddb_tag"]
    dct["data_type"] = "Upgrade"
    dct["evt_max"] = n_events
    if "hlt1" in application:
        dct["input_files"] = [os.path.join(main_directory, "boole", "boole.digi")]
    elif "hlt2" in application:
        dct["input_files"] = [os.path.join(main_directory, "moore_hlt1", "moore_hlt1.dst")]    
    dct["output_file"] = os.path.join(input_dir, application+".dst")
    dct["input_raw_format"] = 0.5
    dct["input_type"] = "ROOT"
    dct["output_type"] = "ROOT"
    dct["n_threads"] = 1
    dct["simulation"] = True

    dct["xml_file_catalog"] = os.path.join(input_dir, "pool_xml_catalog.xml")
    dct["xml_summary_file"] = os.path.join(input_dir, f"summary{application}.xml")


    with open(output_file, 'w') as outfile:
        yaml.dump(dct, outfile, default_flow_style=False)

    return output_file


def run_cmd(cmd, input_dir, dry_run):
    if dry_run:
        print('Command to execute:\n' + cmd)
    else:
        print('Executing command:\n' + cmd)

        # Execute the command
        with open(os.path.join(input_dir, 'stdout'), 'a') as stdout, \
             open(os.path.join(input_dir, 'stderr'), 'a') as stderr:

            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=stdout,
                stderr=stderr,)
            error = (process.wait() != 0)

        if error:
            with open(os.path.join(input_dir, 'stderr')) as stderr, open(
                    os.path.join(input_dir, 'stdout')) as stdout:
                raise RuntimeError(
                    f'Job finished with errors for:\n- stderr:\n{stderr.read() or "none"}- stdout:\n{stdout.read() or "none"}'
                )
        else:
            logger.info('Job finalized successfully')


def setup_cmd(event_type, application, main_directory, opts_filename):
    opts = OPTIONS[application]

    cmd  = f"export HOME=~/;cd {main_directory};"
    cmd += "source /cvmfs/lhcb.cern.ch/lib/etc/cern_profile.sh;"
    cmd += f"lb-run --siteroot=/cvmfs/lhcb.cern.ch/lib/ "
    cmd += f"-c {opts['platform']} "

    if application in ["gauss", "boole"]:
        cmd += opts["extra_opts"]+ " "
    cmd += f"{opts['name']}/{opts['version']} {opts['executable']} "

    if application in ["gauss", "boole"]:
        cmd += "-T "+" ".join(opts["options"]) + " "
    cmd += opts_filename + " "

    if "moore" in application:
        cmd += opts["extra_opts"]

    if str(event_type) in ["38000800", "30011001", "40114060", "11114033"]:
        cmd = cmd.replace("'$DECFILESROOT/options/{event_type}.py'",
                          "'/home3/alejandro.rodriguez/DecFiles/options/{event_type}.py'")

    if application == "boole":
        cmd += f"; rm {main_directory}/gauss/gauss.sim"

    if application == "moore_hlt1":
        cmd += f"; rm {main_directory}/boole/boole.digi"

    if application == "moore_hlt2":
        cmd += f"; rm {main_directory}/moore_hlt1/moore_hlt1.dst"
        cmd += f"; rm -r {main_directory}/lhcb-metainfo"

    return cmd.format(event_type=event_type)


def main(event_type, application, main_directory, n_events,
         run_number, first_event_number, output_directory=None, dry_run=False):
    if str(event_type) not in main_directory:
        main_directory = os.path.join(main_directory, str(event_type))

    if application in ["gauss", "boole"]:
        opts_filename = write_opts(
            application=application,
            main_directory=main_directory,
            n_events=n_events,
            run_number=run_number,
            first_event_number=first_event_number)
    elif "moore" in application:
        opts_filename = write_yaml(
            application=application,
            main_directory=main_directory,
            n_events=n_events,
            )
    else:
        raise ValueError(f"'{application}' not recognized as application")

    cmd = setup_cmd(event_type=event_type, application=application,
                    main_directory=main_directory,
                    opts_filename=opts_filename)

    if output_directory is not None and application == "moore_hlt2":
        cmd += f"; cp {main_directory}/moore_hlt2/moore_hlt2.dst {output_directory}"

    input_dir = os.path.join(main_directory, application)
    run_cmd(cmd=cmd, input_dir=input_dir, dry_run=dry_run)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-type", type=int, default=34122101,
                        help="Event type of the MC sample.")
    parser.add_argument("--nevents", type=int, default=10,
                        help='Number of events to generate')
    parser.add_argument("--run-number", type=int, default=1,
                        help="Run number associated to the Monte Carlo "\
                        "production. This is one of the seeds used by "\
                        "Gauss to generate statistically independent "\
                        "samples.")
    parser.add_argument("--first-event-number", type=int, default=1,                        
                        help="Value to create the seed to be used by Gauss. "\
                        "The actual seed will be this number times the total "\
                        "number of events to process.")
    parser.add_argument("--main-dir", type=str, default=os.getcwd(),
                        help="Directory where the output files will be stored.")
    parser.add_argument('--use-tmp', action='store_true',
                        help='Store the generation files in temporary directories.')
    parser.add_argument('--dry-run', action='store_true',
                        help='This option will make the script print the '\
                        'configuration and exit without running any application')

    args = parser.parse_args()

    if args.use_tmp:
        main_directory   = tempfile.mkdtemp()
        output_directory = args.main_dir

        os.makedirs(output_directory, exist_ok=True)
    else:
        main_directory   = args.main_dir
        output_directory = None

    for application in ["gauss", "boole", "moore_hlt1", "moore_hlt2"]:
        main(event_type=args.event_type,
             application=application,
             main_directory=main_directory,
             n_events=args.nevents,
             run_number=args.run_number,
             first_event_number=args.first_event_number,
             #use_tmp=args.use_tmp,
             output_directory=output_directory,
             dry_run=args.dry_run)
