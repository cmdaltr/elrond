#!/usr/bin/env python3 -tt
import os
import random
import re
import shutil
import subprocess
import sys
import time
from collections import OrderedDict
from datetime import datetime

from rivendell.core.core import collect_process_keyword_analysis_timeline
from rivendell.audit import write_audit_log_entry
from rivendell.core.gandalf import assess_gandalf
from rivendell.core.identify import identify_memory_image
from rivendell.meta import extract_metadata
from rivendell.mount import mount_images
from rivendell.mount import unmount_images
from rivendell.post.clam import run_clamscan
from rivendell.post.clean import archive_artefacts
from rivendell.post.clean import delete_artefacts
from rivendell.post.elastic.config import configure_elastic_stack
from rivendell.post.mitre.nav_config import configure_navigator
from rivendell.post.splunk.config import configure_splunk_stack
from rivendell.post.yara import run_yara_signatures

# SIEM auto-installer
from elrond.tools.siem_installer import SIEMInstaller


def main(
    directory,
    case,
    analysis,
    auto,
    collect,
    vss,
    delete,
    elastic,
    gandalf,
    collectfiles,
    extractiocs,
    imageinfo,
    lotr,
    keywords,
    volatility,
    metacollected,
    navigator,
    nsrl,
    process,
    superquick,
    quick,
    reorganise,
    splunk,
    symlinks,
    timeline,
    memorytimeline,
    userprofiles,
    unmount,
    clamav,
    veryverbose,
    verbose,
    yara,
    archive,
    d,
    cwd,
    sha256,
    allimgs,
    flags,
    elrond_mount,
    ewf_mount,
    system_artefacts,
    quotes,
    asciitext,
):
    partitions = []
    subprocess.Popen(["clear"])
    time.sleep(2)
    print(
        "\n\n    \033[1;36m        .__                               .___\n      ____  |  |  _______   ____    ____    __| _/\n    _/ __ \\ |  |  \\_  __ \\ /  _ \\  /    \\  / __ |\n    \\  ___/ |  |__ |  | \\/(  <_> )|   |  \\/ /_/ |\n     \\___  >|____/ |__|    \\____/ |___|  /\\____ |\n         \\/                            \\/      \\/\n\n     {}\033[1;m\n\n".format(
            random.choice(quotes)
        )
    )
    if not collect and not gandalf and not reorganise:
        print(
            "\n  You MUST use the collect switch (-C), gandalf switch (-G) or the reorganise switch (-O)\n   If you are processing acquired disk and/or memory images, you must invoke the collect switch (-C)\n   If you have previously collected artefacts having used gandalf, you must invoke the gandalf switch (-G)\n   If you have previously collected artefacts NOT having used gandalf, you must invoke the reorganise switch (-O)\n\n  Please try again.\n\n\n"
        )
        sys.exit()
    if collect and gandalf:
        print(
            "\n  You cannot use the collect switch (-C) and the collect gandalf (-G).\n   If you are processing acquired disk and/or memory images, you must invoke the collect switch (-C).\n   If you have previously collected artefacts using gandalf, you must invoke the gandalf switch (-G).\n\n  Please try again.\n\n\n"
        )
        sys.exit()
    if collect and reorganise:
        print(
            "\n  You cannot use the collect switch (-C) and the reorganise switch (-O).\n   If you are processing acquired disk and/or memory images, you must invoke the collect switch (-C).\n   If you have previously collected artefacts NOT using gandalf, you must invoke the reorganise switch (-O).\n\n  Please try again.\n\n\n"
        )
        sys.exit()
    if gandalf and reorganise:
        print(
            "\n  You cannot use the gandalf switch (-G) and the reorganise switch (-O).\n   If you have previously collected artefacts using gandalf, you must invoke the gandalf switch (-G).\n   If you have previously collected artefacts NOT using gandalf, you must invoke the reorganise switch (-O).\n\n  Please try again.\n\n\n"
        )
        sys.exit()
    if volatility and not process:
        print(
            "\n  If you are just processing memory images, you must invoke the process switch (-P) with the memory switch (-M).\n\n  Please try again.\n\n\n"
        )
        sys.exit()
    if (not collect or gandalf) and (
        vss or collectfiles or imageinfo or symlinks or timeline or userprofiles
    ):
        if gandalf:
            gandalforcollect = "gandalf switch (-G)"
        else:
            gandalforcollect = "collect switch (-C)"
        if (not collect or gandalf) and vss:
            collectand = "vss switch (-c)"
        elif (not collect or gandalf) and collectfiles:
            collectand = "collectfiles switch (-F)"
        elif (not collect or gandalf) and imageinfo:
            collectand = "imageinfo switch (-I)"
        elif (not collect or gandalf) and symlinks:
            collectand = "symlinks switch (-s)"
        elif (not collect or gandalf) and timeline:
            collectand = "timeline switch (-t)"
        elif (not collect or gandalf) and userprofiles:
            collectand = "userprofiles switch (-U)"
        print(
            "\n\n  In order to use the {}, you must also invoke the {}. Please try again.\n\n\n\n".format(
                collectand, gandalforcollect
            )
        )
        sys.exit()
    if memorytimeline and not volatility:
        print(
            "\n\n  You cannot provide the memorytimeline switch (-t) without provided the Volatility switch (-M). Please try again.\n\n\n\n"
        )
        sys.exit()
    if analysis and not process:
        print(
            "\n\n  You cannot provide the Analysis switch (-A) without provided the Processing switch (-P). Please try again.\n\n\n\n"
        )
        sys.exit()
    if not metacollected and nsrl and (superquick or quick):
        print(
            "\n\n  In order to use the NSRL switch (-H), you must either provide the metacollected switch (-o) - with or without the Superquick (-Q) and Quick Flags (-q).\n  Or, if not using the metacollected switch (-o), remove the Superquick (-Q) and Quick Flags (-q) altogether. Please try again.\n\n\n\n"
        )
        sys.exit()
    if yara:
        if not os.path.isdir(yara[0]):
            print(
                "\n\n  '{}' is not a valid directory or does not exist. Please try again.\n\n\n\n".format(
                    yara[0]
                )
            )
            sys.exit()
    if navigator and not splunk:
        print(
            "\n\n  You cannot provide the Navigator switch (-N) without providing the Splunk switch (-S). Please try again.\n\n\n\n"
        )
        sys.exit()
    if lotr:
        print(random.choice(asciitext))
        input("\n\n\n\n\n\n     Press Enter to continue... ")
        subprocess.Popen(["clear"])
        time.sleep(2)
    starttime, ot, imgs, foundimgs, doneimgs, d, vssmem = (
        datetime.now().isoformat(),
        {},
        {},
        [],
        [],
        directory[0],
        "",
    )
    if (veryverbose and verbose) or veryverbose:
        verbosity = "veryverbose"
    elif verbose:
        verbosity = "verbose"
    else:
        verbosity = ""
    if collectfiles:
        if collectfiles != True:
            if len(collectfiles) > 0:
                if not collectfiles.startswith(
                    "include:"
                ) and not collectfiles.startswith("exclude:"):
                    print(
                        "\n  [-F --collectfiles] - if providing an inclusion or exclusion list, the optional argument must start with 'include:' or 'exclude:' respectively\n   The correct syntax is: [include/exclude]:/path/to/inclusion_or_exclusion.list\n  Please try again.\n\n"
                    )
                    sys.exit()
                if not os.path.exists(collectfiles[8:]):
                    print(
                        "\n  [-F --collectfiles] - '{}' does not exist and/or is an invalid file, please try again.\n\n".format(
                            collectfiles[8:]
                        )
                    )
                    sys.exit()
    if yara:
        if not os.path.exists(yara[0]):
            print(
                "\n  [-Y --yara] - '{}' does not exist and/or is an invalid directory, please try again.\n\n".format(
                    yara[0]
                )
            )
            sys.exit()
    # check architecture - if arm do not prompt for apfs-fuse
    if "aarch" not in str(
        subprocess.Popen(
            [
                "uname",
                "-m",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()[0]
    ):
        apfsexists = str(
            subprocess.Popen(
                [
                    "locate",
                    "apfs",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).communicate()[0]
        )
        if not "/usr/local/bin/apfs" in apfsexists:
            if (
                input(
                    "  apfs-fuse and associated libraries are not installed. This is required for macOS disk images.\n   Continue? Y/n [Y] "
                )
                == "n"
            ):
                print(
                    "\n  Please run https://github.com/cyberg3cko/elrond/elrond/tools/scripts/apfs-fuse.sh and try again.\n\n"
                )
                if os.path.exists("/usr/local/bin/apfs"):
                    shutil.rmtree("/usr/local/bin/apfs")
                sys.exit()
    if os.path.exists("/opt/elrond/elrond/tools/.profiles"):
        os.remove("/opt/elrond/elrond/tools/.profiles")
    if len(directory) > 1:
        od = directory[1]
        if not od.endswith("/"):
            od = od + "/"
        if not os.path.isdir(od):
            if not auto:
                make_od = input(
                    "  You have specified an output directory that does not currently exist.\n    Would you like to create '{}'? Y/n [Y] ".format(
                        od
                    )
                )
            else:
                make_od = "y"
            if make_od != "n":
                try:
                    os.makedirs(od)
                    print(
                        "  '{}' has been created successfully.\n".format(
                            os.path.realpath(os.path.dirname(od) + "/")
                        )
                    )
                except PermissionError:
                    print(
                        "  A permissions error occured when creating '{}'.\n    Please try again as 'sudo'.\n  ----------------------------------------\n\n".format(
                            od
                        )
                    )
                    sys.exit()
                except Exception as e:
                    if "Input/output error" in str(e):
                        print(
                            "  An input/output error occured when trying to create '{}'.\n    Ensure the full path of '{}' is accessible.\n  ----------------------------------------\n\n".format(
                                od, od
                            )
                        )
                    else:
                        print(
                            "  An unknown error occured when trying to create '{}'.\n    Restart SIFT and try again.\n  ----------------------------------------\n\n".format(
                                od
                            )
                        )
                    sys.exit()
            else:
                print(
                    "\n    You have three choices:\n     -> Specify a directory that exists\n     -> Confirm creation of a specified directory\n     -> Provide no output directory (cwd is default)\n\n  Please try again.\n  ----------------------------------------\n\n"
                )
                sys.exit()
        output_directory = os.path.dirname(od) + "/"
    else:
        output_directory = "./"
    if not os.path.isdir(d) or len(os.listdir(d)) == 0:
        print(
            "\n  [directory] - '{}' does not exist, is not a directory or is empty, please try again.\n\n".format(
                d
            )
        )
        sys.exit()
    elif len(os.listdir(d)) > 0 and (
        ".e01" not in str(os.listdir(d)).lower()
        and ".vmdk" not in str(os.listdir(d)).lower()
        and ".dd" not in str(os.listdir(d)).lower()
        and ".raw" not in str(os.listdir(d)).lower()
        and ".img" not in str(os.listdir(d)).lower()
        and ".001" not in str(os.listdir(d)).lower()
    ):
        print(
            "\n  [directory] - '{}' does not contain any valid files (.E01/.VMDK/.dd/.raw/.img/.001)\n   for elrond to assess.\n   Please ensure you are referencing the correct directory path and try again.\n\n\n".format(
                d
            )
        )
        sys.exit()
    if not unmount:
        unmount_images(elrond_mount, ewf_mount)
    if volatility:
        volchoice, volcheck = (
            "2.6",
            str(
                subprocess.Popen(
                    ["locate", "volatility3"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).communicate()[0]
            )[2:-1],
        )
        if volcheck != "":
            if not auto:
                volchoose = input(
                    "  Which version of volatility do you wish to use? 3/2.6/Both [Both] "
                )
                if volchoose != "3" and volchoose != "2.6":
                    volchoice = "Both"
                elif volchoose == "3":
                    volchoice = "3"
            else:
                volchoice = "Both"
        if memorytimeline:
            memtimeline = memorytimeline
        else:
            memtimeline = ""
    else:
        volchoice = ""
        memtimeline = ""
    print(
        "\n  -> \033[1;36mCommencing Identification Phase...\033[1;m\n  ----------------------------------------"
    )
    time.sleep(1)
    if collect:  # collect artefacts from disk/memory images
        for root, _, files in os.walk(d):  # Mounting images
            for f in files:
                if os.path.exists(os.path.join(root, f)):  # Mounting images
                    if (
                        ".FA" not in f
                        and ".FB" not in f
                        and ".FC" not in f
                        and ".FD" not in f
                        and ".FE" not in f
                        and ".FF" not in f
                        and ".FG" not in f
                        and ".FH" not in f
                        and ".FI" not in f
                        and ".FJ" not in f
                        and ".FK" not in f
                        and ".FL" not in f
                        and ".FM" not in f
                        and ".FN" not in f
                        and ".FO" not in f
                        and ".FP" not in f
                        and ".FQ" not in f
                        and ".FR" not in f
                        and ".FS" not in f
                        and ".FT" not in f
                        and ".FU" not in f
                        and ".FV" not in f
                        and ".FW" not in f
                        and ".FX" not in f
                        and ".FY" not in f
                        and ".FZ" not in f
                        and (
                            (
                                f.split(".E")[0] + ".E" not in str(foundimgs)
                                and f.split(".e")[0] + ".e" not in str(foundimgs)
                            )
                            and (
                                f.split(".F")[0] + ".F" not in str(foundimgs)
                                and f.split(".f")[0] + ".f" not in str(foundimgs)
                            )
                        )
                    ):
                        path, imgformat, fsize = (
                            os.path.join(root, f),
                            str(
                                subprocess.Popen(
                                    ["file", os.path.join(root, f)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                ).communicate()[0]
                            )[2:-3].split(": ")[1],
                            os.stat(os.path.join(root, f)).st_size,
                        )
                        if fsize > 1073741824:  # larger than 1GB
                            if not os.path.isdir(output_directory + f):
                                try:
                                    os.mkdir(os.path.join(output_directory, f))
                                    foundimgs.append(
                                        os.path.join(root, f)
                                        + "||"
                                        + root
                                        + "||"
                                        + f
                                        + "||"
                                        + imgformat
                                    )
                                except PermissionError:
                                    print(
                                        "\n    '{}' could not be created. Are you running as root?".format(
                                            os.path.join(output_directory, f)
                                        )
                                    )
                                    sys.exit()
                            else:
                                print(
                                    "\n    '{}' already exists in '{}'\n     Please remove it before trying again.\n\n\n".format(
                                        f, output_directory
                                    )
                                )
                                sys.exit()
        for (
            foundimg
        ) in (
            foundimgs
        ):  # potentially add ova and vdi - https://superuser.com/questions/915615/mount-vmware-disk-images-under-linux
            stage = "mounting"
            path, root, f, imgformat = foundimg.split("||")
            if (
                "Expert Witness" in imgformat
                or (
                    "VMDK" in imgformat
                    or ("VMware" and " disk image" in imgformat)
                    and (f.endswith(".vmdk"))
                )
                or (
                    "DOS/MBR boot sector" in imgformat
                    and (f.endswith(".raw") or f.endswith(".dd") or f.endswith(".img"))
                )
            ):
                time.sleep(2)
                if not auto:
                    wish_to_mount = input(
                        "  Do you wish to mount '{}'? Y/n [Y] ".format(f)
                    )
                else:
                    wish_to_mount = "y"
                if wish_to_mount != "n":
                    if not superquick and not quick:
                        if not os.path.exists(output_directory + f + "/meta.audit"):
                            with open(
                                output_directory + f + "/meta.audit", "w"
                            ) as metaimglog:
                                metaimglog.write(
                                    "Filename,SHA256,NSRL,Entropy,Filesize,LastWriteTime,LastAccessTime,LastInodeChangeTime,Permissions,FileType\n"
                                )
                        if verbosity != "":
                            print(
                                "    Calculating SHA256 hash for '{}', please stand by...".format(
                                    f
                                )
                            )
                        with open(path, "rb") as metaimg:
                            buffer = metaimg.read(262144)
                            while len(buffer) > 0:
                                sha256.update(buffer)
                                buffer = metaimg.read(262144)
                            metaentry = (
                                path
                                + ","
                                + sha256.hexdigest()
                                + ",unknown,N/A,N/A,N/A,N/A,N/A,N/A,N/A\n"
                            )
                        with open(
                            output_directory + f + "/meta.audit", "a"
                        ) as metaimglog:
                            metaimglog.write(metaentry)
                        extract_metadata(
                            verbosity,
                            output_directory,
                            f,
                            path,
                            "metadata",
                            sha256,
                            nsrl,
                        )
                    entry, prnt = (
                        "LastWriteTime,elrond_host,elrond_stage,elrond_log_entry\n",
                        " -> {} -> created audit log file for '{}'".format(
                            datetime.now().isoformat().replace("T", " "), f
                        ),
                    )
                    write_audit_log_entry(verbosity, output_directory, entry, prnt)
                    print("   Attempting to mount '{}'...".format(f))
                    allimgs, partitions = mount_images(
                        d,
                        auto,
                        verbosity,
                        output_directory,
                        path,
                        f,
                        elrond_mount,
                        ewf_mount,
                        allimgs,
                        imageinfo,
                        imgformat,
                        vss,
                        "mounting",
                        cwd,
                        quotes,
                        partitions,
                    )
                    partitions = list(set(partitions))
                    if len(allimgs) > 0 and f in str(allimgs):
                        entry, prnt = "{},{},{},completed\n".format(
                            datetime.now().isoformat(), f, "mounting"
                        ), " -> {} -> mounted '{}'".format(
                            datetime.now().isoformat().replace("T", " "), f
                        )
                        write_audit_log_entry(verbosity, output_directory, entry, prnt)
                    else:
                        print("   Unfortunately, '{}' could not be mounted".format(f))
                        entry, prnt = "{},{},{},failed\n".format(
                            datetime.now().isoformat(), f, "mounting"
                        ), " -> {} -> not mounted '{}'".format(
                            datetime.now().isoformat().replace("T", " "), f
                        )
                        write_audit_log_entry(verbosity, output_directory, entry, prnt)
                else:
                    print("    OK. '{}' will not be mounted.\n".format(f))
                allimgs = {**allimgs, **ot}
                print()
            elif volatility and ("data" in imgformat or "crash dump" in imgformat):
                if not superquick and not quick:
                    if not os.path.exists(output_directory + f + "/meta.audit"):
                        with open(
                            output_directory + f + "/meta.audit", "w"
                        ) as metaimglog:
                            metaimglog.write(
                                "Filename,SHA256,known-good,Entropy,Filesize,LastWriteTime,LastAccessTime,LastInodeChangeTime,Permissions,FileType\n"
                            )
                    if verbosity != "":
                        print(
                            "    Calculating SHA256 hash for '{}', please stand by...".format(
                                f
                            )
                        )
                    with open(path, "rb") as metaimg:
                        buffer = metaimg.read(262144)
                        while len(buffer) > 0:
                            sha256.update(buffer)
                            buffer = metaimg.read(262144)
                        metaentry = (
                            path
                            + ","
                            + sha256.hexdigest()
                            + ",unknown,N/A,N/A,N/A,N/A,N/A,N/A,N/A\n"
                        )
                    with open(output_directory + f + "/meta.audit", "a") as metaimglog:
                        metaimglog.write(metaentry)
                    extract_metadata(
                        verbosity,
                        output_directory,
                        f,
                        path,
                        "metadata",
                        sha256,
                        nsrl,
                    )
                ot = identify_memory_image(
                    verbosity,
                    output_directory,
                    flags,
                    auto,
                    superquick,
                    quick,
                    metacollected,
                    cwd,
                    sha256,
                    nsrl,
                    f,
                    ot,
                    d,
                    path,
                    volchoice,
                    vss,
                    vssmem,
                    memtimeline,
                )
                for mempath, memimg in ot.items():
                    allimgs[memimg] = mempath
                allimgs = OrderedDict(sorted(allimgs.items(), key=lambda x: x[1]))
                print()
    elif gandalf:  # populate allimgs and imgs dictionaries
        assess_gandalf(
            auto,
            gandalf,
            vss,
            nsrl,
            volatility,
            metacollected,
            superquick,
            quick,
            ot,
            d,
            cwd,
            sha256,
            flags,
            output_directory,
            verbosity,
            allimgs,
            imgs,
            volchoice,
            vssmem,
            memtimeline,
        )
    else:
        f, path, stage = "", "", "reorganise"
    allimgs = OrderedDict(sorted(allimgs.items(), key=lambda x: x[1]))
    if len(allimgs) > 0:
        for (
            image_location,
            image_name,
        ) in allimgs.items():  # populating just a 'disk image' dictionary
            if "::" in image_name and "::memory_" not in image_name:
                imgs[image_location] = image_name
        time.sleep(1)
        if volatility:
            print(
                "  ----------------------------------------\n  -> Completed Identification & Extraction Phase.\n"
            )
        else:
            print(
                "  ----------------------------------------\n  -> Completed Identification Phase.\n"
            )
    else:
        if not auto:
            nodisks = input(
                "  No disk images exist in the provided directory.\n   Do you wish to continue? Y/n [Y] "
            )
            if nodisks == "n":
                print(
                    "  ----------------------------------------\n  -> Completed Identification Phase.\n\n\n  ----------------------------------------\n   If you are confident there are valid images in this directory, maybe try with the Memory switch (-M)?\n   Otherwise review the path location and ensure the images are supported by elrond.\n  ----------------------------------------\n\n\n"
                )
                sys.exit()
    time.sleep(1)
    if (
        collect or reorganise
    ):  # Collection/Reorganisation, Processing, Keyword Searching, Analysis & Timelining
        collect_process_keyword_analysis_timeline(
            auto,
            collect,
            process,
            analysis,
            extractiocs,
            timeline,
            vss,
            collectfiles,
            nsrl,
            keywords,
            volatility,
            metacollected,
            superquick,
            quick,
            reorganise,
            symlinks,
            userprofiles,
            verbose,
            d,
            cwd,
            sha256,
            flags,
            system_artefacts,
            output_directory,
            verbosity,
            f,
            allimgs,
            imgs,
            path,
            volchoice,
            vssmem,
            memtimeline,
            stage,
        )
    allimgs, imgs, elrond_mount, img_list = (
        OrderedDict(sorted(allimgs.items(), key=lambda x: x[1])),
        OrderedDict(sorted(imgs.items(), key=lambda x: x[1])),
        [
            "/mnt/elrond_mount00",
            "/mnt/elrond_mount01",
            "/mnt/elrond_mount02",
            "/mnt/elrond_mount03",
            "/mnt/elrond_mount04",
            "/mnt/elrond_mount05",
            "/mnt/elrond_mount06",
            "/mnt/elrond_mount07",
            "/mnt/elrond_mount08",
            "/mnt/elrond_mount09",
            "/mnt/elrond_mount10",
            "/mnt/elrond_mount11",
            "/mnt/elrond_mount12",
            "/mnt/elrond_mount13",
            "/mnt/elrond_mount14",
            "/mnt/elrond_mount15",
            "/mnt/elrond_mount16",
            "/mnt/elrond_mount17",
            "/mnt/elrond_mount18",
            "/mnt/elrond_mount19",
        ],
        [],
    )
    if (
        len(allimgs) > 0
    ):  # Post-processing metadata, YARA, Splunk, Elastic, Archive, Deletion
        if not superquick or metacollected:
            print(
                "\n\n  -> \033[1;36mCommencing Metadata phase for proccessed artefacts...\033[1;m\n  ----------------------------------------"
            )
            time.sleep(1)
            imgs_metad = []
            for _, img in allimgs.items():
                print(
                    "\n    Collecting metadata from processed artefacts for '{}'...".format(
                        img.split("::")[0]
                    )
                )
                extract_metadata(
                    verbosity,
                    output_directory,
                    img,
                    output_directory + img.split("::")[0] + "/artefacts/raw/",
                    stage,
                    sha256,
                    nsrl,
                )
                if os.path.exists(
                    output_directory + img.split("::")[0] + "/artefacts/cooked/"
                ):
                    extract_metadata(
                        verbosity,
                        output_directory,
                        img,
                        output_directory + img.split("::")[0] + "/artefacts/cooked/",
                        stage,
                        sha256,
                        nsrl,
                    )
                if os.path.exists(
                    output_directory + img.split("::")[0] + "/artefacts/carved/"
                ):
                    extract_metadata(
                        verbosity,
                        output_directory,
                        img,
                        output_directory + img.split("::")[0] + "/artefacts/carved/",
                        stage,
                        sha256,
                        nsrl,
                    )
                if os.path.exists(output_directory + img.split("::")[0] + "/analysis/"):
                    extract_metadata(
                        verbosity,
                        output_directory,
                        img,
                        output_directory + img.split("::")[0] + "/analysis/",
                        stage,
                        sha256,
                        nsrl,
                    )
                if os.path.exists(output_directory + img.split("::")[0] + "/files/"):
                    extract_metadata(
                        verbosity,
                        output_directory,
                        img,
                        output_directory + img.split("::")[0] + "/files/",
                        stage,
                        sha256,
                        nsrl,
                    )
                if (
                    os.path.exists(output_directory + img.split("::")[0])
                    and "memory_" in img.split("::")[1]
                ):
                    extract_metadata(
                        verbosity,
                        output_directory,
                        img,
                        output_directory + img.split("::")[0],
                        stage,
                        sha256,
                        nsrl,
                    )
                if img.split("::")[0] not in str(imgs_metad):
                    imgs_metad.append(img.split("::")[0])
                print(
                    "     Completed collection of metadata from processed artefacts for '{}'".format(
                        img.split("::")[0]
                    )
                )
            print(
                "  ----------------------------------------\n  -> Completed Metadata phase for proccessed artefacts.\n"
            )
            time.sleep(1)
        if clamav:
            print(
                "\n\n  -> \033[1;36mCommencing ClamAV Phase...\033[1;m\n  ----------------------------------------"
            )
            time.sleep(1)
            for loc, img in imgs.items():
                if not auto:
                    yes_clam = input(
                        "  Do you wish to conduct ClamAV scanning for '{}'? Y/n [Y] ".format(
                            img.split("::")[0]
                        )
                    )
                if auto or yes_clam != "n":
                    run_clamscan(verbosity, output_directory, loc, img, collectfiles)
            flags.append("06clam")
            print(
                "  ----------------------------------------\n  -> Completed ClamAV Phase.\n"
            )
            time.sleep(1)
        if yara:
            print(
                "\n\n  -> \033[1;36mCommencing Yara Phase...\033[1;m\n  ----------------------------------------"
            )
            time.sleep(1)
            yara_files = []
            for yroot, _, yfiles in os.walk(yara[0]):
                for yfile in yfiles:
                    if yfile.endswith(".yara"):
                        yara_files.append(os.path.join(yroot, yfile))
            for loc, img in imgs.items():
                if not auto:
                    yes_yara = input(
                        "  Do you wish to conduct Yara analysis for '{}'? Y/n [Y] ".format(
                            img.split("::")[0]
                        )
                    )
                if auto or yes_yara != "n":
                    run_yara_signatures(
                        verbosity, output_directory, loc, img, collectfiles, yara_files
                    )
            flags.append("07yara")
            print(
                "  ----------------------------------------\n  -> Completed Yara Phase.\n"
            )
            time.sleep(1)
        if splunk:
            # Ensure Splunk is installed before configuring
            siem_installer = SIEMInstaller()
            if not siem_installer.ensure_siem_installed('splunk'):
                print("\n  \033[1;31mWARNING: Splunk is not installed. Skipping Splunk phase.\033[0m\n")
            else:
                usercred, pswdcred = configure_splunk_stack(
                    verbosity,
                    output_directory,
                    case,
                    "splunk",
                    allimgs,
                )
                flags.append("08splunk")
                print(
                    "  ----------------------------------------\n  -> Completed Splunk Phase.\n"
                )
            time.sleep(1)
        if elastic:
            # Ensure Elasticsearch and Kibana are installed before configuring
            siem_installer = SIEMInstaller()
            es_installed = siem_installer.ensure_siem_installed('elasticsearch')
            kb_installed = siem_installer.ensure_siem_installed('kibana')

            if not (es_installed and kb_installed):
                print("\n  \033[1;31mWARNING: Elastic Stack is not fully installed. Skipping Elastic phase.\033[0m\n")
            else:
                # Verify version match
                match, match_msg = siem_installer.version_checker.check_elasticsearch_kibana_match()
                if not match:
                    print(f"\n  \033[1;33mWARNING: {match_msg}\033[0m")
                    print("  \033[1;33mProceeding with caution...\033[0m\n")

                configure_elastic_stack(
                    verbosity,
                    output_directory,
                    case,
                    "elastic",
                    allimgs,
                )
                flags.append("09elastic")
                print(
                    "  ----------------------------------------\n  -> Completed Elastic Phase.\n"
                )
            time.sleep(1)
        if (splunk or elastic) and navigator:  # mapping to attack-navigator
            print(
                "\n\n  -> \033[1;36mBuilding ATT&CK® Navigator...\033[1;m\n  ----------------------------------------"
            )
            time.sleep(1)
            navresults = configure_navigator(
                verbosity, case, splunk, elastic, usercred, pswdcred
            )
            if navresults != "":
                flags.append("10navigator")
            print(
                "  ----------------------------------------\n  -> Completed ATT&CK® Navigator Phase.\n"
            )
            time.sleep(1)
        if archive or delete:
            for img, mntlocation in imgs.items():
                if "vss" not in img and "vss" not in mntlocation:
                    if archive:
                        archive_artefacts(verbosity, output_directory)
                        flags.append("11archiving")
                    if delete:
                        delete_artefacts(verbosity, output_directory)
                        flags.append("12deletion")
    endtime, fmt, timestringprefix = (
        datetime.now().isoformat(),
        "%Y-%m-%dT%H:%M:%S.%f",
        "Total elasped time: ",
    )
    st, et = datetime.strptime(starttime, fmt), datetime.strptime(endtime, fmt)
    totalsecs, secs = int(round((et - st).total_seconds())), int(
        round((et - st).total_seconds() % 60)
    )
    if round((et - st).total_seconds()) > 3600:
        hours, mins = round((et - st).total_seconds() / 60 / 60), round(
            (et - st).total_seconds() / 60 % 60
        )
        if hours > 1 and mins > 1 and secs > 1:
            timetaken = "{} hours, {} minutes and {} seconds.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours > 1 and mins > 1 and secs == 1:
            timetaken = "{} hours, {} minutes and {} second.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours > 1 and mins == 1 and secs > 1:
            timetaken = "{} hours, {} minute and {} seconds.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours == 1 and mins > 1 and secs > 1:
            timetaken = "{} hour, {} minutes and {} seconds.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours > 1 and mins == 1 and secs == 1:
            timetaken = "{} hours, {} minute and {} second.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours == 1 and mins > 1 and secs == 1:
            timetaken = "{} hour, {} minutes and {} second.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours == 1 and mins == 1 and secs > 1:
            timetaken = "{} hour, {} minute and {} seconds.".format(
                str(hours), str(mins), str(secs)
            )
        elif hours > 1 and mins > 1 and secs == 0:
            timetaken = "{} hours and {} minutes.".format(str(hours), str(mins))
        elif hours > 1 and mins == 0 and secs > 0:
            timetaken = "{} hours and {} seconds.".format(str(hours), str(secs))
        elif hours == 1 and mins > 1 and secs == 0:
            timetaken = "{} hour and {} minutes.".format(str(hours), str(mins))
        elif hours == 1 and mins == 0 and secs > 0:
            timetaken = "{} hour and {} second.".format(str(hours), str(secs))
        elif hours > 1 and mins == 0 and secs == 0:
            timetaken = "{} hours.".format(str(hours))
        elif hours == 1 and mins == 0 and secs == 0:
            timetaken = "{} hour.".format(str(hours))
    elif 3600 > round((et - st).total_seconds()) > 60:
        mins = round((et - st).total_seconds() / 60)
        if mins > 1 and secs > 1:
            timetaken = "{} minutes and {} seconds.".format(str(mins), str(secs))
        elif mins == 1 and secs > 1:
            timetaken = "{} minute and {} seconds.".format(str(mins), str(secs))
        elif mins > 1 and secs == 1:
            timetaken = "{} minutes and {} second.".format(str(mins), str(secs))
        elif mins == 1 and secs == 1:
            timetaken = "{} minute and {} second.".format(str(mins), str(secs))
        else:
            timetaken = "{} minutes.".format(str(mins))
    else:
        if secs > 1:
            timetaken = "{} seconds.".format(str(secs))
        else:
            timetaken = "{} second.".format(str(secs))
    OrderedDict(sorted(imgs.items(), key=lambda x: x[1]))
    for _, eachimg in imgs.items():
        img_list.append(eachimg)
    partitions = sorted(list(set(partitions)))
    if vss:
        for eachimg, partition in zip(img_list, partitions):
            if (
                "Windows" in eachimg.split("::")[1]
                and (
                    ".E01" in eachimg.split("::")[0] or ".e01" in eachimg.split("::")[0]
                )
                and "memory_" not in eachimg.split("::")[1]
                and "_vss" not in eachimg.split("::")[1]
            ):
                if len(partitions) > 1:
                    partition_insert = " ({} partition)".format(
                        partition.split("||")[0][2::]
                    )
                else:
                    partition_insert = ""
                inspectedvss = input(
                    "\n\n  ----------------------------------------\n   Have you reviewed the Volume Shadow Copies for '{}'{}? Y/n [Y] ".format(
                        eachimg.split("::")[0], partition_insert
                    )
                )
                if inspectedvss != "n":
                    unmount_images(elrond_mount, ewf_mount)
                    print(
                        "    Unmounted Volume Shadow Copies for '{}'\n  ----------------------------------------\n".format(
                            eachimg.split("::")[0]
                        )
                    )
    else:
        unmount_images(elrond_mount, ewf_mount)
    print(
        "\n\n  -> \033[1;36mFinished. {}{}\033[1;m\n  ----------------------------------------".format(
            timestringprefix, timetaken
        )
    )
    time.sleep(1)
    if len(flags) > 0:
        doneimgs, sortedflags = [], re.sub(
            r"', '\d{2}", r", ", str(sorted(set(flags))).title()[4:-2]
        )
        if ", " in sortedflags:
            more_than_one_phase = "phases"
            flags = sortedflags.split(", ")
            lastflag = " and " + flags[-1]
            flags.pop()
            flags = (
                str(flags).replace("[", "").replace("]", "").replace("'", "") + lastflag
            )
        else:
            flags = str(flags)[4:-2].title()
            more_than_one_phase = "phase"
        if len(allimgs) > 0:
            print("      {} {} completed for...".format(flags, more_than_one_phase))
            for _, eachimg in allimgs.items():
                doneimgs.append(eachimg.split("::")[0])
    doneimgs = sorted(list(set(doneimgs)))
    unmount_images(elrond_mount, ewf_mount)
    for eachimg, _ in allimgs.items():
        for doneroot, donedirs, donefiles in os.walk(
            output_directory + str(eachimg.split("::")[0]).split("/")[-1]
        ):
            for donefile in donefiles:
                if os.path.exists(os.path.join(doneroot, donefile)):
                    if os.stat(os.path.join(doneroot, donefile)).st_size <= 100:
                        try:
                            os.remove(os.path.join(doneroot, donefile))
                        except:
                            pass
            for donedir in donedirs:
                if os.path.exists(doneroot + "/artefacts/raw/"):
                    for eachdir in os.listdir(doneroot + "/artefacts/raw/"):
                        if os.path.exists(
                            doneroot + "/artefacts/raw/" + eachdir + "/IE/"
                        ):
                            shutil.rmtree(doneroot + "/artefacts/raw/" + eachdir)
                if len(os.listdir(os.path.join(doneroot, donedir))) < 1:
                    try:
                        shutil.rmtree(os.path.join(doneroot, donedir))
                    except:
                        pass
    for doneimg in doneimgs:
        print("       '{}'".format(doneimg))
        entry, prnt = "{},{},finished,'{}'-'{}': ({} seconds)".format(
            datetime.now().isoformat(), doneimg, st, et, totalsecs
        ), " -> {} -> elrond completed for '{}'".format(
            datetime.now().isoformat().replace("T", " "), doneimg
        )
        write_audit_log_entry(verbosity, output_directory, entry, prnt)
        time.sleep(1)
    print("  ----------------------------------------")
    print()
    if len(allimgs.items()) > 0 and (splunk or elastic or navigator):
        if splunk:
            print("    Splunk Web:           127.0.0.1:8000/en-US/app/elrond/")
        if elastic:
            print(
                "    elasticsearch:        127.0.0.1:9200\n    Kibana:               127.0.0.1:5601"
            )
        if navigator:
            print("    ATT&CK® Navigator:    127.0.0.1:4200")
        print()
        print("  ----------------------------------------")
        print("\n")
    print("\n\n     \033[1;36m{}\033[1;m".format(random.choice(quotes) + "\n\n\n"))
    os.chdir(cwd)
