import os, sys
import time, re, json, shutil
import requests, subprocess
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-mr", "--model_req", 
                    help="DeSOTA Request as yaml file path",
                    type=str)
parser.add_argument("-mru", "--model_res_url",
                    help="DeSOTA API Result URL. Recognize path instead of url for desota tests", # check how is atribuited the dev_mode variable in main function
                    type=str)

DEBUG = False

# DeSOTA Funcs [START]
#   > Import DeSOTA Scripts
from desota import detools
#   > Grab DeSOTA Paths
USER_SYS = detools.get_platform()
APP_PATH = os.path.dirname(os.path.realpath(__file__))
#   > USER_PATH
if USER_SYS == "win":
    path_split = str(APP_PATH).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(APP_PATH).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
# DeSOTA Funcs [END]

TTS_SPEAKER = "male-en-2"

def main(args):
    '''
    return codes:
    0 = SUCESS
    1 = INPUT ERROR
    2 = OUTPUT ERROR
    3 = API RESPONSE ERROR
    9 = REINSTALL MODEL (critical fail)
    '''
   # Time when grabed
    _report_start_time = time.time()
    start_time = int(_report_start_time)

    # DeSOTA Model Request
    model_request_dict = detools.get_model_req(args.model_req)
    model_request_args = detools.get_model_args(model_request_dict)
    
    #---INPUT---# (PRO ARGS)
    # NOT APPLIED!
    #---INPUT---#

    # API Response URL
    send_task_url = args.model_res_url
    
    # TARGET File Path
    out_filepath = os.path.join(APP_PATH, f"text-to-speech{start_time}.wav")
    out_urls = detools.get_url_from_str(send_task_url)
    if len(out_urls)==0:
        dev_mode = True
        report_path = send_task_url
    else:
        dev_mode = False
        report_path = out_urls[0]

    # Get text from request
    _req_text = detools.get_request_text(model_request_dict)
    if isinstance(_req_text, list):
        _req_text = " ".join(_req_text)
    if DEBUG:
        print(json.dumps([
            f"INPUT: '{_req_text}'\n",
            f"IsINPUT?: {True if _req_text else False}\n"
        ], indent=2))


    # Run Model
    if _req_text:
        _model_run = os.path.join(APP_PATH, "main.py")
        if USER_SYS == "win":
            _model_runner_py = os.path.join(APP_PATH, "env", "python.exe")
        elif USER_SYS == "lin":
            _model_runner_py = os.path.join(APP_PATH, "env", "bin", "python3")

        _sproc = subprocess.Popen(
            [
                _model_runner_py, _model_run, 
                "--query", str(_req_text),
                "--speaker", TTS_SPEAKER,
                "--respath", out_filepath
            ]
        )
        while True:
            # TODO: implement model timeout
            _ret_code = _sproc.poll()
            if _ret_code != None:
                break
    else:
        print(f"[ ERROR ] -> TTS Request Failed: No Input found")
        exit(1)

    if not os.path.isfile(out_filepath):
        print(f"[ ERROR ] -> TTS Request Failed: No Output found")
        exit(2)
    
    if dev_mode:
        if not report_path.endswith(".json"):
            report_path += ".json"
        with open(report_path, "w") as rw:
            json.dump(
                {
                    "Model Result Path": out_filepath,
                    "Processing Time": time.time() - _report_start_time
                },
                rw,
                indent=2
            )
        detools.user_chown(report_path)
        detools.user_chown(out_filepath)
        print(f"Path to report:\n\t{report_path}")
    else:
        print(f"[ INFO ] -> TTS Result can be found at:{out_filepath}")

        # DeSOTA API Response Preparation
        files = []
        with open(out_filepath, 'rb') as fr:
            files.append(('upload[]', fr))
            # DeSOTA API Response Post
            send_task = requests.post(url = send_task_url, files=files)
            print(f"[ INFO ] -> DeSOTA API Upload:{json.dumps(send_task.json(), indent=2)}")
        # Delete temporary file
        os.remove(out_filepath)

        if send_task.status_code != 200:
            print(f"[ ERROR ] -> TTS Post Failed (Info):\nfiles: {files}\nResponse Code: {send_task.status_code}")
            exit(3)
    
    print("TASK OK!")
    exit(0)


if __name__ == "__main__":
    args = parser.parse_args()
    if not args.model_req or not args.model_res_url:
        raise EnvironmentError()
    main(args)