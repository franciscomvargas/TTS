#!./env/bin/python3
#         ,*++++++*,                ,*++++++*,
#      *++.        .+++          *++.        .++*
#    *+*     ,++++*   *+*      *+*   ,++++,     *+*
#   ,+,   .++++++++++* ,++,,,,*+, ,++++++++++.   *+,
#   *+.  .++++++++++++..++    *+.,++++++++++++.  .+*
#   .+*   ++++++++++++.*+,    .+*.++++++++++++   *+,
#    .++   *++++++++* ++,      .++.*++++++++*   ++,
#     ,+++*.    . .*++,          ,++*.      .*+++*
#    *+,   .,*++**.                  .**++**.   ,+*
#   .+*                                          *+,
#   *+.                   Coqui                  .+*
#   *+*              +++   TTS  +++              *+*
#   .+++*.            .          .             *+++.
#    ,+* *+++*...                       ...*+++* *+,
#     .++.    .""""+++++++****+++++++"""".     ++.
#       ,++.                                .++,
#         .++*                            *++.
#             *+++,                  ,+++*
#                 .,*++++::::::++++*,.
#                        ``````

import os, sys, time, json
import torch
from TTS.api import TTS
from desota import detools
USER_SYS = detools.get_platform()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", "--query", 
                    help='Search query, empty to enter in cli mode',
                    default="tts_cli",
                    type=str)
parser.add_argument("-s", "--speaker", 
                    help='Search query, empty to enter in cli mode',
                    default="male-en-2",
                    type=str)
APP_PATH = os.path.dirname(os.path.realpath(__file__))
OUT_DIR = os.path.join(APP_PATH, "results")
if not os.path.isdir(OUT_DIR):
    os.mkdir(OUT_DIR)
    detools.user_chown(OUT_DIR)

parser.add_argument("-rp", "--respath", 
                    help=f'Output TTS wav file path, default created at inside the class `C_TTS`',
                    default="__default__",
                    type=str)
parser.add_argument('-nc', '--noclear',
                    help='Service Status Request',
                    action='store_true')

DEBUG = True


# Does CUDA is available?
TORCH_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# 🐸TTS model definition
TTS_MODEL = "tts_models/multilingual/multi-dataset/your_tts"
# UTILS
def pcol(obj, template, nostart=False, noend=False):
    '''
    # Description
        print with colors
    # Arguments
    {
        obj: {
            desc: object to print, parsed into string
        },
        template: {
            desc: template name,
            options: [
                header1,
                header2,
                section,
                title,
                body,
                sucess,
                fail
            ]
        }
    }
    '''
    _configs = {
        "header1": "\033[1;105m",
        "header2": "\033[1;95m",
        "search": "\033[104m",
        "section": "\033[94m",
        "title": "\033[7m",
        "body": "\033[97m",
        "sucess": "\033[92m",
        "fail": "\033[91m",
        "end": "\033[0m"
    }
    _morfed_obj = ""
    # PARSE OBJ INTO STR
    if isinstance(obj, list) or isinstance(obj, dict):
        _morfed_obj = json.dumps(obj, indent=2)
    elif not isinstance(obj, str):
        try:
            _morfed_obj = str(obj)
        except:
            # Last ressource
            pass
    else:
        _morfed_obj = obj

    if template in _configs and (_morfed_obj or _morfed_obj==""):
        return f"{_configs[template] if not nostart else ''}{_morfed_obj}{_configs['end'] if not noend else ''}"
    else:
        return obj

class C_TTS:
    def __init__(self, query, speaker, respath):
        if not isinstance(query, str):
            raise ValueError(f"Input Query not String: {type(query)}")
        self.query = query
        self.speaker = speaker
        if respath == "__default__":
            respath = os.path.join(OUT_DIR, f"tts_res{int(time.time())}.wav")
        self.respath = respath

    def run_tts(self):
        # Init TTS
        tts = TTS(TTS_MODEL).to(TORCH_DEVICE)
        # Run TTS
        # ❗ Since this model is multi-speaker and multi-lingual, we must set the target speaker and the language
        # Text to speech to a file
        try:
            tts.tts_to_file(text=self.query, speaker=self.speaker, language=tts.languages[0], file_path=self.respath)
            print(f"[ SUCESS ] Smooth Operation!")
            return self.respath
        except Exception as e:
            print(f"[ ERROR ] TTS exception: {e}")
            return "__fail__"

def main(args):
    _start_time = time.time()
    if args.query == "tts_cli":
        if not args.noclear:
            os.system("cls" if sys.platform == "win32" else "clear" )
        print(pcol("Welcome to TTS 🐸 CLI ", "header1"), pcol("by © DeSOTA, 2024", "header2"))
        print(pcol("Convert text to speech!\n", "body"))

        while True:
            print(pcol("*"*80, "body"))

            # Get User Query
            _user_query = ""
            _exit = False
            try:
                _input_query_msg = "".join([pcol("What text you want to convert to speech? ('exit' to exit)\n-------------------------------------------\n|", "search"), pcol("", "title", noend=True)])
                _user_query = input(_input_query_msg)
            except KeyboardInterrupt:
                _exit = True
                pass
            if _user_query.strip().lower() == "exit" or _exit:
                print(pcol("", "title", nostart=True))
                return
            print(f'{pcol("", "title", nostart=True)}{pcol("-------------------------------------------", "search")}')
            
            
            # LET'S GOO!
            c_tts = C_TTS(_user_query, args.speaker, args.respath)
            tts_res = c_tts.run_tts()
                
            
            if DEBUG:
                print(f" [ DEBUG ] - elapsed time (secs): {time.time()-_start_time}")

            # Print Results
            if tts_res != "__fail__":
                detools.user_chown(tts_res)
                if USER_SYS == "lin":
                    os.system('xdg-open %s' % tts_res)
                else:
                    os.system('open %s' % tts_res)
                print(pcol(f"\nTTS Result has been stored at: {tts_res}\n", "sucess"))
            else:
                print(pcol("\nTTS Request Failure!\n", "fail"))
    else:
        # LET'S GOO!
        c_tts = C_TTS(args.query, args.speaker, args.respath)
        tts_res = c_tts.run_tts()
        if tts_res == "__fail__":
            exit(1)
        exit(0)
        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)