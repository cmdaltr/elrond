import pandas as pd
import re
from datetime import datetime

from rivendell.audit import write_audit_log_entry


def extract_sru(
    verbosity, vssimage, output_directory, img, vss_path_insert, stage
):
    with open(
        output_directory
        + img.split("::")[0]
        + "/artefacts/cooked"
        + vss_path_insert
        + "SRUDB.json",
        "a",
    ):
        entry, prnt = "{},{},{},'SRUDB.dat'\n".format(
            datetime.now().isoformat(),
            vssimage.replace("'", ""),
            stage,
        ), " -> {} -> {} SRUDB.dat for {}".format(
            datetime.now().isoformat().replace("T", " "),
            stage,
            vssimage,
        )
        write_audit_log_entry(verbosity, output_directory, entry, prnt)
        dfs = pd.read_excel(output_directory + img.split("::")[0] + "/artefacts/cooked" + vss_path_insert + "SRUDB.dat.xlsx", sheet_name=None)
        rows = []
        # cycle through each worksheet tab
        for name, sheet in dfs.items():
            headers = list(sheet)
            # cycle through each row in respective tab        
            for _, row in sheet.iterrows():
                columns = {}
                # cycle through each column in respective row
                for header in headers:
                    columns["System Resource"] = name
                    columns[header] = str(row[header])
                rows.append(columns)
        with open(output_directory + img.split("::")[0] + "/artefacts/cooked" + vss_path_insert + "SRUDB.json", "w") as srujson:
            valid_json = re.sub(r"'(\}, \{)'(System Resource\": \")", r'"\1"\2', str(rows)[3:-3].replace("', '", '", "').replace("': '", '": "'))
            srujson.write('[{{"{}"}}]'.format(valid_json))
